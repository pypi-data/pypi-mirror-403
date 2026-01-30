"""示例拦截器实现"""
import logging
import time

from .context import RequestContext
from .interface import IServiceInterceptor

logger = logging.getLogger(__name__)


class LoggingInterceptor(IServiceInterceptor):
    """日志拦截器"""

    def __init__(self, log_request: bool = True, log_response: bool = True):
        """初始化日志拦截器

        Args:
            log_request: 是否记录请求日志
            log_response: 是否记录响应日志
        """
        self.log_request = log_request
        self.log_response = log_response

    @property
    def name(self) -> str:
        return "LoggingInterceptor"

    async def before_request(self, context: RequestContext) -> None:
        """请求前记录日志"""
        if self.log_request:
            logger.info(
                f"→ {context.method} {context.service_name}{context.path} | "
                f"Headers: {context.kwargs.get('headers', {})} | "
                f"Params: {context.kwargs.get('params', {})}"
            )

    async def after_response(self, context: RequestContext) -> None:
        """响应后记录日志"""
        if self.log_response and context.response:
            logger.info(
                f"← {context.method} {context.service_name}{context.path} | "
                f"Resolved URL: {context.resolved_url} | "
                f"Status: {context.response.status} | "
                f"Duration: {context.duration:.3f}s | "
                f"Size: {len(str(context.result)) if context.result else 0} bytes"
            )

    async def handle_exception(self, context: RequestContext) -> None:
        """异常处理记录日志"""
        if context.exception:
            logger.error(
                f"✗ {context.method} {context.service_name}{context.path} | "
                f"Exception: {context.exception} | "
                f"Duration: {context.duration:.3f}s"
            )

    @property
    def order(self) -> int:
        return 99999

class AuthInterceptor(IServiceInterceptor):
    """认证拦截器"""

    def __init__(self, token: str, header_name: str = "Authorization", prefix: str = "Bearer "):
        """初始化认证拦截器

        Args:
            token: 认证令牌
            header_name: HTTP头名称
            prefix: 令牌前缀
        """
        self.token = token
        self.header_name = header_name
        self.prefix = prefix

    @property
    def name(self) -> str:
        return "AuthInterceptor"

    async def before_request(self, context: RequestContext) -> None:
        """请求前添加认证头"""
        if "headers" not in context.kwargs:
            context.kwargs["headers"] = {}

        context.kwargs["headers"][self.header_name] = f"{self.prefix}{self.token}"

    async def after_response(self, context: RequestContext) -> None:
        """响应后处理认证相关的响应"""
        if context.response and context.response.status == 401:
            logger.warning(f"Authentication failed for {context.service_name}{context.path}")

    async def handle_exception(self, context: RequestContext) -> None:
        """认证相关异常处理"""
        # 认证相关的异常不处理，让上层处理
        pass


class RetryInterceptor(IServiceInterceptor):
    """重试拦截器"""

    def __init__(
        self,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        retry_on_status: set = None
    ):
        """初始化重试拦截器

        Args:
            max_retries: 最大重试次数
            retry_delay: 重试延迟（秒）
            retry_on_status: 需要重试的状态码集合
        """
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.retry_on_status = retry_on_status or {500, 502, 503, 504}

    @property
    def name(self) -> str:
        return "RetryInterceptor"

    @property
    def order(self) -> int:
        return 1000  # 最后执行重试

    async def before_request(self, context: RequestContext) -> None:
        """初始化重试计数"""
        context.set_attribute("retry_count", 0)
        context.set_attribute("should_retry", True)

    async def after_response(self, context: RequestContext) -> None:
        """检查响应状态，决定是否重试"""
        if (context.response and
            context.response.status in self.retry_on_status and
            context.get_attribute("should_retry", False)):

            retry_count = context.get_attribute("retry_count", 0)
            if retry_count < self.max_retries:
                context.set_attribute("retry_count", retry_count + 1)
                logger.info(
                    f"Retrying request {context.method} {context.service_name}{context.path} "
                    f"(attempt {retry_count + 1}/{self.max_retries})"
                )

                # 延迟后重试
                await asyncio.sleep(self.retry_delay)
                # 这里需要在ServiceTemplate中实现重试逻辑
                # 当前实现只是记录，实际重试需要更复杂的机制
            else:
                logger.error(f"Max retries exceeded for {context.method} {context.service_name}{context.path}")

    async def handle_exception(self, context: RequestContext) -> None:
        """异常处理，某些异常也需要重试"""
        if isinstance(context.exception, (aiohttp.ClientError, ConnectionError, TimeoutError)):
            retry_count = context.get_attribute("retry_count", 0)
            if retry_count < self.max_retries and context.get_attribute("should_retry", False):
                context.set_attribute("retry_count", retry_count + 1)
                logger.info(
                    f"Retrying request due to exception {context.method} {context.service_name}{context.path} "
                    f"(attempt {retry_count + 1}/{self.max_retries})"
                )

                # 延迟后重试
                await asyncio.sleep(self.retry_delay)


class MetricsInterceptor(IServiceInterceptor):
    """指标拦截器"""

    def __init__(self):
        """初始化指标拦截器"""
        self.request_count = 0
        self.success_count = 0
        self.error_count = 0
        self.total_duration = 0

    @property
    def name(self) -> str:
        return "MetricsInterceptor"

    async def before_request(self, context: RequestContext) -> None:
        """记录请求开始"""
        self.request_count += 1
        context.set_attribute("metrics_start_time", time.time())

    async def after_response(self, context: RequestContext) -> None:
        """记录请求完成指标"""
        if context.response and 200 <= context.response.status < 400:
            self.success_count += 1
        else:
            self.error_count += 1

        start_time = context.get_attribute("metrics_start_time")
        if start_time and context.duration:
            self.total_duration += context.duration

        logger.info(
            f"Metrics - Total: {self.request_count}, "
            f"Success: {self.success_count}, "
            f"Error: {self.error_count}, "
            f"Avg Duration: {self.get_average_duration():.3f}s"
        )

    async def handle_exception(self, context: RequestContext) -> None:
        """记录异常指标"""
        self.error_count += 1
        start_time = context.get_attribute("metrics_start_time")
        if start_time and context.duration:
            self.total_duration += context.duration

    def get_average_duration(self) -> float:
        """获取平均耗时"""
        return self.total_duration / max(1, self.request_count)

    def get_success_rate(self) -> float:
        """获取成功率"""
        return self.success_count / max(1, self.request_count)


# 导入必要的模块用于RetryInterceptor
import aiohttp
import asyncio