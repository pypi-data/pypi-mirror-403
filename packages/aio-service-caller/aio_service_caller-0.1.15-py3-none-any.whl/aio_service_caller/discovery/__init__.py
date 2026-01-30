from .interface import IServiceDiscovery, IServiceRegistry
from .nacos_discovery import NacosServiceDiscovery
from .nacos_registry import NacosServiceRegistry

__all__ = [
    "IServiceDiscovery",
    "IServiceRegistry",
    "NacosServiceDiscovery",
    "NacosServiceRegistry",
]
