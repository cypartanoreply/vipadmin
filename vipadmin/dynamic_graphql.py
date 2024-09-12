# dynamic_graphql.py
from graphene_django import DjangoObjectType
import django_filters
from django.apps import apps

from django.db import models 
from django.forms import modelform_factory 
from .utils import CustomDjangoModelFormMutation,CustomUploadDjangoModelFormMutation
from datetime import timedelta 
from graphene_django.forms.mutation import DjangoModelFormMutation
from graphene import ID, Field, Mutation,relay,Scalar,Int,Boolean,String,Float
from CypartaGraphqlSubscriptionsTools.utils import *
from asgiref.sync import async_to_sync
import logging
from django.core.exceptions import PermissionDenied

logger = logging.getLogger(__name__)
from graphql import GraphQLError
class CountableConnectionBase(relay.Connection):
 
    class Meta:
        abstract = True

    total_count = Int()

    def resolve_total_count(self, info, **kwargs):
       
        return self.iterable.count()
     
    
relay.Connection = CountableConnectionBase
class DurationScalar(Scalar):
    """A custom scalar to serialize timedelta objects as total seconds."""

    @staticmethod
    def serialize(value):
        if isinstance(value, timedelta):
            return value.total_seconds()
        raise Exception(f"Received incompatible Duration: {repr(value)}")

    @staticmethod
    def parse_literal(node):
        if isinstance(node, Int):
            return timedelta(seconds=node.value)

    @staticmethod
    def parse_value(value):
        return timedelta(seconds=int(value))
    


def generate_filterset(model, excluded_fields):
    # Dynamically determine which fields to include and exclude
    fields = []
    exclude = []

    filterable_fields = []  # Store filterable fields here

    for field in model._meta.fields:
        fields.append(field.name)
        if isinstance(field, (models.FileField, models.ImageField, models.JSONField)):
            exclude.append(field.name)
        else:
            filterable_fields.append(field.name)  # Add non-excluded fields to filterable_fields

    # Dynamically create the Meta class for the FilterSet
    Meta = type('Meta', (), {
        'model': model,
        'fields': fields,
        'exclude': exclude + excluded_fields,
    })

    # Dynamically create the FilterSet class
    filterset_name = f"{model.__name__}FilterSet"
    filterset_class = type(filterset_name, (django_filters.FilterSet,), {'Meta': Meta})

    return filterable_fields, filterset_class  # Return filterable_fields along with filterset_class

def generate_model_type(model, exclude):
    # Prepare custom fields for handling DurationField with the custom scalar
    custom_fields = {
        field.name: DurationScalar(description="Duration in seconds")
        for field in model._meta.fields
        if isinstance(field, models.DurationField)
    }

    # Dynamically create the Meta class for the DjangoObjectType
    meta_attributes = {
        'model': model,
        'exclude': exclude,
        
        'interfaces': (relay.Node,),
        'connection_class': CountableConnectionBase,
    }

    Meta = type('Meta', (), meta_attributes)

    def resolve_pk(self, info):
        return self.pk
    def resolve_show_value(self, info): #to appear if filed type is forgin key or many to many insted of id value 
        return model.__str__(self)

    attributes = {'Meta': Meta, **custom_fields,'resolve_show_value':resolve_show_value,'show_value':String(), 'resolve_pk': resolve_pk, 'pk': ID(),}
    model_type_name = f"{model.__name__}Type"
    return type(model_type_name, (DjangoObjectType,), attributes)

#ddd

def generate_model_form(model,exclude=None):
   
    # Dynamically create a ModelForm class for the given model
    return modelform_factory(model, fields="__all__",exclude=exclude)


def generate_create_mutation(model, has_permission_func, execlude_fileds):
    model_form = generate_model_form(model=model, exclude=execlude_fileds)

    Meta = type('Meta', (), {'form_class': model_form})

    mutation_class_name = f"Create{model.__name__}Mutation"

    def mutate_and_get_payload(cls, root, info, **input):
        
        user = info.context.user
        
        if not user.is_authenticated:
            raise PermissionDenied("You must be authenticated to perform this operation.")
        if not has_permission_func(user=user, model=model):
            raise PermissionDenied("You must have permission to perform this operation.")
        return super(mutation_class, cls).mutate_and_get_payload(root, info, **input)

    fields_dict = {'Meta': Meta, 'mutate_and_get_payload': classmethod(mutate_and_get_payload)}

   
    mutation_class = type(mutation_class_name, (CustomUploadDjangoModelFormMutation,), fields_dict)

    return mutation_class









