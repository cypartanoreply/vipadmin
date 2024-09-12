from django.apps import apps
from django.db.models.fields import NOT_PROVIDED


from collections import OrderedDict
from graphene.types.utils import yank_fields_from_attrs
from graphene_django.forms.mutation import (
    fields_for_form,
    DjangoModelDjangoFormMutationOptions,
    BaseDjangoFormMutation,
    _set_errors_flag_to_context,
)
from graphene_django.registry import get_global_registry

from graphene_django.types import ErrorType
from graphene import Field, InputField, Enum, List, ID, NonNull
from .model_manager import ModelManger
from django.db import models
from graphene_file_upload.scalars import Upload
from django.core.files.uploadedfile import InMemoryUploadedFile


def get_table_name_without_app(model):
    # db_table = model._meta.db_table
    # Split the table name by underscores and remove the first part (app name)
    # then join back the remaining parts if there are any
    table_name_without_app = "_".join(model.split("_")[1:])
    return table_name_without_app


def generate_apps_enum():

    installed_apps = ModelManger.installed_apps
    apps_enum = {}
    for app in installed_apps:
        # Use the app label as the enum name and value, ensure it's a valid Enum name
        apps_enum[app.label.upper()] = app.label
    return Enum("AppsEnum", apps_enum)


AppsEnum = generate_apps_enum()


def has_delete_permission(user, model):
    # Check if the user has the permission to delete objects of the given model
    return user.has_perm(f"{model._meta.app_label}.delete_{model.__name__.lower()}")


def has_view_permission(user, model):
    # Check if the user has the permission to view objects of the given model
    return user.has_perm(f"{model._meta.app_label}.view_{model.__name__.lower()}")


def has_edit_permission(user, model):
    # Check if the user has the permission to edit objects of the given model
    return user.has_perm(f"{model._meta.app_label}.change_{model.__name__.lower()}")


def has_add_permission(user, model):
    # Check if the user has the permission to add objects of the given model
    return user.has_perm(f"{model._meta.app_label}.add_{model.__name__.lower()}")


def has_add_edit_del_permission(user, model):

    # Check if the user has the permission to add objects of the given model
    return (
        user.has_perm(f"{model._meta.app_label}.add_{model.__name__.lower()}")
        and user.has_perm(f"{model._meta.app_label}.change_{model.__name__.lower()}")
        and user.has_perm(f"{model._meta.app_label}.delete_{model.__name__.lower()}")
    )


class CustomDjangoModelFormMutation(BaseDjangoFormMutation):
    class Meta:
        abstract = True

    errors = List(NonNull(ErrorType), required=True)

    @classmethod
    def __init_subclass_with_meta__(
        cls,
        form_class=None,
        model=None,
        return_field_name=None,
        only_fields=(),
        exclude_fields=(),
        **options,
    ):
        if not form_class:
            raise Exception("form_class is required for CustomDjangoModelFormMutation")

        if not model:
            model = form_class._meta.model

        if not model:
            raise Exception("model is required for CustomDjangoModelFormMutation")

        form = form_class()
        input_fields = fields_for_form(form, only_fields, exclude_fields)
        # if "id" not in exclude_fields:
        input_fields["pk"] = ID(required=True)

        registry = get_global_registry()
        model_type = registry.get_type_for_model(model)
        if not model_type:
            raise Exception(f"No type registered for model: {model.__name__}")

        if not return_field_name:
            model_name = model.__name__
            return_field_name = model_name[:1].lower() + model_name[1:]

        output_fields = OrderedDict()

        _meta = DjangoModelDjangoFormMutationOptions(cls)
        _meta.form_class = form_class
        _meta.model = model
        _meta.return_field_name = return_field_name
        _meta.fields = yank_fields_from_attrs(output_fields, _as=Field)

        input_fields = yank_fields_from_attrs(input_fields, _as=InputField)
        super().__init_subclass_with_meta__(
            _meta=_meta, input_fields=input_fields, **options
        )


