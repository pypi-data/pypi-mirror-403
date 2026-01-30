from providerkit.providers.base import ProviderListBase

from .provider import ProviderkitModel
from .service import create_service_provider_model

services_models = []
for svc, cfg in ProviderListBase.services_cfg.items():
    model = create_service_provider_model(svc, cfg['fields'], 'djproviderkit', 'name')
    services_models.append(model)
    globals()[str(model.__name__)] = model

__all__ = ['ProviderkitModel', *[str(model.__name__) for model in services_models]]
