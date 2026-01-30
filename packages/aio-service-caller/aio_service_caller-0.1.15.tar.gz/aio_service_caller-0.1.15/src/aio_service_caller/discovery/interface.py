"""服务发现接口定义"""
from abc import ABC, abstractmethod
from typing import List, Optional
from ..models.service_instance import ServiceInstance


class IServiceDiscovery(ABC):
    """服务发现接口"""

    @abstractmethod
    async def get_instances(
        self,
        service_name: str,
        healthy_only: bool = True
    ) -> List[ServiceInstance]:
        """根据服务名获取实例列表

        Args:
            service_name: 服务名
            cluster: 集群名，可选
            healthy_only: 是否只返回健康的实例

        Returns:
            服务实例列表
        """
        pass

    @abstractmethod
    async def get_one_instance(
        self,
        service_name: str,
        healthy_only: bool = True
    ) -> Optional[ServiceInstance]:
        """根据服务名获取单个实例

        Args:
            service_name: 服务名
            cluster: 集群名，可选
            healthy_only: 是否只返回健康的实例

        Returns:
            单个服务实例，如果没有找到则返回None
        """
        pass


class IServiceRegistry(ABC):
    """服务注册接口"""

    @abstractmethod
    async def register(
        self,
        service_name: str,
        ip: str,
        port: int,
        weight: float = 1.0,
        cluster: str = None,
        metadata: dict = None
    ) -> bool:
        """注册服务实例

        Args:
            service_name: 服务名
            ip: IP地址
            port: 端口
            weight: 权重
            cluster: 集群名
            metadata: 元数据

        Returns:
            注册是否成功
        """
        pass

    @abstractmethod
    async def deregister(
        self,
        service_name: str,
        ip: str,
        port: int,
        cluster: str = None
    ) -> bool:
        """注销服务实例

        Args:
            service_name: 服务名
            ip: IP地址
            port: 端口
            cluster: 集群名

        Returns:
            注销是否成功
        """
        pass