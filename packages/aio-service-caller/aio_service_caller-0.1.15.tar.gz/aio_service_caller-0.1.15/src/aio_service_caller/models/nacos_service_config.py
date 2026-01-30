import logging
from typing import Optional, Any

from pydantic import BaseModel, Field
from typing import Self

from aio_service_caller.models import LoadBalancerType

logger = logging.getLogger(__name__)
class ServiceCallerConfig(BaseModel):
    """Service caller model."""
    lb_type: LoadBalancerType = Field(LoadBalancerType.ROUND_ROBIN, alias="lb-type", description="service caller load balancer type")
    connection_timeout: int = Field(6, alias="connection-timeout", description="service caller connection timeout")
    read_timeout: int = Field(6, alias="read-timeout", description="service caller read timeout")
    connection_pool_size: int = Field(100, alias="connection-pool-size", description="service caller connection pool size")

    @classmethod
    def load_service_caller_config(cls, config: dict[str, Any]) -> Optional[Self]:
        """Load Nacos configuration from a dict."""
        try:
            if "service-caller" in config:
                return ServiceCallerConfig.model_validate(config["service-caller"])
            return None
        except Exception as e:
            logger.error(f"Error loading service caller config: {e}")
            return None

class NacosAppConfig(BaseModel):
    """Nacos configuration model."""
    server_addr: str = Field(..., alias="server-addr", description="Nacos server address")
    namespace: Optional[str] = Field(None, alias="namespace", description="Nacos namespace")
    cluster: Optional[str] = Field(None, alias="cluster", description="Nacos cluster")
    group: Optional[str] = Field("DEFAULT_GROUP", alias="group", description="Nacos group")
    ip: str = Field(..., alias="ip", description="Nacos IP address")
    port: int = Field(..., alias="port", description="Nacos port")
    app_name: Optional[str] = Field(None, alias="app-name", description="Nacos application name")
    username: Optional[str] = Field(None, alias="username", description="Nacos username")
    password: Optional[str] = Field(None, alias="password", description="Nacos password")
    weight: float = Field(1.0, alias="weight", description="Nacos application weight")
    access_key: Optional[str] = Field(None, alias="access-key", description="Nacos access key")
    secret_key: Optional[str] = Field(None, alias="secret-key", description="Nacos secret key")

    @classmethod
    def load_nacos_config(cls, config: dict[str, Any]) -> Optional[Self]:
        """Load Nacos configuration from a dict."""
        try:
            if "app-registry" in config and "nacos" in config["app-registry"]:
                return NacosAppConfig.model_validate(config["app-registry"]["nacos"])
            return None
        except Exception as e:
            logger.error(f"Error loading service caller config: {e}")
            return None
