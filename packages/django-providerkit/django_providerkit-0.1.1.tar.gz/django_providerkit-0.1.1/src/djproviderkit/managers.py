from typing import Any

from providerkit.helpers import get_providerkit
from virtualqueryset.managers import VirtualManager


class BaseProviderManager(VirtualManager):
    """Base manager for provider models."""

    package_name = 'providerkit'
    _providers_by_name = {}  # Cache providers by name

    def get_data(self) -> list[Any]:
        if not self.model:
            return []

        pvk = get_providerkit()
        providers = pvk.get_providers(lib_name=self.package_name)

        if isinstance(providers, dict):
            providers = list(providers.values())

        # Store providers in manager cache
        self._providers_by_name.clear()
        for provider in providers:
            self._providers_by_name[provider.name] = provider

        return list(providers)

class BaseServiceProviderManager(VirtualManager):
    _commands = {}
    _args_available = []
    _default_command = None

    def __init__(self, **kwargs: Any):
        super().__init__()
        for arg in self._args_available:
            setattr(self, arg, kwargs.get(arg))
        self._command = kwargs.get("command", self._default_command)
        self._cached_providers = {}
        self._cached_data_search_company = {}
        self._cached_data_search_company_by_reference = {}

    def _clear_cached_command(self, command: str) -> None:
        setattr(self, f"_cached_data_{command}", {})

    def set_cached_command(self, command: str, cache: Any, **kwargs: Any) -> Any:
        cache = self.queryset_class(model=self.model, data=cache)
        setattr(self, f"_cached_data_{command}", {"kwargs": kwargs, "data": cache})
        return self.get_cached_command(command, **kwargs)

    def get_cached_command(self, command: str, **kwargs: Any) -> Any:
        cache = getattr(self, f"_cached_data_{command}", {})
        if kwargs == cache.get("kwargs", {}) and cache.get("data") is not None:
            return cache.get("data")
        return None

    def get_command_data_list(self, results: Any, command: str) -> list[Any]:
        data_list = []
        for result in results:
            if isinstance(result, dict) and 'provider' in result:
                if "error" in result:
                    continue
                provider_obj = result['provider']
                normalize_data = provider_obj.get_service_normalize(command)  # type: ignore[attr-defined]
                if isinstance(normalize_data, list):
                    data_list.extend(normalize_data)
                else:
                    data_list.append(normalize_data)
        return data_list

    def get_response_times(self, command: str) -> dict[str, float]:
        times = self._cached_providers.get(command, [])
        return {provider["name"]: provider["response_time"] for provider in times}

    def get_raw_result(self, command: str, **_kwargs: Any) -> Any:
        raw = self._cached_providers.get(command, {})
        return raw

    def get_queryset_command(self, command: str, **kwargs: Any) -> Any:
        cached = self.get_cached_command(command)
        if not cached or kwargs.get("ignore_cache", False):
            self._clear_cached_command(command)
            command_func = self._commands[command]
            results = command_func(**kwargs)
            self._cached_providers[command] = results
            data_list = self.get_command_data_list(results, command)
            cached = self.set_cached_command(command, data_list, **kwargs)
        return cached

    def get_data(self) -> Any:
        if not self.query and not self.code:
            return self.queryset_class(model=self.model, data=[])
        command = self._command
        kwargs = {
            "first": self.first,
            "attribute_search": self.attribute_search,
        }
        if self.backend:
            kwargs["attribute_search"] = {"name": self.backend}
        return self.get_queryset_command(command, **kwargs)

