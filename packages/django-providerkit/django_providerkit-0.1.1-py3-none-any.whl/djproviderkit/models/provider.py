from django.db import models
from django.utils.translation import gettext_lazy as _
from providerkit.providers.base import ProviderListBase
from virtualqueryset.models import VirtualModel

from djproviderkit.managers import BaseProviderManager

from .service import define_provider_fields, define_service_fields

services = list(ProviderListBase.services_cfg.keys())

@define_provider_fields(primary_key='name')
@define_service_fields(services)
class ProviderkitModel(VirtualModel):
    """Virtual model for providers."""
    name: models.CharField = models.CharField(
        max_length=255,
        verbose_name=_('Name'),
        help_text=_('Provider name'),
        primary_key=True,
    )
    objects = BaseProviderManager()

    class Meta:
        app_label = 'djproviderkit'
        managed = False
        verbose_name = _('Provider')
        verbose_name_plural = _('Providers')

    def __str__(self) -> str:
        return str(self.name)

