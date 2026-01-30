from .interface import ILoadBalancerStrategy
from .strategies import RoundRobinStrategy, RandomStrategy, WeightedRandomStrategy, WeightedRoundRobinStrategy
from ..models import LoadBalancerType


class LoadBalancerFactory:
    """负载均衡工厂类"""
    @classmethod
    def create(cls, strategy: LoadBalancerType) -> ILoadBalancerStrategy:
        """创建负载均衡策略实例"""
        if strategy == LoadBalancerType.ROUND_ROBIN:
            return RoundRobinStrategy()
        elif strategy == LoadBalancerType.RANDOM:
            return RandomStrategy()
        elif strategy == LoadBalancerType.WEIGHTED_RANDOM:
            return WeightedRandomStrategy()
        elif strategy == LoadBalancerType.WEIGHTED_ROUND_ROBIN:
            return WeightedRoundRobinStrategy()
        else:
            raise ValueError(f"Invalid load balancer strategy: {strategy}")