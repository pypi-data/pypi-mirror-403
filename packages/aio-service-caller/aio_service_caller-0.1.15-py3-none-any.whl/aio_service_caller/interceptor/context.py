"""请求上下文定义"""
import time
from typing import Any, Dict, Optional
from aiohttp import ClientResponse


class RequestContext:
    """请求上下文，在拦截器链中传递"""

    def __init__(
        self,
        method: str,
        service_name: str,
        path: str,
        protocol: str = "http",
        **kwargs
    ):
        """
        初始化请求上下文

        Args:
            method: HTTP方法 (GET, POST, PUT, DELETE等)
            service_name: 服务名
            path: 请求路径
            **kwargs: 其他请求参数 (headers, params, data, json等)
        """
        self.method = method.upper()
        self.service_name = service_name
        self.path = path
        self.protocol = protocol
        if self.protocol not in ["http", "https"]:
            raise ValueError("Invalid protocol.")
        self.kwargs = kwargs

        # 请求执行过程中填充的字段
        self.resolved_url: Optional[str] = None  # LB解析后的URL
        self.selected_instance: Optional[Any] = None  # 选择的服务实例
        self.response: Optional[ClientResponse] = None  # HTTP响应
        self.exception: Optional[Exception] = None  # 异常信息
        self.result: Any = None  # 最终结果

        # 请求时间记录
        self.start_time: Optional[float] = None
        self.response_time: Optional[float] = None
        self.end_time: Optional[float] = None

        # 自定义属性存储
        self.attributes: Dict[str, Any] = {}

    @property
    def duration(self) -> Optional[float]:
        """获取请求耗时（秒）"""
        if self.start_time is None or self.end_time is None:
            return None
        return self.end_time - self.start_time

    def start_timing(self):
        """开始计时"""
        self.start_time = time.time()

    def response_timing(self):
        """响应开始时间"""
        self.response_time = time.time()

    def end_timing(self):
        """结束计时"""
        self.end_time = time.time()

    def get_attribute(self, key: str, default: Any = None) -> Any:
        """获取自定义属性"""
        return self.attributes.get(key, default)

    def set_attribute(self, key: str, value: Any):
        """设置自定义属性"""
        self.attributes[key] = value

    def has_attribute(self, key: str) -> bool:
        """检查是否存在自定义属性"""
        return key in self.attributes

    def remove_attribute(self, key: str) -> Any:
        """移除自定义属性"""
        return self.attributes.pop(key, None)

    def __str__(self) -> str:
        return (
            f"RequestContext(method={self.method}, service={self.service_name}, "
            f"path={self.path}, url={self.resolved_url}, "
            f"status={self.response.status if self.response else 'unknown'}, "
            f"duration={self.duration})"
        )

    def __repr__(self) -> str:
        return self.__str__()