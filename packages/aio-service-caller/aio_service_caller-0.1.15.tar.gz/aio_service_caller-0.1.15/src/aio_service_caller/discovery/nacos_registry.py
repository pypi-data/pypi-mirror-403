import logging
from typing import Optional

from v2.nacos import NacosNamingService, ClientConfigBuilder, GRPCConfig, RegisterInstanceParam, DeregisterInstanceParam

from .interface import IServiceRegistry
from .registry_thread_loop import RegistryThreadLoop

logger = logging.getLogger(__name__)

class NacosServiceRegistry(IServiceRegistry):
    """Nacos服务注册实现"""

    def __init__(self, naming_service: NacosNamingService, group_name: str = "DEFAULT_GROUP",
                 thread_loop: Optional[RegistryThreadLoop] = None):
        """初始化Nacos服务注册

        Args:
            naming_service: Nacos Naming服务客户端
        """
        self._client = naming_service
        self._group_name = group_name
        self.__thread_loop = thread_loop

    @classmethod
    async def create(
        cls,
        server_addresses: str,
        namespace: str = "",
        group_name: str = "DEFAULT_GROUP",
        username: str = None,
        password: str = None,
        access_key: str = None,
        secret_key: str = None,
        **kwargs
    ) -> 'NacosServiceRegistry':
        """创建Nacos服务注册实例

        Args:
            server_addresses: Nacos服务器地址，如 "127.0.0.1:8848"
            namespace: 命名空间
            group_name: group名
            username: 用户名
            password: 密码
            access_key: 访问密钥
            secret_key: 秘密密钥
            **kwargs: 其他配置参数

        Returns:
            NacosServiceRegistry实例
        """
        # 构建客户端配置

        new_thread = kwargs.get('new_thread', True)
        thread_loop = RegistryThreadLoop.get(new_thread)
        config_builder = (ClientConfigBuilder()
                        .server_address(server_addresses)
                        .namespace_id(namespace))

        # 添加认证配置
        if username and password:
            config_builder = config_builder.username(username).password(password)
        elif access_key and secret_key:
            config_builder = config_builder.access_key(access_key).secret_key(secret_key)

        # 添加其他配置
        if 'log_level' in kwargs:
            config_builder = config_builder.log_level(kwargs['log_level'])

        # 添加GRPC配置
        grpc_config = GRPCConfig(
            grpc_timeout=kwargs.get('grpc_timeout', 5000),
            max_receive_message_length=kwargs.get('max_receive_message_length', 100 * 1024 * 1024),
            max_keep_alive_ms=kwargs.get('max_keep_alive_ms', 60 * 1000),
            initial_window_size=kwargs.get('initial_window_size', 10 * 1024 * 1024),
            initial_conn_window_size=kwargs.get('initial_conn_window_size', 10 * 1024 * 1024)
        )
        config_builder = config_builder.grpc_config(grpc_config)

        client_config = config_builder.build()
        naming_service_coro = NacosNamingService.create_naming_service(client_config)
        # 创建命名服务客户端
        naming_service: NacosNamingService = await thread_loop.run(naming_service_coro)
        return cls(naming_service, group_name, thread_loop)

    async def register(
        self,
        service_name: str,
        ip: str,
        port: int,
        weight: float = 1.0,
        cluster: str = None,
        metadata: dict = None
    ) -> bool:
        """注册服务实例"""
        return await self.__thread_loop.run(self.__register_internal(service_name, ip,
                                                                       port, weight, cluster, metadata))
    async def __register_internal(
        self,
        service_name: str,
        ip: str,
        port: int,
        weight: float = 1.0,
        cluster: str = None,
        metadata: dict = None
    ) -> bool:
        """注册服务实例"""
        try:
            param = RegisterInstanceParam(
                service_name=service_name,
                group_name=self._group_name,
                ip=ip,
                port=port,
                weight=weight,
                cluster_name=cluster or "DEFAULT",
                metadata=metadata or {},
                enabled=True,
                healthy=True,
                ephemeral=True
            )
            response = await self._client.register_instance(param)
            if response:
                logger.info(f"Successfully registered service '{service_name}' at {ip}:{port}")
                return True
            else:
                logger.error(f"Failed to register service '{service_name}' at {ip}:{port}")
                return False

        except Exception as e:
            logger.error(f"Failed to register service '{service_name}' at {ip}:{port}: {e}")
            return False

    async def deregister(
        self,
        service_name: str,
        ip: str,
        port: int,
        cluster: str = None
    ) -> bool:
        """注销服务实例"""
        try:
            param = DeregisterInstanceParam(
                service_name=service_name,
                group_name=self._group_name,
                ip=ip,
                port=port,
                cluster_name=cluster or "DEFAULT",
                ephemeral=True
            )

            response_coro = self._client.deregister_instance(param)
            response = await self.__thread_loop.run(response_coro)

            if response:
                logger.info(f"Successfully deregistered service '{service_name}' at {ip}:{port}")
                return True
            else:
                logger.error(f"Failed to deregister service '{service_name}' at {ip}:{port}")
                return False

        except Exception as e:
            logger.error(f"Failed to deregister service '{service_name}' at {ip}:{port}: {e}")
            return False

    async def close(self):
        """
        安全地关闭底层的 Nacos Naming Service 客户端。
        """
        try:
            if self._client:
                await self.__thread_loop.run(self._client.shutdown())
                logger.info("Nacos Naming Service client closed.")
        except Exception as e:
            logger.error(f"Error during Nacos client close: {e}")