from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django_boosted import AdminBoostModel
from qualitybase.services.utils import snake_to_camel


class BaseServiceAdminFilter(admin.SimpleListFilter):
    """Filter for base service model."""
    title = _("Base service")
    parameter_name = None
    field: str | None = None

    def lookups(self, request, model_admin):  # noqa: ARG002
        return (
            ("1", _("Yes")),
            ("0", _("No")),
        )

    def queryset(self, request, queryset):  # noqa: ARG002
        return queryset


class FirstServiceAdminFilter(BaseServiceAdminFilter):
    """Filter for first service model."""
    title = _("First")
    parameter_name = "first"
    field = "first"

    def lookups(self, request, model_admin):  # noqa: ARG002
        return (
            ("1", _("Yes")),
            ("0", _("No")),
        )

    def queryset(self, request, queryset):  # noqa: ARG002
        return queryset


class BackendServiceAdminFilter(BaseServiceAdminFilter):
    title = _("Backend")
    parameter_name = "bck"
    provider_model = None

    def lookups(self, request, model_admin):  # noqa: ARG002
        if self.provider_model:
            providers = self.provider_model.objects.get_queryset()
            return [(provider.name, provider.display_name) for provider in providers]
        return []

    def queryset(self, request, queryset):  # noqa: ARG002
        queryset.backend = self.value()
        return queryset


def create_service_provider_admin(name, fields, model=None, **kwargs):
    field_names = list(fields.keys())

    attrs = {
        'list_display': field_names,
        'search_fields': kwargs.get('search_fields', []),
        'readonly_fields': kwargs.get('readonly_fields', []),
        'fieldsets': kwargs.get('fieldsets'),
    }

    admin_name = snake_to_camel(name) + 'ServiceProviderAdmin'

    cls = type(admin_name, (AdminBoostModel,), attrs)

    if model:
        admin.site.register(model, cls)

    return cls
