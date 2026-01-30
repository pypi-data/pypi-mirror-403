"""拦截器接口定义"""
from abc import ABC, abstractmethod

from .context import RequestContext


class IServiceInterceptor(ABC):
    """服务调用拦截器接口"""

    @abstractmethod
    async def before_request(self, context: RequestContext) -> None:
        """请求前置处理

        Args:
            context: 请求上下文
        """
        pass

    @abstractmethod
    async def after_response(self, context: RequestContext) -> None:
        """响应后置处理

        Args:
            context: 请求上下文
        """
        pass

    @abstractmethod
    async def handle_exception(self, context: RequestContext) -> None:
        """异常处理

        Args:
            context: 请求上下文
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """拦截器名称"""
        pass

    @property
    def order(self) -> int:
        """拦截器顺序，数值越小优先级越高"""
        return 0