import asyncio
import importlib.util
from typing import Optional, Any

from ..discovery import NacosServiceDiscovery, NacosServiceRegistry
from ..interceptor import IServiceInterceptor
from ..http import AsyncServiceTemplate
from ..load_balancer import LoadBalancerFactory
from ..models import NacosAppConfig, ServiceCallerConfig


class ServiceManager:
    """服务管理器"""

    def __init__(self, *, app_config: Optional[NacosAppConfig] = None,
                 service_caller_config: Optional[ServiceCallerConfig] = None,
                 config_manager = None,
                 interceptors: Optional[list[IServiceInterceptor]] = None,
                 **kwargs):
        """
        Configuration priority:
        1. The passed-in app_config and service_caller_config
        2. The configuration retrieved from config_manager
        3. If none of the above exist, raise an error
        """
        self._config_manager = config_manager
        self._app_config: Optional[NacosAppConfig] = app_config
        self._service_caller_config: Optional[ServiceCallerConfig] = service_caller_config
        self._gen_config_from_config_manage()
        if not self._app_config:
            raise ValueError("No app_config found.")
        if not self._service_caller_config:
            self.service_caller_config = ServiceCallerConfig()
        self._interceptors = interceptors or []
        self._kwargs = kwargs
        self._registry: Optional[NacosServiceRegistry] = None
        self._discovery: Optional[NacosServiceDiscovery] = None
        self._lb_strategy = LoadBalancerFactory.create(self._service_caller_config.lb_type)
        self._service_template: Optional[AsyncServiceTemplate] = None

    def _gen_config_from_config_manage(self):
        if not importlib.util.find_spec("yamlpyconfig"):
            return
        from yamlpyconfig import ConfigManager
        if self._config_manager and isinstance(self._config_manager, ConfigManager):
            if not self._app_config:
                self._app_config = NacosAppConfig.load_nacos_config(self._config_manager.get_config())
            if not self._service_caller_config:
                self._service_caller_config = ServiceCallerConfig.load_service_caller_config(
                    self._config_manager.get_config())

    async def get_interceptors(self) -> tuple:
        return await self._service_template.get_interceptors()

    async def add_interceptor(self, interceptor: IServiceInterceptor) -> None:
        """动态添加拦截器"""
        await self._service_template.add_interceptor(interceptor)

    async def add_interceptors(self, interceptors: list[IServiceInterceptor]) -> None:
        """动态批量添加拦截器"""
        await self._service_template.add_interceptors(interceptors)

    async def remove_interceptor(self, name: str) -> None:
        """按名称移除拦截器"""
        await self._service_template.remove_interceptor(name)

    async def clear_interceptors(self) -> None:
        """清空所有拦截器"""
        await self._service_template.clear_interceptors()

    async def start(self):
        """启动服务"""
        if not self._registry:
            self._registry = await NacosServiceRegistry.create(
                server_addresses=self._app_config.server_addr,
                namespace=self._app_config.namespace,
                group_name=self._app_config.group,
                username=self._app_config.username,
                password=self._app_config.password,
                access_key=self._app_config.access_key,
                secret_key=self._app_config.secret_key,
                **self._kwargs
            )
            while not await self._registry.register(self._app_config.app_name, self._app_config.ip, self._app_config.port,
                                          self._app_config.weight, self._app_config.cluster):
                await asyncio.sleep(1)
        if not self._discovery:
            self._discovery = await NacosServiceDiscovery.create(
                server_addresses=self._app_config.server_addr,
                namespace=self._app_config.namespace,
                group_name=self._app_config.group,
                cluster_name=self._app_config.cluster,
                username=self._app_config.username,
                password=self._app_config.password,
                access_key=self._app_config.access_key,
                secret_key=self._app_config.secret_key,
                **self._kwargs
            )
            self._service_template = AsyncServiceTemplate(
                self._discovery,
                self._lb_strategy,
                self._interceptors,
                self._service_caller_config.connection_timeout,
                self._service_caller_config.read_timeout,
                self._service_caller_config.connection_pool_size
            )

    async def __aenter__(self):
        await self.start()
        return self

    async def stop(self):
        if self._service_template:
            await self._service_template.close()
        if self._registry:
            await self._registry.deregister(self._app_config.app_name, self._app_config.ip, self._app_config.port,
                                            self._app_config.cluster)
            await self._registry.close()
        if self._discovery:
            await self._discovery.close()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop()

    # 便捷方法
    async def get(self, service_name: str, path: str, **kwargs) -> Any:
        """GET请求"""
        return await self._service_template.get(service_name, path, **kwargs)

    async def post(self, service_name: str, path: str, **kwargs) -> Any:
        """POST请求"""
        return await self._service_template.post(service_name, path, **kwargs)

    async def put(self, service_name: str, path: str, **kwargs) -> Any:
        """PUT请求"""
        return await self._service_template.put(service_name, path, **kwargs)

    async def delete(self, service_name: str, path: str, **kwargs) -> Any:
        """DELETE请求"""
        return await self._service_template.delete(service_name, path, **kwargs)

    async def patch(self, service_name: str, path: str, **kwargs) -> Any:
        """PATCH请求"""
        return await self._service_template.patch(service_name, path, **kwargs)

    # 便捷方法
    def raw_get(self, service_name: str, path: str, **kwargs) -> Any:
        """GET请求"""
        return self._service_template.raw_get(service_name, path, **kwargs)

    def raw_post(self, service_name: str, path: str, **kwargs) -> Any:
        """POST请求"""
        return self._service_template.raw_post(service_name, path, **kwargs)

    def raw_put(self, service_name: str, path: str, **kwargs) -> Any:
        """PUT请求"""
        return self._service_template.raw_put(service_name, path, **kwargs)

    def raw_delete(self, service_name: str, path: str, **kwargs) -> Any:
        """DELETE请求"""
        return self._service_template.raw_delete(service_name, path, **kwargs)

    def raw_patch(self, service_name: str, path: str, **kwargs) -> Any:
        """PATCH请求"""
        return self._service_template.raw_patch(service_name, path, **kwargs)
