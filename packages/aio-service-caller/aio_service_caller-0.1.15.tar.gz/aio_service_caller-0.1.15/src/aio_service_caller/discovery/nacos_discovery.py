"""基于Nacos的服务发现实现"""
import asyncio
import logging
from typing import List, Optional, Dict

from v2.nacos import NacosNamingService, ClientConfigBuilder, GRPCConfig, Instance, SubscribeServiceParam, \
    ListInstanceParam

from .interface import IServiceDiscovery
from ..models.service_instance import ServiceInstance

logger = logging.getLogger(__name__)


class NacosServiceDiscovery(IServiceDiscovery):
    """Nacos服务发现实现"""

    def __init__(self, naming_service: NacosNamingService, group_name: str = "DEFAULT_GROUP",
                 clusters: list[str] = None, cache_ttl: int = 30):
        """初始化Nacos服务发现

        Args:
            naming_service: Nacos Naming服务客户端
            group_name: group名
            clusters: 集群名
            cache_ttl: 缓存TTL（秒）
        """
        self._client = naming_service
        self._cache: Dict[str, List[ServiceInstance]] = {}
        self._cache_ttl = cache_ttl
        self._cache_timestamps: Dict[str, float] = {}
        self._locks: Dict[str, asyncio.Lock] = {}
        self._subscriptions: Dict[str, bool] = {}
        self._group_name = group_name
        self._clusters = []
        if clusters and len(clusters) > 0:
            self._clusters = clusters

    @classmethod
    async def create(
        cls,
        server_addresses: str,
        namespace: str = "",
        group_name: str = "DEFAULT_GROUP",
        cluster_name: str = None,
        username: str = None,
        password: str = None,
        access_key: str = None,
        secret_key: str = None,
        cache_ttl: int = 30,
        **kwargs
    ) -> 'NacosServiceDiscovery':
        """创建Nacos服务发现实例

        Args:
            server_addresses: Nacos服务器地址，如 "127.0.0.1:8848"
            namespace: 命名空间
            group_name: group名
            cluster_name: 集群名
            username: 用户名
            password: 密码
            access_key: 访问密钥
            secret_key: 秘密密钥
            cache_ttl: 缓存TTL（秒）
            **kwargs: 其他配置参数

        Returns:
            NacosServiceDiscovery实例
        """
        # 构建客户端配置
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

        # 创建命名服务客户端
        naming_service = await NacosNamingService.create_naming_service(client_config)
        clusters = []
        if cluster_name:
            clusters.append(cluster_name)

        return cls(naming_service, group_name, clusters, cache_ttl)

    async def get_instances(
        self,
        service_name: str,
        healthy_only: bool = True
    ) -> List[ServiceInstance]:
        """根据服务名获取实例列表"""
        cluster_key = f"{",".join(self._clusters)}:" if self._clusters and len(self._clusters) > 0 else ""
        cache_key = f"{service_name}:{cluster_key}{healthy_only}"

        # 1. 检查缓存
        if await self._is_cache_valid(cache_key):
            return self._cache[cache_key]

        # 2. 加锁更新缓存
        lock = self._locks.setdefault(cache_key, asyncio.Lock())
        async with lock:
            # 3. 双重检查锁定模式
            if await self._is_cache_valid(cache_key):
                return self._cache[cache_key]

            # 4. 从Nacos拉取实例
            instances = await self._fetch_instances(service_name, healthy_only)

            # 5. 更新缓存
            self._cache[cache_key] = instances
            self._cache_timestamps[cache_key] = asyncio.get_event_loop().time()

            # 6. 订阅服务变化（如果还没有订阅）
            if not self._subscriptions.get(cache_key, False):
                await self._subscribe_service(service_name, healthy_only, cache_key)
                self._subscriptions[cache_key] = True

            return instances

    async def get_one_instance(
        self,
        service_name: str,
        healthy_only: bool = True
    ) -> Optional[ServiceInstance]:
        """根据服务名获取单个实例"""
        instances = await self.get_instances(service_name, healthy_only)
        return instances[0] if instances else None

    async def _is_cache_valid(self, cache_key: str) -> bool:
        """检查缓存是否有效"""
        if cache_key not in self._cache:
            return False

        if cache_key not in self._cache_timestamps:
            return False

        current_time = asyncio.get_event_loop().time()
        return (current_time - self._cache_timestamps[cache_key]) < self._cache_ttl

    async def _fetch_instances(
        self,
        service_name: str,
        healthy_only: bool = True
    ) -> List[ServiceInstance]:
        """从Nacos获取实例列表"""
        try:
            # 从Nacos获取实例
            param = ListInstanceParam(
                service_name=service_name,
                group_name=self._group_name,
                clusters=self._clusters,
                subscribe=False,
                healthy_only=healthy_only
            )
            nacos_instances = await self._client.list_instances(param)

            # 转换为ServiceInstance
            instances = []
            for nacos_instance in nacos_instances:
                instance = self._transform_instance(service_name, nacos_instance)
                instances.append(instance)

            logger.info(f"Fetched {len(instances)} instances for service '{service_name}'")
            return instances

        except Exception as e:
            logger.error(f"Failed to fetch instances for service '{service_name}': {e}")
            return []

    def _transform_instance(self, service_name: str, nacos_instance: Instance) -> ServiceInstance:
        """将Nacos实例转换为ServiceInstance"""
        return ServiceInstance(
            ip=nacos_instance.ip,
            port=nacos_instance.port,
            weight=nacos_instance.weight,
            healthy=nacos_instance.healthy,
            metadata=nacos_instance.metadata or {},
            service_name=service_name,
            cluster_name=nacos_instance.clusterName
        )

    async def _subscribe_service(
        self,
        service_name: str,
        healthy_only: bool,
        cache_key: str
    ):
        """订阅服务变化"""
        async def _on_service_change(instances: List[Instance]):
            """服务变化回调"""
            logger.info(f"Service '{service_name}' instances changed, updating cache")

            # 转换并更新缓存
            service_instances = []
            for nacos_instance in instances:
                if not healthy_only or nacos_instance.healthy:
                    instance = self._transform_instance(service_name, nacos_instance)
                    service_instances.append(instance)

            self._cache[cache_key] = service_instances
            self._cache_timestamps[cache_key] = asyncio.get_event_loop().time()

            logger.info(f"Updated cache for service '{service_name}' with {len(service_instances)} instances")

        try:
            subscribe_param = SubscribeServiceParam(
                service_name=service_name,
                group_name=self._group_name,
                clusters=self._clusters,
                subscribe_callback=_on_service_change
            )
            await self._client.subscribe(subscribe_param)
            logger.info(f"Subscribed to service '{service_name}' changes")
        except Exception as e:
            logger.error(f"Failed to subscribe to service '{service_name}': {e}")


    async def close(self):
        """
        安全地关闭底层的 Nacos Naming Service 客户端。
        """
        try:
            if self._client:
                await self._client.shutdown()
                logger.info("Discovery Nacos Naming Service client closed.")
        except Exception as e:
            logger.error(f"Error during Discovery Nacos Naming Service client close: {e}")