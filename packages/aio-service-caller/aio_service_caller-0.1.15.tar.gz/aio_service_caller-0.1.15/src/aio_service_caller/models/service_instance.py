"""服务实例模型定义"""
from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass
class ServiceInstance:
    """服务实例模型"""
    ip: str
    port: int
    weight: float = 1.0
    healthy: bool = True
    metadata: Dict[str, Any] = None
    service_name: Optional[str] = None
    cluster_name: Optional[str] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

    @property
    def host_port(self) -> str:
        """获取主机:端口字符串"""
        return f"{self.ip}:{self.port}"

    @property
    def url(self) -> str:
        """获取服务实例的URL"""
        return f"http://{self.host_port}"

    def __str__(self) -> str:
        return f"ServiceInstance({self.host_port}, weight={self.weight}, healthy={self.healthy})"

    def __repr__(self) -> str:
        return self.__str__()