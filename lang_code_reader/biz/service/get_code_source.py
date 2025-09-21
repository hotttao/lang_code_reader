
from urllib.parse import urlparse

from lang_code_reader.config.schema import AppConfig
from lang_code_reader.internal.code_fs.github import GitHubClient
from lang_code_reader.internal.code_fs.github import CodeStorageClient

class CodeSourceService:
    def __init__(self, code_client: CodeStorageClient):
        self.code_client = code_client

    @classmethod
    def new(cls, conf: AppConfig, source: str, path: str, ref: str="main"):
        code_client = None
        if source == "github":
            parsed = urlparse(path)
            if parsed.netloc != "github.com":
                raise ValueError(f"Invalid github url: {path}")
            parts = parsed.path.strip("/").split("/")
            if len(parts) < 2:  # 至少有 owner/repo
                raise ValueError(f"Invalid github path: {path}")
            owner, repo = parts[:2]
            code_client = GitHubClient(
                owner=owner,
                repo=repo,
                token=conf.github.token,
                default_ref=ref,
        )
        else:
            raise ValueError(f"Unknown source: {source}")
        return cls(code_client)

    async def read_file(self, path: str) -> str:
        return await self.code_client.read_file(path)