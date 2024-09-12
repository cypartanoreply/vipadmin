from django.contrib.auth.models import User
import json
from django.core.serializers.json import DjangoJSONEncoder

from graphene.types.generic import GenericScalar
from .models import User,models,Employee
from .utils import (
    has_delete_permission,
    has_view_permission,
    has_edit_permission,
    has_add_permission,
    has_add_edit_del_permission,
    AppsEnum,get_additional_field_info,to_camel_case
)
from django.db.models import Q, F
from graphene_django.filter import DjangoFilterConnectionField
from CypartaGraphqlSubscriptionsTools.utils import get_model_name_instance
from django.core.serializers import serialize
from rest_framework.authtoken.models import Token
from django.db.models import Q
from .dynamic_graphql import (
    generate_filterset,
    generate_model_type,
    generate_create_mutation,
    generate_delete_mutation,
    generate_update_mutation,
    helper_function_created,
    helper_function_updated,
    helper_function_deleted,
    helper_function_created_updated_deleted,
)
from django.contrib.auth import authenticate
from graphene import (
    ID,
    Field,
    ObjectType,
    Mutation,
    Boolean,
    ID,
    String,
    Schema,
    JSONString,
    Dynamic,
    List,
)
from graphene.types.objecttype import ObjectTypeMeta

from .model_manager import ModelManger
from django.core.exceptions import PermissionDenied

from django.apps import apps

class DynamicSearchResultType(ObjectType):
    """
    A generic GraphQL object type that represents the search results.
    """
    id = ID()
    name = String()
    display_value = String()
    
class FieldInfo(ObjectType):
    field_name = String()
    field_type = String()
    max_length = String()  # Add max_length attribute
    is_required = Boolean()
    relation_table = String()

    default = String()  # Adjust data type according to your needs
    choices = List(JSONString)  # Adjust data type according to your needs
    verbose_name = String()
    help_text = String()
    primary_key = Boolean()
    auto_created = Boolean()
    unique = Boolean()
    editable = Boolean()

    is_password = Boolean()


class TableInfo(ObjectType):
    model_name = String()
    table_verbose_name = String()
    fields = List(FieldInfo)
    can_edit = Boolean()
    can_del = Boolean()
    can_add = Boolean()
    model_icon = String()
    filter_fields = List(String)
    pk_field_name = String()


class AppInfo(ObjectType):
    app_name = String()
    app_verbose_name = String()
    tables = List(TableInfo)
    app_icon = String()


# login fucntion
# class log


class UpdateUserPassword(Mutation):
    class Arguments:
        pk = ID(required=True)
        new_password = String(required=True)

    success = Boolean()

    @staticmethod
    def mutate(root, info, pk, new_password):
        user = User.objects.get(pk=pk)
        user.set_password(new_password)
        user.save()
        return UpdateUserPassword(success=True)


