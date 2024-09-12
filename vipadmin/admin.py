from django.contrib import admin

# Register your models here.
from .models import *

from django.contrib.auth.models import Group, User
from django.contrib.auth.admin import GroupAdmin, UserAdmin


from .model_manager import ModelManger

# import model_manager
# Unregister the original Group model to avoid duplicate entries
admin.site.unregister(Group)
admin.site.unregister(User)
# Register the proxy model with the customized admin interface
admin.site.register(Group, GroupAdmin)
# admin.site.register(User)
admin.site.register(AllTypeModel)

admin.site.register(User, UserAdmin)
admin.site.register(OtherModel)
admin.site.register(Employee)


# ModelManger.exclude(model=AllTypeModel,on_query=True,on_mutation=True,on_subscription=True)
# ModelManger.exclude(model=Employee,on_query=True,on_mutation=True,on_subscription=False)
# ModelManger.exclude(model=Group,on_query=True,on_mutation=True,on_subscription=True)
# ModelManger.exclude(model=OtherModel,on_query=True,on_mutation=True,on_subscription=True)
# ModelManger.exclude(model=AllTypeModel,on_query=True,on_mutation=True,on_subscription=True,fields=['one_to_one_field','auto_slug_field','text_field','uuid_field'])
ModelManger.exclude(model=User, on_query=True, on_mutation=True, on_subscription=True)
# ModelManger.exclude_app('CypartaGraphqlSubscriptionsTools')
# ModelManger.exclude_app('vipadmin')
ModelManger.set_app_icon(
    "vipadmin", "https://sadakatcdn.cyparta.com/people_3369137.png"
)
ModelManger.set_app_icon("Group", "/fav.png")

ModelManger.set_model_icon(
    "vipadmin", "AllTypeModel", "https://sadakatcdn.cyparta.com/money_2454282.png"
)
