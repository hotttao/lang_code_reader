import asyncio
import hydra
from omegaconf import DictConfig, OmegaConf
from lang_code_reader.config import get_config
from lang_code_reader.config import AppConfig
from lang_code_reader.biz.service.get_code_source import CodeSourceService


async def start_reader(cfg: DictConfig) -> None:


    code_source_service = CodeSourceService.new(cfg, "github", "https://github.com/langchain-ai/langgraph/")
    content = await code_source_service.read_file("Makefile")
    print(content)


if __name__ == "__main__":
    app_config = get_config()
    asyncio.run(start_reader(app_config))
