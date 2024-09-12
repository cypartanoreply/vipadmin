# model_manager.py


from django.apps import apps


class VipModelManger:
    quer_models = list(apps.get_models())
    mutation_models = list(apps.get_models())
    subscription_models = list(apps.get_models())
    installed_apps = list(apps.get_app_configs())
    exclude_fields = {}
    app_icon_list = {}
    model_icon_list = {}

    def exclude(self, model, on_query, on_mutation, on_subscription, fields=None):

        if (
            fields == None
            or fields == ["*"]
            or fields == "__all__"
            or fields == ["__All__"]
        ):

            if on_query and model in self.quer_models:
                # print(apps.get_models())
                print(model)
                self.quer_models.remove(model)
                # print(apps.get_models())
            if on_mutation and model in self.mutation_models:
                self.mutation_models.remove(model)

            if on_subscription and model in self.subscription_models:
                self.subscription_models.remove(model)
        else:
            self.exclude_fields[model] = fields

    def get_exclude_fields(self, model):
        if model in self.exclude_fields:
            return self.exclude_fields[model]
        else:
            return []

    def exclude_app(self, app_name):
        app = apps.get_app_config(app_name)
        if apps.is_installed(app_name) and app in self.installed_apps:

            self.installed_apps.remove(app)
            for model in app.get_models():
                self.exclude(
                    model=model, on_query=True, on_mutation=True, on_subscription=True
                )

    def set_app_icon(self, app_name, icon_url):
        installed_apps = [app_config.name for app_config in self.installed_apps]
        installed_apps_string = ", ".join(installed_apps)
        if app_name in installed_apps_string:
            self.app_icon_list[app_name] = icon_url
            return self.app_icon_list

    def get_app_icon(self, app_name):
        if app_name in self.app_icon_list:
            return self.app_icon_list[app_name]
        else:
            return None

    def set_model_icon(self, app_name, model_name, icon_url):
        for model in self.quer_models:
            if (
                model.__name__.lower() == model_name.lower()
                and model.__module__.startswith(app_name)
            ):
                self.model_icon_list[(app_name.lower(), model_name.lower())] = icon_url
                # print(self.model_icon_list)
                return self.model_icon_list  # Model found and icon set
        return None  # Model not found in the specified app

    def get_model_icon(self, app_name, model_name):

        return self.model_icon_list.get((app_name.lower(), model_name.lower()), None)


ModelManger = VipModelManger()
