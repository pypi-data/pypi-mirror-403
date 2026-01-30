from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django_boosted import AdminBoostModel
from providerkit.kit import FIELDS_PROVIDER_BASE
from providerkit.kit.config import FIELDS_CONFIG_BASE
from providerkit.kit.package import FIELDS_PACKAGE_BASE
from providerkit.kit.service import FIELDS_SERVICE_BASE

#FIELDS_SERVICE_BASE_CUSTOM = {key: value for key, value in FIELDS_PROVIDER_BASE.items() if key not in ['display_name', 'name', 'description']}
FIELDS_PROVIDERKIT = {
    **FIELDS_PROVIDER_BASE,
    **FIELDS_CONFIG_BASE,
    **FIELDS_PACKAGE_BASE,
    **FIELDS_SERVICE_BASE,
}


list_display = ['admin_display_name']
list_display += list(FIELDS_PROVIDER_BASE.keys())[3:]
list_display.append(list(FIELDS_CONFIG_BASE.keys())[-1])
list_display.append(list(FIELDS_PACKAGE_BASE.keys())[-1])
list_display.append(list(FIELDS_SERVICE_BASE.keys())[-1])

class BaseProviderAdminFilters(admin.SimpleListFilter):
    """Filter for base provider model."""
    title = _("Base provider")
    parameter_name = "base_provider"
    field: str | None = None

    def lookups(self, request, model_admin):  # noqa: ARG002
        return (
            ("1", _("Yes")),
            ("0", _("No")),
        )

    def queryset(self, request, queryset):  # noqa: ARG002
        if self.field and self.value():
            filter_value = self.value() == "1"
            return queryset.filter(**{self.field: filter_value})
        return queryset


class PackagesInstalledFilter(BaseProviderAdminFilters):
    """Filter for packages installed status using pkg alias."""
    title = _("Packages installed")
    parameter_name = "pkg"
    field = "are_packages_installed"


class ServicesImplementedFilter(BaseProviderAdminFilters):
    """Filter for services implemented status using svc alias."""
    title = _("Services implemented")
    parameter_name = "svc"
    field = "are_services_implemented"


class ConfigReadyFilter(BaseProviderAdminFilters):
    """Filter for config ready status using cfg alias."""
    title = _("Config ready")
    parameter_name = "cfg"
    field = "is_config_ready"


class BaseProviderAdmin(AdminBoostModel):
    """Admin for provider model."""

    list_display = list_display
    search_fields = tuple(FIELDS_PROVIDER_BASE.keys())
    readonly_fields = tuple(FIELDS_PROVIDERKIT.keys())
    fieldsets = [
        (None, {'fields': tuple(FIELDS_PROVIDER_BASE.keys())}),
    ]
    list_filter = [PackagesInstalledFilter, ServicesImplementedFilter, ConfigReadyFilter]

    def get_list_display(self, request):
        return list(super().get_list_display(request)) + self.get_service_fields()

    def get_service_fields(self):
        fields = []
        if hasattr(self.model, "has_service_fields"):
            for field in self.model.has_service_fields:
                if field not in fields:
                    fields.append(field)
                cost_field = field.replace("has_", "")
                cost_field = f"{cost_field}_cost"
                if cost_field in self.model.cost_service_fields and cost_field not in fields:
                    fields.append(cost_field)
        return fields

    def admin_display_name(self, obj):
        return self.format_with_help_text(obj.display_name, obj.description)

    def change_fieldsets(self):
        self.add_to_fieldset('Config', list(FIELDS_CONFIG_BASE.keys()))
        self.add_to_fieldset('Packages', list(FIELDS_PACKAGE_BASE.keys()))
        self.add_to_fieldset('Services', list(FIELDS_SERVICE_BASE.keys()))
        self.add_to_fieldset('Cost', ['costs_services'])