class QueryMeta(ObjectTypeMeta):
    def __new__(cls, name, bases, attrs):
        @staticmethod
        def get_field_value(obj, field):
            value = getattr(obj, field.name)

            # Check for FileField and ImageField to return the URL
            if isinstance(field, (FileField, ImageField)) and value:
                return value.url

            # Add custom handling for other field types as needed

            return value
       
       
    
        
        
        


        def resolve_dynamic_search(self, info, app_name, model_name, search_term):
            """
            Perform the search based on the app name, model name, and search term.
            """
            try:
                model = apps.get_model(app_name, model_name)
            except LookupError:
                raise Exception(f"Model '{model_name}' in app '{app_name}' not found.")

            queries = Q()
            
            # Iterate over the fields of the model
            for field in model._meta.get_fields():
                if isinstance(field, models.CharField):
                    # Search on CharField
                    queries |= Q(**{f"{field.name}__icontains": search_term})

                elif isinstance(field, models.ForeignKey):
                    # Search using the related model's __str__ method
                    related_model = field.related_model
                    related_str = related_model.objects.filter(
                        Q(**{f"{related_model._meta.pk.name}__icontains": search_term})
                    ).values_list('id', flat=True)
                    queries |= Q(**{f"{field.name}__in": related_str})

                elif isinstance(field, models.ManyToManyField):
                    # Search using the related model's __str__ method
                    related_model = field.related_model
                    related_str = related_model.objects.filter(
                        Q(**{f"{related_model._meta.pk.name}__icontains": search_term})
                    ).values_list('id', flat=True)
                    queries |= Q(**{f"{field.name}__in": related_str})

            # Perform the search and return the results
            search_results = model.objects.filter(queries).distinct()

            # Construct the return value for GraphQL
            result_list = []
            for instance in search_results:
                result_list.append(DynamicSearchResultType(
                    id=instance.pk,  # Assuming primary key is 'id'
                    name=str(instance),  # Use the model's __str__ method to display the name
                    display_value=str(instance)  # Customize this as needed
                ))

            return result_list


        def resolve_fields_by_table(self, info, app_name, model_name):
            # Get the app's models by app name
            user = info.context.user
            if not user.is_authenticated:
                raise PermissionDenied(
                    "You must be authenticated to perform this operation."
                )

            app = apps.get_app_config(app_name.value)

            if app in ModelManger.installed_apps:
                # Get the model directly
                model = apps.get_model(app.label, model_name)

                if model in ModelManger.quer_models and has_view_permission(
                    user, model
                ):
                    excluded_fields = ModelManger.get_exclude_fields(model)

                    # Generate filterable fields and filterset class
                    filterable_fields, _filterset_class = generate_filterset(
                        model, excluded_fields
                    )

                    # Check user permission for this model
                    if user.has_perm(f"{app.label}.view_{model_name.lower()}"):
                        field_info_list = []

                        # Handle standard fields
                        for field in model._meta.fields:
                            if field.name not in ModelManger.get_exclude_fields(model):
                                additional_info = get_additional_field_info(field)

                                # Determine the related table name for relational fields
                                relation_table = None
                                if isinstance(
                                    field, (models.OneToOneField, models.ForeignKey)
                                ):
                                    relation_table = (
                                        field.related_model._meta.model_name
                                    )

                                field_info = FieldInfo(
                                    field_name=to_camel_case(field.name),
                                    field_type=type(field).__name__,
                                    relation_table=relation_table,  # Include relation table information
                                    **additional_info,
                                )
                                field_info_list.append(field_info)

                        # Handle ManyToMany fields
                        for field in model._meta.many_to_many:
                            if field.name not in ModelManger.get_exclude_fields(model):
                                additional_info = get_additional_field_info(field)

                                relation_table = field.related_model._meta.model_name

                                field_info = FieldInfo(
                                    field_name=to_camel_case(field.name),
                                    field_type=type(field).__name__,
                                    relation_table=relation_table,  # Include relation table information
                                    **additional_info,
                                )
                                field_info_list.append(field_info)

                        # Generate table info
                        table_info = TableInfo(
                            model_name=model._meta.model_name,
                            fields=field_info_list,
                            filter_fields=filterable_fields,  # Include filterable_fields in TableInfo
                            table_verbose_name=model._meta.verbose_name,
                            can_edit=has_edit_permission(user, model),
                            can_del=has_delete_permission(user, model),
                            can_add=has_add_permission(user, model),
                            model_icon=ModelManger.get_model_icon(
                                app.label, model._meta.model_name
                            ),
                            pk_field_name=model._meta.pk.name,
                        )
                        return table_info
                    else:
                        raise PermissionDenied(
                            "You don't have permission to access this model."
                        )
                else:
                    raise PermissionDenied("Model not allowed in queries.")
            else:
                raise PermissionDenied(
                    "You don't have permission to access this app or it does not exist in installed apps."
                )

        def resolve_all_apps(self, info):
            user = info.context.user
            if not user.is_authenticated:
                raise PermissionDenied(
                    "You must be authenticated to perform this operation."
                )

            # Get all installed Django apps
            installed_apps = ModelManger.installed_apps
            # Define a helper function to get additional field info
            # Create a list of AppInfo objects containing app names and their tables with fields
            app_info_list = []
            for app in installed_apps:
                tables_info = []
                for model in app.get_models():
                    if model in ModelManger.quer_models and has_view_permission(
                        user, model
                    ):
                        # Retrieve excluded fields from ModelManger
                        excluded_fields = ModelManger.get_exclude_fields(model)

                        # Generate filterable fields and filterset class
                        filterable_fields, _filterset_class = generate_filterset(
                            model, excluded_fields
                        )

                        # Generate field info list
                        field_info_list = []
                        for field in model._meta.fields:
                            if (
                                field.name not in excluded_fields
                            ):  # Check if the field should be excluded
                                additional_info = get_additional_field_info(field)
                                field_info = FieldInfo(
                                    field_name=to_camel_case(field.name),
                                    field_type=type(field).__name__,
                                    **additional_info,
                                )
                                field_info_list.append(field_info)

                        # Generate table info
                        table_info = TableInfo(
                            model_name=model._meta.model_name,
                            fields=field_info_list,
                            filter_fields=filterable_fields,  # Include filterable_fields in TableInfo
                            table_verbose_name=model._meta.verbose_name,
                            can_edit=has_edit_permission(user, model),
                            can_del=has_delete_permission(user, model),
                            can_add=has_add_permission(user, model),
                            model_icon=ModelManger.get_model_icon(
                                app.label, model._meta.model_name
                            ),
                            pk_field_name=model._meta.pk.name,
                        )
                        tables_info.append(table_info)

                if len(tables_info) > 0:
                    app_info = AppInfo(
                        app_name=app.label,
                        tables=tables_info,
                        app_verbose_name=app.verbose_name,
                        app_icon=ModelManger.get_app_icon(app.label),
                    )
                    app_info_list.append(app_info)

            return app_info_list

        for model in apps.get_models():
            exclude_fileds = ModelManger.get_exclude_fields(model)
            # Generate filterable fields and filterset class
            _filterable_fields, filterset_class = generate_filterset(
                model, exclude_fileds
            )

            model_type = generate_model_type(model, exclude_fileds)
            # print(model_type)
            if (
                model in ModelManger.quer_models
            ):  # to solve problem if table have forgienkey to another table exclude to exculde filed itself
                attrs[model._meta.model_name] = DjangoFilterConnectionField(
                    model_type, filterset_class=filterset_class
                )



        
       # Define your dynamic search field
        attrs["dynamic_search"] = List(
            DynamicSearchResultType,
            app_name=String(required=True),
            model_name=String(required=True),
            search_term=String(required=True),
            resolver=resolve_dynamic_search
        )

        attrs["get_field_value"] = get_field_value
        attrs["resolve_all_apps"] = resolve_all_apps
        attrs["resolve_fields_by_table"] = resolve_fields_by_table
        attrs["all_apps"] = List(AppInfo)
        attrs["fields_by_table"] = Field(
            TableInfo,
            app_name=AppsEnum(required=True),
            model_name=String(required=True),
        )

        return super(QueryMeta, cls).__new__(cls, name, bases, attrs)


