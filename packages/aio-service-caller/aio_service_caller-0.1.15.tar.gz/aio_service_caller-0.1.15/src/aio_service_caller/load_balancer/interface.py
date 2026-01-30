"""负载均衡策略接口定义"""
from abc import ABC, abstractmethod
from typing import List, Optional
from ..models.service_instance import ServiceInstance


class ILoadBalancerStrategy(ABC):
    """负载均衡策略接口"""

    @abstractmethod
    def choose(self, instances: List[ServiceInstance]) -> Optional[ServiceInstance]:
        """从实例列表中选择一个实例

        Args:
            instances: 服务实例列表

        Returns:
            选择的服务实例，如果列表为空则返回None
        """
        pass