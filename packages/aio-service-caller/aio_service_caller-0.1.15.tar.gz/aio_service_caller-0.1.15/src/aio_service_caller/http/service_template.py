"""异步服务调用模板"""
import logging
import asyncio
from contextlib import asynccontextmanager
from typing import Any, List, Optional
import aiohttp
from ..discovery.interface import IServiceDiscovery
from ..load_balancer.interface import ILoadBalancerStrategy
from ..interceptor.interface import IServiceInterceptor
from ..interceptor.context import RequestContext
from ..utils.rw_lock import RWLock

logger = logging.getLogger(__name__)

class AsyncServiceTemplate:
    """异步服务调用模板，整合服务发现、负载均衡和拦截器机制"""

    def __init__(
        self,
        discovery: IServiceDiscovery,
        lb_strategy: ILoadBalancerStrategy,
        interceptors: Optional[List[IServiceInterceptor]] = None,
        connection_timeout: int = 6,
        read_timeout: int = 6,
        connection_pool_size: int = 100
    ):
        """
        初始化异步服务调用模板

        Args:
            discovery: 服务发现实现
            lb_strategy: 负载均衡策略
            interceptors: 拦截器列表
            connection_timeout: 会话连接超时时间（秒）
            read_timeout：read timeout
            connection_pool_size: 连接池大小
        """
        self._discovery = discovery
        self._lb = lb_strategy
        self._interceptors_name_set = set()
        self._interceptors = sorted(interceptors or [], key=lambda x: x.order)
        self._interceptor_lock = RWLock()
        self._http_session: Optional[aiohttp.ClientSession] = None
        self._session_timeout = aiohttp.ClientTimeout(connect=connection_timeout, sock_read=read_timeout)
        self._connection_pool_size = connection_pool_size
        self._session_lock = asyncio.Lock()


    async def add_interceptor(self, interceptor: IServiceInterceptor) -> None:
        """动态添加拦截器"""
        if interceptor:
            async with self._interceptor_lock.w_locked():
                self.__add_interceptors([interceptor])

    async def add_interceptors(self, interceptors: list[IServiceInterceptor]) -> None:
        """动态添加拦截器"""
        if interceptors and len(interceptors) > 0:
            async with self._interceptor_lock.w_locked():
                self.__add_interceptors(interceptors)

    def __add_interceptors(self, interceptors: list[IServiceInterceptor]) -> None:
        """动态添加拦截器"""
        for interceptor in interceptors:
            if interceptor.name not in self._interceptors_name_set:
                self._interceptors_name_set.add(interceptor.name)
                self._interceptors.append(interceptor)
        self._interceptors.sort(key=lambda x: x.order)

    async def remove_interceptor(self, name: str) -> None:
        """按名称移除拦截器"""
        async with self._interceptor_lock.w_locked():
            if name and name in self._interceptors_name_set:
                self._interceptors = [
                    it for it in self._interceptors if it.name != name
                ]
                self._interceptors_name_set.remove(name)

    async def clear_interceptors(self) -> None:
        """清空所有拦截器"""
        async with self._interceptor_lock.w_locked():
            self._interceptors.clear()
            self._interceptors_name_set.clear()

    async def get_session(self) -> aiohttp.ClientSession:
        """获取或创建HTTP会话"""
        if self._http_session is None or self._http_session.closed:
            async with self._session_lock:
                if self._http_session is None or self._http_session.closed:
                    connector = aiohttp.TCPConnector(
                        limit=self._connection_pool_size,
                        limit_per_host=self._connection_pool_size // 4,
                        force_close=False,
                        enable_cleanup_closed=True
                    )
                    self._http_session = aiohttp.ClientSession(
                        connector=connector,
                        timeout=self._session_timeout
                    )
        return self._http_session

    async def request(
        self,
        method: str,
        service_name: str,
        path: str,
        protocol: str = "http",
        **kwargs
    ) -> Any:
        """
        发起HTTP请求

        Args:
            method: HTTP方法
            service_name: 服务名
            path: 请求路径
            protocol: http or https, default is http
            **kwargs: 请求参数 (headers, params, data, json等)

        Returns:
            响应结果

        Raises:
            Exception: 请求异常或拦截器处理后的异常
        """
        # 创建请求上下文
        context = RequestContext(method, service_name, path, protocol, **kwargs)

        try:
            async with self.__raw_request(context, **kwargs) as response:
                # 6. 读取响应内容
                content_type = response.headers.get('content-type', '').lower()
                if 'application/json' in content_type:
                    context.result = await response.json()
                elif 'text/' in content_type:
                    context.result = await response.text()
                else:
                    context.result = await response.read() # 建议把其它类型也读出来

            return context.result
        except Exception as e:
            raise

    def raw_request(
        self,
        method: str,
        service_name: str,
        path: str,
        protocol: str = "http",
        **kwargs
    ) -> Any:
        """
        发起HTTP请求

        Args:
            method: HTTP方法
            service_name: 服务名
            path: 请求路径
            protocol: http or https, default is http
            **kwargs: 请求参数 (headers, params, data, json等)

        Returns:
            响应结果

        Raises:
            Exception: 请求异常或拦截器处理后的异常
        """
        # 创建请求上下文
        context = RequestContext(method, service_name, path, protocol, **kwargs)
        return self.__raw_request(context, **kwargs)

    @asynccontextmanager
    async def __raw_request(self, context: RequestContext, **kwargs):
        """
        发起HTTP请求

        Args:
            context: 请求上下文
            **kwargs: 请求参数 (headers, params, data, json等)

        Returns:
            响应结果

        Raises:
            Exception: 请求异常或拦截器处理后的异常
        """
        try:
            await self._request_pre(context)

            # 5. 执行HTTP请求
            session = await self.get_session()
            async with session.request(
                method=context.method,
                url=context.resolved_url,
                **context.kwargs
            ) as response:
                context.response_timing()
                context.response = response
                yield response

        except Exception as e:
            context.exception = e
            # 7. 执行异常拦截器（逆序）
            await self._execute_exception_interceptors(context)
            logger.error(f"Request failed: {e}")
            raise
        finally:
            # 结束计时
            context.end_timing()
            # 8. 执行后置拦截器（逆序）
            await self._execute_after_interceptors(context)

    async def _request_pre(self, context):
        # 开始计时
        context.start_timing()
        # 1. 执行前置拦截器
        await self._execute_before_interceptors(context)
        # 2. 服务发现和负载均衡
        instances = await self._discovery.get_instances(context.service_name)
        if not instances:
            raise Exception(f"Service '{context.service_name}' unavailable. No healthy instances found.")
        # 3. 负载均衡选择实例
        chosen_instance = self._lb.choose(instances)
        if not chosen_instance:
            raise Exception(f"Failed to choose instance for service '{context.service_name}'")
        context.selected_instance = chosen_instance
        # 4. 解析真实URL
        base_url = f"{context.protocol}://{chosen_instance.ip}:{chosen_instance.port}"
        context.resolved_url = f"{base_url}{context.path}"

    async def get_interceptors(self) -> tuple:
        return tuple(await self.__interceptors_snapshot())

    async def __interceptors_snapshot(self) -> List[IServiceInterceptor]:
        async with self._interceptor_lock.r_locked():
            return list(self._interceptors)

    async def _execute_before_interceptors(self, context: RequestContext):
        """执行前置拦截器"""
        for interceptor in await self.__interceptors_snapshot():
            try:
                await interceptor.before_request(context)
            except Exception as e:
                logger.error(f"Interceptor '{interceptor.name}' before_request failed: {e}")
                # 前置拦截器失败不应该中断请求流程

    async def _execute_after_interceptors(self, context: RequestContext):
        """执行后置拦截器"""
        for interceptor in reversed(await self.__interceptors_snapshot()):
            try:
                await interceptor.after_response(context)
            except Exception as e:
                logger.error(f"Interceptor '{interceptor.name}' after_response failed: {e}")
                # 后置拦截器失败不应该中断请求流程

    async def _execute_exception_interceptors(self, context: RequestContext):
        """执行异常拦截器"""
        for interceptor in reversed(await self.__interceptors_snapshot()):
            try:
                await interceptor.handle_exception(context)
                # 如果异常被处理了（设置为None），则中断异常处理链
                if context.exception is None:
                    break
            except Exception as e:
                logger.error(f"Interceptor '{interceptor.name}' handle_exception failed: {e}")

    # 便捷方法
    async def get(self, service_name: str, path: str, **kwargs) -> Any:
        """GET请求"""
        return await self.request("GET", service_name, path, **kwargs)

    async def post(self, service_name: str, path: str, **kwargs) -> Any:
        """POST请求"""
        return await self.request("POST", service_name, path, **kwargs)

    async def put(self, service_name: str, path: str, **kwargs) -> Any:
        """PUT请求"""
        return await self.request("PUT", service_name, path, **kwargs)

    async def delete(self, service_name: str, path: str, **kwargs) -> Any:
        """DELETE请求"""
        return await self.request("DELETE", service_name, path, **kwargs)

    async def patch(self, service_name: str, path: str, **kwargs) -> Any:
        """PATCH请求"""
        return await self.request("PATCH", service_name, path, **kwargs)


    # 便捷方法
    def raw_get(self, service_name: str, path: str, **kwargs) -> Any:
        """GET请求"""
        return self.raw_request("GET", service_name, path, **kwargs)

    def raw_post(self, service_name: str, path: str, **kwargs) -> Any:
        """POST请求"""
        return self.raw_request("POST", service_name, path, **kwargs)

    def raw_put(self, service_name: str, path: str, **kwargs) -> Any:
        """PUT请求"""
        return self.raw_request("PUT", service_name, path, **kwargs)

    def raw_delete(self, service_name: str, path: str, **kwargs) -> Any:
        """DELETE请求"""
        return self.raw_request("DELETE", service_name, path, **kwargs)

    def raw_patch(self, service_name: str, path: str, **kwargs) -> Any:
        """PATCH请求"""
        return self.raw_request("PATCH", service_name, path, **kwargs)

    async def close(self):
        """关闭HTTP会话"""
        if self._http_session and not self._http_session.closed:
            await self._http_session.close()

    async def __aenter__(self):
        """异步上下文管理器入口"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close()