class Query(ObjectType, metaclass=QueryMeta):

    pass


class MutationMeta(ObjectTypeMeta):

    def __new__(cls, name, bases, attrs):

        for model in apps.get_models():
            execlude_fileds = ModelManger.get_exclude_fields(model)
            create_class = generate_create_mutation(
                model=model,
                execlude_fileds=execlude_fileds,
                has_permission_func=has_add_permission,
            )
            delete_class = generate_delete_mutation(
                model=model, has_permission_func=has_delete_permission
            )
            update_mutation = generate_update_mutation(
                model=model,
                has_permission_func=has_edit_permission,
                execlude_fileds=execlude_fileds,
            )

            if model in ModelManger.mutation_models:
                attrs["create_" + model._meta.model_name] = create_class.Field()
                attrs["delete_" + model._meta.model_name] = delete_class.Field()

                attrs["update_" + model._meta.model_name] = update_mutation.Field()
        attrs["Update_User_Password"] = UpdateUserPassword.Field()

        return super(MutationMeta, cls).__new__(cls, name, bases, attrs)


class Mutationql(ObjectType, metaclass=MutationMeta):
    pass


# Custom metaclass extending Graphene's ObjectTypeMeta
class SubscriptionMeta(ObjectTypeMeta):
    def __new__(cls, name, bases, attrs):

        for model in apps.get_models():
            execlude_fileds = ModelManger.get_exclude_fields(model)
            model_type = generate_model_type(model=model, exclude=execlude_fileds)
            model_name = get_model_name_instance(model_type)

            if model in ModelManger.subscription_models:
                attrs[model._meta.model_name + "_created"] = Field(
                    model_type,
                    subscribe=Boolean(
                        description=f"Subscribe to {model_name} creation events.",
                        required=True,
                    ),
                )
                attrs[model._meta.model_name + "_updated"] = Field(
                    model_type,
                    subscribe=Boolean(
                        description=f"Subscribe to {model_name} creation events.",
                        required=True,
                    ),
                    id=String(required=True),
                )
                attrs[model._meta.model_name + "_deleted"] = Field(
                    model_type,
                    subscribe=Boolean(
                        description=f"Subscribe to {model_name} creation events.",
                        required=True,
                    ),
                    id=String(required=True),
                )
                attrs[model._meta.model_name + "_created_updated_deleted"] = Field(
                    model_type,
                    subscribe=Boolean(
                        description=f"Subscribe to {model_name} creation events.",
                        required=True,
                    ),
                    id=String(),
                )

                attrs["resolve_" + model._meta.model_name + "_created"] = (
                    lambda self, info, subscribe, model=model, model_name=model_name, has_permission_func=has_add_permission: helper_function_created(
                        self,
                        info=info,
                        model=model,
                        model_name=model_name,
                        subscribe=subscribe,
                        has_permission_func=has_add_permission,
                    )
                )
                attrs["resolve_" + model._meta.model_name + "_updated"] = (
                    lambda self, info, subscribe, id, model=model, model_name=model_name, has_permission_func=has_edit_permission: helper_function_updated(
                        self,
                        info=info,
                        model=model,
                        model_name=model_name,
                        subscribe=subscribe,
                        id=id,
                        has_permission_func=has_edit_permission,
                    )
                )
                attrs["resolve_" + model._meta.model_name + "_deleted"] = (
                    lambda self, info, subscribe, id, model=model, model_name=model_name, has_permission_func=has_delete_permission: helper_function_deleted(
                        self,
                        info=info,
                        model=model,
                        model_name=model_name,
                        subscribe=subscribe,
                        id=id,
                        has_permission_func=has_delete_permission,
                    )
                )
                attrs[
                    "resolve_" + model._meta.model_name + "_created_updated_deleted"
                ] = lambda self, info, subscribe, id=None, model=model, model_name=model_name, has_permission_func=has_add_edit_del_permission: helper_function_created_updated_deleted(
                    self,
                    info=info,
                    model=model,
                    model_name=model_name,
                    subscribe=subscribe,
                    id=id,
                    has_permission_func=has_add_edit_del_permission,
                )
        return super(SubscriptionMeta, cls).__new__(cls, name, bases, attrs)


