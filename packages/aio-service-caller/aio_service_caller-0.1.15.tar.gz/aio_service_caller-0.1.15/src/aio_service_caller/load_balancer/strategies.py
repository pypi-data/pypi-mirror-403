"""负载均衡策略实现"""
import random
import itertools
from typing import List, Optional, Dict, Any
from .interface import ILoadBalancerStrategy
from ..models.service_instance import ServiceInstance


class RoundRobinStrategy(ILoadBalancerStrategy):
    """轮询策略"""

    def __init__(self):
        """初始化轮询策略"""
        self._cycles: Dict[str, itertools.cycle] = {}
        self._last_instances: Dict[str, tuple] = {}

    def choose(self, instances: List[ServiceInstance]) -> Optional[ServiceInstance]:
        """轮询选择实例"""
        if not instances:
            return None

        # 获取服务名（从第一个实例中获取）
        service_name = instances[0].service_name or "default"

        # 检查实例列表是否发生变化
        current_instances_key = tuple(sorted((inst.ip, inst.port) for inst in instances))
        last_instances_key = self._last_instances.get(service_name)

        # 如果实例列表发生变化，重新创建cycle
        if last_instances_key is None or current_instances_key != last_instances_key:
            self._cycles[service_name] = itertools.cycle(instances)
            self._last_instances[service_name] = current_instances_key

        # 选择下一个实例
        try:
            return next(self._cycles[service_name])
        except StopIteration:
            # 理论上不应该发生，但作为安全措施
            self._cycles[service_name] = itertools.cycle(instances)
            return next(self._cycles[service_name])


class RandomStrategy(ILoadBalancerStrategy):
    """随机策略"""

    def choose(self, instances: List[ServiceInstance]) -> Optional[ServiceInstance]:
        """随机选择实例"""
        if not instances:
            return None
        return random.choice(instances)


class WeightedRandomStrategy(ILoadBalancerStrategy):
    """加权随机策略"""

    def choose(self, instances: List[ServiceInstance]) -> Optional[ServiceInstance]:
        """根据权重随机选择实例"""
        if not instances:
            return None

        # 过滤掉权重为0的实例
        valid_instances = [inst for inst in instances if inst.weight > 0]
        if not valid_instances:
            # 如果所有实例权重都为0，退化为随机策略
            return random.choice(instances)

        # 计算总权重
        total_weight = sum(inst.weight for inst in valid_instances)
        if total_weight <= 0:
            return random.choice(valid_instances)

        # 生成随机数
        r = random.uniform(0, total_weight)

        # 根据权重选择实例
        current_weight = 0
        for instance in valid_instances:
            current_weight += instance.weight
            if current_weight >= r:
                return instance

        # 兜底：返回最后一个实例
        return valid_instances[-1]


class WeightedRoundRobinStrategy(ILoadBalancerStrategy):
    """加权轮询策略"""

    def __init__(self):
        """初始化加权轮询策略"""
        self._weights: Dict[str, List[int]] = {}
        self._current_indices: Dict[str, int] = {}
        self._last_instances: Dict[str, tuple] = {}

    def choose(self, instances: List[ServiceInstance]) -> Optional[ServiceInstance]:
        """根据权重轮询选择实例"""
        if not instances:
            return None

        # 获取服务名
        service_name = instances[0].service_name or "default"

        # 检查实例列表是否发生变化
        current_instances_key = tuple(sorted((inst.ip, inst.port) for inst in instances))
        last_instances_key = self._last_instances.get(service_name)

        # 如果实例列表发生变化，重新计算权重
        if last_instances_key is None or current_instances_key != last_instances_key:
            self._update_weights(service_name, instances)
            self._last_instances[service_name] = current_instances_key

        # 获取当前权重列表
        weights = self._weights.get(service_name, [])
        if not weights:
            return instances[0]

        # 获取当前索引
        current_index = self._current_indices.get(service_name, 0)
        selected_index = weights[current_index]

        # 更新索引
        self._current_indices[service_name] = (current_index + 1) % len(weights)

        return instances[selected_index]

    def _update_weights(self, service_name: str, instances: List[ServiceInstance]):
        """更新权重列表"""
        # 过滤掉权重为0的实例
        valid_instances = [inst for inst in instances if inst.weight > 0]
        if not valid_instances:
            # 如果所有实例权重都为0，给每个实例权重1
            valid_instances = instances

        # 构建权重列表：每个实例根据权重出现多次
        weights = []
        for i, instance in enumerate(valid_instances):
            # 权重转换为整数，至少为1
            weight = max(1, int(instance.weight * 10))  # 乘以10提高精度
            weights.extend([i] * weight)

        self._weights[service_name] = weights
        self._current_indices[service_name] = 0