# Aio Service Caller

A lightweight, high-performance Python asynchronous service invocation framework that provides service registration, service discovery, load balancing, and declarative HTTP client capabilities.

---

## 1. Features

* 🔍 **Service Discovery**: Integrated with Nacos service governance, supporting automatic service registration and discovery.
* ⚖️ **Load Balancing**: Built-in strategies including round-robin, random, weighted random, and weighted round-robin.
* 🔌 **Interceptor Mechanism**: Similar to Spring’s interceptor design, supporting request-before, response-after, and exception handling phases.
* 🚀 **Asynchronous High Performance**: Based on `aiohttp`, supporting connection pooling for efficient HTTP calls.

---

## 2. Installation

```bash
pip install aio-service-caller[config]
```

> The `[config]` option automatically installs
> [`yamlpyconfig`](https://pypi.org/project/yamlpyconfig/).
> It is recommended to use `yamlpyconfig` to load configuration from local files (with environment variable expansion), and manage service registry, discovery, and invocation settings.

---

## 3. Quick Start

### 3.1. Add Configuration

Create or modify configuration files under a directory (e.g., `/config`) such as `application.yaml` or `application-{profile}.yaml`:

> For details about `yamlpyconfig`, see the [documentation](https://pypi.org/project/yamlpyconfig/).

```yaml
# Service caller configuration
service-caller:
  lb-type: round_robin      # Load balancing strategy: round_robin, random, weight_round_robin, weight_random
  connection-timeout: 6     # Connection timeout (seconds)
  read-timeout: 6           # Read timeout (seconds)
  connection-pool-size: 100 # aiohttp connection pool size

# Nacos configuration
app-registry:
  nacos:
    server-addr: "192.168.30.36:9090"
    namespace: "dev"
    cluster: "DEFAULT"
    group: "DEFAULT_GROUP"
    ip: "127.0.0.1"
    port: 9999
    app-name: "my-app"
    username: "nacos"
    password: "Y789uioJKL"
    weight: 1.0
```

---

### 3.2. Create ServiceManager and Invoke Other Services

`ServiceManager` serves two purposes:

1. **Register the current service into Nacos** according to the configuration.
2. **Call other services registered in the same Nacos namespace**, using `aiohttp` for the underlying HTTP requests.

```python
@pytest.mark.asyncio
async def test_get_service_instances_with_nacos(self):
    async with ConfigManager("./") as config_manager:
        # Create ServiceManager
        async with ServiceManager(
            config_manager=config_manager,
            interceptors=[LoggingInterceptor(), AuthInterceptor(token="123456"), MetricsInterceptor()]
        ) as manager:

            # Option 1: get the parsed business result
            result = await manager.get("other-app", "/hello")
            assert result == {"status": "OK"}

            # Option 2: get the raw aiohttp response
            async with manager.raw_get("other-app", "/hello") as response:
                assert response.status == 200
                result = await response.json()
                assert result == {"status": "OK"}
```

Each supported HTTP method provides two calling styles:

1. `manager.<method>(service_name, path, **kwargs)`
   → returns the processed business result
2. `manager.raw_<method>(service_name, path, **kwargs)`
   → returns the raw `aiohttp` response object

`kwargs` is passed directly to `aiohttp`, allowing you to set `headers`, `params`, `data`, `json`, `timeout`, etc.

---

### 3.3. Custom Interceptors

When invoking other services via `ServiceManager`, interceptors registered in the manager will be invoked automatically at appropriate stages.
You can implement custom interceptors by implementing the `IServiceInterceptor` interface.

```python
class IServiceInterceptor(ABC):
    """Service invocation interceptor interface"""

    @abstractmethod
    async def before_request(self, context: RequestContext) -> None:
        """Pre-processing before the request is sent"""
        pass

    @abstractmethod
    async def after_response(self, context: RequestContext) -> None:
        """Post-processing after the response is received"""
        pass

    @abstractmethod
    async def handle_exception(self, context: RequestContext) -> None:
        """Exception handling when the request fails"""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Interceptor name"""
        pass

    @property
    def order(self) -> int:
        """Execution order, smaller values indicate higher priority"""
        return 0
```

#### Notes on interceptor behavior:

1. **Duplicate interceptors with the same name are ignored** — only the first instance is kept.
2. Interceptors can be dynamically managed through:

   * `add_interceptor(interceptor)`
   * `remove_interceptor(name)`
   * `clear_interceptors()`

---

### 3.3.1. Interceptor `context` Parameter

The `context` parameter passed into interceptors is a `RequestContext` object containing all information about the current request.

#### **Attributes available in all stages (`before_request`, `after_response`, `handle_exception`):**

1. `method`: `str` — HTTP method (`GET`, `POST`, `PUT`, `DELETE`, etc.)
2. `service_name`: `str` — Name of the target service
3. `path`: `str` — Request path (e.g., `/api/user/info`)
4. `protocol`: `str` — Request protocol (`http` or `https`)
5. `kwargs`: `dict` — Request parameters (`headers`, `params`, `data`, `json`, ...)
6. `attributes`: `Dict[str, Any]` — Custom attribute storage

#### **Attributes available only in `after_response` and `handle_exception`:**

1. `resolved_url`: `Optional[str]` — Fully resolved URL after load balancing

2. `selected_instance`: `Optional[Any]` — Chosen service instance

3. `response`: `Optional[ClientResponse]` — aiohttp response object

4. `exception`: `Optional[Exception]` — Exception raised during execution

5. `result`: `Any` — Final processed result

6. `start_time`: `Optional[float]` — Start timestamp

7. `response_time`: `Optional[float]` — Time when response headers were received

8. `end_time`: `Optional[float]` — End timestamp

9. `duration`: `Optional[float]` — Total request duration

---

### 3.3.2. Interceptor Examples

#### Logging interceptor:

```python
class LoggingInterceptor(IServiceInterceptor):
    """Logging interceptor"""

    def __init__(self, log_request: bool = True, log_response: bool = True):
        self.log_request = log_request
        self.log_response = log_response

    @property
    def name(self) -> str:
        return "LoggingInterceptor"

    async def before_request(self, context: RequestContext) -> None:
        if self.log_request:
            logger.info(
                f"→ {context.method} {context.service_name}{context.path} | "
                f"Headers: {context.kwargs.get('headers', {})} | "
                f"Params: {context.kwargs.get('params', {})}"
            )

    async def after_response(self, context: RequestContext) -> None:
        if self.log_response and context.response:
            logger.info(
                f"← {context.method} {context.service_name}{context.path} | "
                f"Resolved URL: {context.resolved_url} | "
                f"Status: {context.response.status} | "
                f"Duration: {context.duration:.3f}s | "
                f"Size: {len(str(context.result)) if context.result else 0} bytes"
            )

    async def handle_exception(self, context: RequestContext) -> None:
        if context.exception:
            logger.error(
                f"✗ {context.method} {context.service_name}{context.path} | "
                f"Exception: {context.exception} | "
                f"Duration: {context.duration:.3f}s"
            )

    @property
    def order(self) -> int:
        return 99999
```

#### Authentication interceptor:

```python
class AuthInterceptor(IServiceInterceptor):
    """Authentication interceptor"""

    def __init__(self, token: str, header_name: str = "Authorization", prefix: str = "Bearer "):
        self.token = token
        self.header_name = header_name
        self.prefix = prefix

    @property
    def name(self) -> str:
        return "AuthInterceptor"

    async def before_request(self, context: RequestContext) -> None:
        if "headers" not in context.kwargs:
            context.kwargs["headers"] = {}

        context.kwargs["headers"][self.header_name] = f"{self.prefix}{self.token}"

    async def after_response(self, context: RequestContext) -> None:
        if context.response and context.response.status == 401:
            logger.warning(f"Authentication failed for {context.service_name}{context.path}")

    async def handle_exception(self, context: RequestContext) -> None:
        pass
```