##ss
# Subscription class using the custom metaclass
class Subscription(ObjectType, metaclass=SubscriptionMeta):
    # Placeholder for explicitly defined fields if necessary

    pass


schema = Schema(query=Query, mutation=Mutationql, subscription=Subscription)
# print(schema)


class LoginMutation(Mutation):
    class Arguments:
        username_or_email = String(required=True)
        password = String(required=True)

    token = String()
    msg = String()

    @staticmethod
    def mutate(self, info, username_or_email, password):
        user = None

        # Fetch the user based on username or email
        users = User.objects.filter(
            Q(email=username_or_email) | Q(username=username_or_email)
        )
        print(User)
        if users.exists():
            print("wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww")
            print(users[0].username)
            print(password)
            user = authenticate(username=users[0].username, password=password)
        print(user)
        if user:

            token, _ = Token.objects.get_or_create(user=user)
            return LoginMutation(token=token, msg="Sign-in successful")
        else:
            return LoginMutation(msg="Invalid username or password")


class AnnonyQuery(ObjectType):

    # Add a dummy field to satisfy the requirement
    dummy = String()

    def resolve_dummy(self, info):
        return "This is a dummy field"


class AnnonyMutation(ObjectType):

    login = LoginMutation.Field()


AnnonySchema = Schema(query=AnnonyQuery, mutation=AnnonyMutation)