def generate_delete_mutation(model,has_permission_func):
    class DeleteMutation(Mutation):
        class Arguments:
            pk = ID(required=True)

        success = Boolean()

        @staticmethod
        def mutate(root, info, pk):
            user=info.context.user
            
            if not user.is_authenticated :
                    raise PermissionDenied("You must be authenticated to perform this operation.")
            if not has_permission_func(user=user,model=model):
                    raise PermissionDenied("You must be have a permission to perform this operation.")
        
            
            instance = model.objects.get(pk=pk)
            instance.delete()
            return DeleteMutation(success=True)

    mutation_class_name = f"Delete{model.__name__}Mutation"
    return type(mutation_class_name, (DeleteMutation,), {})


def generate_update_mutation(model,has_permission_func,execlude_fileds):
    model_form_class = generate_model_form(model,execlude_fileds)
   
    class CustomModelForm(model_form_class):
      

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            for field_name in self.fields:
                self.fields[field_name].required = False
                self.fields[field_name].disabled = True

    def mutate_and_get_payload(cls, root, info, **input):
            user = info.context.user
            
            if not user.is_authenticated:
                raise PermissionDenied("You must be authenticated to perform this operation.")
            
            if not has_permission_func(user=user, model=model):
                raise PermissionDenied("You must have permission to perform this operation.")
        
            instance_id = input.pop('pk', None)
            if not instance_id:
                raise Exception("pk field is required.")
            
            try:
                instance = model.objects.get(pk=instance_id)
                for attr, value in input.items():
                    setattr(instance, attr, value)
                instance.save()
                return cls(retun_data_after_update=instance, errors=[])  # Adjust accordingly
            except model.DoesNotExist:
                # Handle the case where the object with the provided ID does not exist
                return cls(errors=[{'field': 'id', 'messages': ['Object with the provided ID does not exist.']}])

    mutation_class = type(
        f"Update{model.__name__}Mutation",
        (CustomDjangoModelFormMutation,),
        {
            
            #'Input': Input,
            'Meta': type('Meta', (), {'form_class': CustomModelForm}),
            'retun_data_after_update':Field(generate_model_type(model,execlude_fileds)),
           'mutate_and_get_payload': classmethod(mutate_and_get_payload),
        }
    )

    return mutation_class



def helper_function_created(root, info, model,model_name,subscribe,has_permission_func):
    try:
        user=info.context.user
        if not user.is_authenticated:
            raise PermissionDenied("You must be authenticated to perform this operation.")
        if not has_permission_func(user=user, model=model):
            raise PermissionDenied("You must have permission to perform this operation.")
        
        requested_fields = [field.name.value for field in info.field_nodes[0].selection_set.selections]

        return async_to_sync(root.detect_register_group_status)([f'{model_name}Created'], subscribe, requested_fields)
     
    except Exception as e:
        logger.exception("An error occurred in helper_function")
        raise e  # 
def helper_function_updated(root, info, model,model_name,subscribe,id,has_permission_func):
    try:
        user=info.context.user
        if not user.is_authenticated:
            return GraphQLError("You must be authenticated to perform this operation.")
        if not has_permission_func(user=user, model=model):
            return GraphQLError("You must have permission to perform this operation.")
        
        return async_to_sync(root.detect_register_group_status)([f'{model_name}Updated.{id}'], subscribe)
     
    except Exception as e:
        logger.exception("An error occurred in helper_function")
        raise e  # 
def helper_function_deleted(root, info, model,model_name,subscribe,id,has_permission_func):
    try:
        user=info.context.user
        if not user.is_authenticated:
            return GraphQLError("You must be authenticated to perform this operation.")
        if not has_permission_func(user=user, model=model):
            return GraphQLError("You must have permission to perform this operation.")
        
        return async_to_sync(root.detect_register_group_status)([f'{model_name}Deleted.{id}'], subscribe)
     
    except Exception as e:
        logger.exception("An error occurred in helper_function")
        raise e  # 
def helper_function_created_updated_deleted(root, info, model,model_name,subscribe,id,has_permission_func):
    try:
        
        user=info.context.user
        if not user.is_authenticated:
            return GraphQLError("You must be authenticated to perform this operation.")
        if not has_permission_func(user=user, model=model):
            return GraphQLError("You must have permission to perform this operation.")
        
        requested_fields = [field.name.value for field in info.field_nodes[0].selection_set.selections]
        
        groups = [f'{model_name}Created', f'{model_name}Updated.{id}', f'{model_name}Deleted.{id}']
        if id == "" or id ==None:
            groups = [f'{model_name}Created']
        
        return async_to_sync(root.detect_register_group_status)(groups, subscribe, requested_fields)

     
    except Exception as e:
        logger.exception("An error occurred in helper_function")
        raise e  # 