class CustomUploadDjangoModelFormMutation(BaseDjangoFormMutation):
    class Meta:
        abstract = True

    errors = List(NonNull(ErrorType), required=True)

    @classmethod
    def __init_subclass_with_meta__(
        cls,
        form_class=None,
        model=None,
        return_field_name=None,
        only_fields=(),
        exclude_fields=(),
        **options,
    ):
        if not form_class:
            raise Exception("form_class is required for DjangoModelFormMutation")

        if not model:
            model = form_class._meta.model

        if not model:
            raise Exception("model is required for DjangoModelFormMutation")

        form = form_class()
        input_fields = fields_for_form(form, only_fields, exclude_fields)
        if "id" not in exclude_fields:
            input_fields["id"] = ID()

        # Handle FileField, ImageField, and ManyToManyField
        for field in model._meta.fields:
            if isinstance(field, models.FileField) or isinstance(
                field, models.ImageField
            ):
                input_fields[field.name] = Upload(required=False)

        for field in model._meta.many_to_many:
            input_fields[field.name] = List(ID, required=False)

        registry = get_global_registry()
        model_type = registry.get_type_for_model(model)
        if not model_type:
            raise Exception(f"No type registered for model: {model.__name__}")

        if not return_field_name:
            model_name = model.__name__
            return_field_name = model_name[:1].lower() + model_name[1:]

        output_fields = OrderedDict()
        output_fields[return_field_name] = Field(model_type)

        _meta = DjangoModelDjangoFormMutationOptions(cls)
        _meta.form_class = form_class
        _meta.model = model
        _meta.return_field_name = return_field_name
        _meta.fields = yank_fields_from_attrs(output_fields, _as=Field)

        input_fields = yank_fields_from_attrs(input_fields, _as=InputField)
        super().__init_subclass_with_meta__(
            _meta=_meta, input_fields=input_fields, **options
        )

    @classmethod
    def mutate_and_get_payload(cls, root, info, **input):
        files = {
            key: value
            for key, value in input.items()
            if isinstance(value, InMemoryUploadedFile)
        }
        normal_data = {
            key: value
            for key, value in input.items()
            if not isinstance(value, InMemoryUploadedFile)
        }
        many_to_many_data = {
            key: value for key, value in input.items() if isinstance(value, list)
        }

        form = cls.get_form(root, info, **normal_data)

        # Assign files to form's .files attribute if necessary
        for field_name, file in files.items():
            form.files[field_name] = file

        if form.is_valid():
            return cls.perform_mutate(form, info, many_to_many_data=many_to_many_data)
        else:
            errors = ErrorType.from_errors(form.errors)
            _set_errors_flag_to_context(info)
            return cls(errors=errors)

    @classmethod
    def perform_mutate(cls, form, info, many_to_many_data=None):
        obj = form.save(commit=False)

        # Manually assign files to model fields before saving
        for field_name, file in form.files.items():
            setattr(obj, field_name, file)

        obj.save()

        # Save many-to-many relationships
        if many_to_many_data:
            for field_name, pks in many_to_many_data.items():
                many_to_many_manager = getattr(obj, field_name)
                many_to_many_manager.set(pks)

        kwargs = {cls._meta.return_field_name: obj}
        return cls(errors=[], **kwargs)


def get_additional_field_info(field):

    additional_info = {}

    # check if the field is a password field and set the is_password attribute

    if isinstance(field, models.CharField) and field.name.lower().endswith("password"):
        additional_info["is_password"] = True
    else:
        additional_info["is_password"] = False

    if hasattr(field, "max_length"):
        additional_info["max_length"] = field.max_length

    # Check if the field has the `null` attribute
    if hasattr(field, "null"):
        print("null:", field.null)

        # Check if the field is a BooleanField
        if isinstance(field, models.BooleanField):
            additional_info["is_required"] = (
                False  # BooleanField is never required in forms
            )
        else:
            # Check if the field has the `blank` attribute
            if hasattr(field, "blank"):
                print("blank:", field.blank)
                default_value = field.default

                # Determine if the field is required
                if default_value is not NOT_PROVIDED:
                    additional_info["is_required"] = False
                else:
                    additional_info["is_required"] = not field.blank
            else:
                # If `blank` attribute is not present, assume default behavior
                additional_info["is_required"] = not field.null
    else:
        # If `null` attribute is not present, assume the field is required
        additional_info["is_required"] = True

    if hasattr(field, "default"):
        default_value = field.default
        if default_value is not NOT_PROVIDED:  # Check if default value is NOT_PROVIDED
            if callable(default_value):  # If default value is a function
                default_value = str(
                    default_value()
                )  # Convert function to string representation
            additional_info["default"] = default_value
        else:
            additional_info["default"] = None  # Set default value to null
    if hasattr(field, "choices"):
        # Transform choices into a list of dictionaries
        if field.choices is not None:
            additional_info["choices"] = [
                {"value": str(choice[0]), "label": str(choice[1])}
                for choice in field.choices
            ]
        else:
            additional_info["choices"] = None
    if hasattr(field, "verbose_name"):
        additional_info["verbose_name"] = field.verbose_name
    if hasattr(field, "help_text"):
        additional_info["help_text"] = field.help_text
    if hasattr(field, "primary_key"):
        additional_info["primary_key"] = field.primary_key
    if hasattr(field, "auto_created"):
        additional_info["auto_created"] = field.auto_created
    if hasattr(field, "unique"):
        additional_info["unique"] = field.unique
    if hasattr(field, "editable"):
        additional_info["editable"] = field.editable

    return additional_info


def to_camel_case(s):
    parts = s.split("_")
    return parts[0] + "".join(x.title() for x in parts[1:])


# Example usage:
