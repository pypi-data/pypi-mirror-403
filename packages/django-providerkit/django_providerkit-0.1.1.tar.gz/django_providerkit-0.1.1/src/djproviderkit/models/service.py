from django.db import models
from providerkit.kit import FIELDS_PROVIDER_BASE
from providerkit.kit.config import FIELDS_CONFIG_BASE
from providerkit.kit.package import FIELDS_PACKAGE_BASE
from providerkit.kit.service import FIELDS_SERVICE_BASE
from qualitybase.services.utils import snake_to_camel

from djproviderkit import fields_associations
from djproviderkit.managers import BaseProviderManager

FIELDS_PROVIDERKIT = {
    **FIELDS_PROVIDER_BASE,
    **FIELDS_CONFIG_BASE,
    **FIELDS_PACKAGE_BASE,
    **FIELDS_SERVICE_BASE,
}


class ServiceProviderModel(models.Model):
    objects = BaseProviderManager()

    class Meta:
        managed = False
        abstract = True


def create_service_provider_model(name, fields, app_label, field_id):
    """Create a service provider model."""
    attrs = {
        '__module__': __name__,
        'Meta': type('Meta', (), {'app_label': app_label}),
    }

    fields_to_add = {
        field: fields_associations[cfg['format']](
            verbose_name=cfg['label'],
            help_text=cfg['description'],
            primary_key=field == field_id,
        )
        for field, cfg in fields.items()
    }

    attrs.update(fields_to_add)
    model_name = snake_to_camel(name) + 'ServiceProviderModel'

    return type(model_name, (ServiceProviderModel,), attrs)


def define_provider_fields(primary_key="id", add_fields=None):
    """Decorator to automatically add provider fields to a model."""
    def decorator(cls):
        for field, value in FIELDS_PROVIDERKIT.items():
            if field == primary_key:
                continue
            db_field = fields_associations[value['format']](
                verbose_name=value['label'], help_text=value['description']
            )
            cls.add_to_class(field, db_field)

        @property
        def _provider(self):
            """Get the original provider from the manager."""
            if hasattr(self.__class__.objects, '_providers_by_name'):
                return self.__class__.objects._providers_by_name.get(self.name)
            return None

        cls.add_to_class("_provider", _provider)

        @property
        def costs_services(self):
            """Get costs for all services."""
            provider = self._provider if self._provider else self
            if hasattr(provider, 'get_costs_services'):
                return provider.get_costs_services()
            return {}

        cls.add_to_class("costs_services", costs_services)

        if add_fields:
            for field, value in add_fields.items():
                db_field = fields_associations[value['format']](
                    verbose_name=value['label'], help_text=value['description']
                )
                cls.add_to_class(field, db_field)

        return cls
    return decorator

class ServiceProperty:
    """Property descriptor with admin attributes."""

    def __init__(self, func, short_description: str, boolean: bool = False):
        self.func = func
        self.short_description = short_description
        self.boolean = boolean

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        return self.func(obj)


def define_service_fields(services: list[str]):
    """Decorator to automatically add service fields to a model."""
    def decorator(cls):
        fields_service = []
        fields_cost = []
        for service in services:
            def make_has_service(svc: str):
                def has_service(self):
                    provider = self._provider if self._provider else self
                    return hasattr(provider, svc) and callable(getattr(provider, svc))

                return ServiceProperty(has_service, f"Has {svc}", boolean=True)

            def make_cost_service(svc: str):
                def cost_service(self):
                    provider = self._provider if self._provider else self
                    if hasattr(provider, 'get_cost'):
                        cost = provider.get_cost(svc)
                        if cost in (None, 0, 'free'):
                            return "-"
                        return f"${cost:.5f}"
                    return "-"

                return ServiceProperty(cost_service, f"Cost {svc}")

            fields_service.append(f"has_{service}")
            cls.add_to_class(f"has_{service}", make_has_service(service))

            fields_cost.append(f"{service}_cost")
            cls.add_to_class(f"{service}_cost", make_cost_service(service))

        cls.add_to_class("has_service_fields", fields_service)
        cls.add_to_class("cost_service_fields", fields_cost)
        return cls
    return decorator


def define_fields_from_config(fields_config: dict, primary_key: str | None = None):
    """Decorator to automatically add fields to a model from a fields configuration."""
    def decorator(cls):
        for field, value in fields_config.items():
            if field == primary_key:
                continue

            db_field = fields_associations[value['format']](
                verbose_name=value['label'], help_text=value['description']
            )

            if value['format'] in ('str', 'text'):
                db_field.blank = True
                if value['format'] == 'text':
                    db_field.max_length = None
                elif 'reference' in field or 'id' in field:
                    db_field.max_length = 255
                else:
                    db_field.max_length = 500
            elif value['format'] == 'float':
                db_field.null = True
                db_field.blank = True

            cls.add_to_class(field, db_field)

        return cls
    return decorator
