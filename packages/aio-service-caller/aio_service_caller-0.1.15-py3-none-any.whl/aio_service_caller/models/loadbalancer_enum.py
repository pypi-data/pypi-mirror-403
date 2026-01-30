from enum import Enum


class LoadBalancerType(str, Enum):
    """负载均衡类型枚举"""
    ROUND_ROBIN = "round_robin"
    RANDOM = "random"
    WEIGHTED_RANDOM = "weighted_random"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"