from omegaconf import DictConfig, OmegaConf
from hydra import compose, initialize

from lang_code_reader.config.schema import (
    GithubConfig,
    PgsqlConfig,
    RedisConfig,
    ModelConfig,
    AppConfig,
)


from typing import Optional


# 全局配置实例
_CONFIG: Optional[AppConfig] = None


def get_config() -> AppConfig:
    """获取当前配置

    如果配置尚未加载，则抛出异常

    Returns:
        AppConfig: 应用配置对象
    """
    if _CONFIG is None:
        return load_config()
    return _CONFIG


def load_config():
    with initialize(version_base=None, config_path="."):
        cfg = compose(config_name="conf.yaml")
        cfg_dict  = OmegaConf.to_container(cfg, resolve=True)
        config = AppConfig.model_validate(cfg_dict)
        _CONFIG = config
    return _CONFIG


__all__ = [
    "load_config",
    "get_config",
    "GithubConfig",
    "PgsqlConfig",
    "RedisConfig",
    "ModelConfig",
    "AppConfig",
]
