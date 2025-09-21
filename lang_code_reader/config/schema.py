from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field


class GithubConfig(BaseModel):
    """GitHub配置"""
    token: str
    api_url: str = "https://api.github.com"
    timeout: int = 30
    max_retries: int = 3
    user_agent: Optional[str] = None


class PgsqlConfig(BaseModel):
    """PostgreSQL数据库配置"""
    host: str
    username: str
    password: str
    database: str
    port: int = 5432
    min_connections: int = 1
    max_connections: int = 10
    ssl_mode: Optional[str] = None


class RedisConfig(BaseModel):
    """Redis配置"""
    host: str
    port: int = 6379
    password: Optional[str] = None
    db: int = 0
    timeout: int = 5
    pool_size: int = 10
    ssl: bool = False


class ModelConfig(BaseModel):
    """模型配置"""
    name: str
    version: str
    api_key: Optional[str] = None
    endpoint: Optional[str] = None
    timeout: int = 60
    max_tokens: int = 4096
    temperature: float = 0.7
    parameters: Dict[str, Any] = Field(default_factory=dict)


class AppConfig(BaseModel):
    """应用程序总配置"""
    github: GithubConfig
    pgsql: PgsqlConfig
    redis: RedisConfig
    model: ModelConfig
    debug: bool = False
    log_level: str = "INFO"
    environment: str = "development"