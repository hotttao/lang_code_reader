# filename: storage_interface.py

from abc import ABC, abstractmethod
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator
import aiohttp

# 引入 gidgethub
from gidgethub import aiohttp as gh_aiohttp
from gidgethub import GraphQLException

# -------------------------------
# Pydantic 数据模型
# -------------------------------

class SearchOptions(BaseModel):
    extension: Optional[str] = Field(None, description="File extension filter, with leading dot, e.g. '.py'")
    max_results: int = Field(100, ge=1, description="Max number of results to return")
    include_content: bool = False
    search_in_content: bool = False

    @field_validator('extension')
    def extension_must_start_with_dot(cls, v):
        if v is not None and not v.startswith('.'):
            raise ValueError("extension must start with '.'")
        return v


class FileSearchResultModel(BaseModel):
    path: str
    name: str
    type: str  # "file" or "directory"
    size: Optional[int] = None
    content: Optional[str] = None
    sha: Optional[str] = None
    url: Optional[str] = None
    score: Optional[float] = None


class GitHubFileContentModel(BaseModel):
    type: str
    encoding: str
    content: str
    sha: str
    size: int
    name: str
    path: str
    url: str
    git_url: str
    html_url: str
    download_url: Optional[str] = None


# -------------------------------
# 接口定义
# -------------------------------

class CodeStorageClient(ABC):
    """
    接口：统一读文件／搜索文件／获取目录结构等
    """

    @abstractmethod
    async def read_file(self, path: str) -> str:
        """
        读某个文件的内容
        """
        pass

    @abstractmethod
    async def search_files(
        self, query: str, options: SearchOptions
    ) -> List[FileSearchResultModel]:
        """
        搜索文件名或内容
        """
        pass

    @abstractmethod
    async def get_directory_structure(
        self, path: str = ""
    ) -> List[FileSearchResultModel]:
        """
        列出某个目录（在 tree 或 contents API）下的结构
        """
        pass

# -------------------------------
# GitHub 客户端实现
# -------------------------------

class GitHubClient(CodeStorageClient):
    def __init__(self, owner: str, repo: str, token: Optional[str] = None, default_ref: str = "main", session: Optional[aiohttp.ClientSession] = None):
        self.owner = owner
        self.repo = repo
        self.token = token
        self.default_ref = default_ref
        self._session = session or aiohttp.ClientSession()
        self._gh = gh_aiohttp.GitHubAPI(self._session, f"{owner}/{repo}", oauth_token=token)

    async def read_file(self, path: str, ref: Optional[str] = None) -> str:
        """
        类似 readFromGithub，读某个文件内容；若不是 file 或找不到则抛错
        """
        ref = ref or self.default_ref
        # 使用 contents API: GET /repos/{owner}/{repo}/contents/{path}?ref={ref}
        # gidgethub 的 getitem 可以用来访问 REST endpoints
        endpoint = f"/repos/{self.owner}/{self.repo}/contents/{path}"
        try:
            # import base64 decoding
            data = await self._gh.getitem(endpoint)
        except GraphQLException:
            raise FileNotFoundError(f"File not found: {path} (ref: {ref})")
        # Map response to GitHubFileContentModel
        gh_file = GitHubFileContentModel(**data)
        if gh_file.type != "file":
            raise ValueError(f"Path {path} is not a file, got type {gh_file.type}")
        if gh_file.encoding != "base64":
            raise ValueError(f"Unsupported encoding: {gh_file.encoding}")
        import base64
        content_bytes = base64.b64decode(gh_file.content)
        content_str = content_bytes.decode('utf-8')
        return content_str

    async def search_files(self, query: str, options: SearchOptions) -> List[FileSearchResultModel]:
        """
        实现 searchFilesInGithub
        """
        results: List[FileSearchResultModel] = []
        opts = options

        if opts.search_in_content:
            # 用 GitHub Search API 搜内容
            # endpoint: GET /search/code?q={query}+repo:{owner}/{repo}+extension:...
            query_parts = [query, f"repo:{self.owner}/{self.repo}"]
            if opts.extension:
                query_parts.append(f"extension:{opts.extension.lstrip('.')}")
            q = " ".join(query_parts)
            resp = await self._gh.getitem("/search/code", params={"q": q, "per_page": opts.max_results})
            items = resp.get("items", [])
            for item in items:
                name = item.get("name")
                path = item.get("path")
                sha = item.get("sha")
                score = item.get("score")
                fsr = FileSearchResultModel(
                    path=path,
                    name=name,
                    type="file",
                    sha=sha,
                    url=item.get("url"),
                    score=score,
                )
                if opts.include_content:
                    try:
                        content = await self.read_file(path, ref=self.default_ref)
                        fsr.content = content
                    except Exception as e:
                        # 可以记录 warn
                        fsr.content = None
                results.append(fsr)
            # 不额外排序，因为 Search API 自带一定排序
            return results

        else:
            # 根据 repo tree 抓取所有文件名，过滤
            # endpoint: GET /repos/{owner}/{repo}/git/trees/{ref}?recursive=1
            resp = await self._gh.getitem(f"/repos/{self.owner}/{self.repo}/git/trees/{self.default_ref}", params={"recursive": "1"})
            tree = resp.get("tree", [])
            count = 0
            for item in tree:
                if item.get("type") != "blob":
                    continue
                path = item.get("path")
                if opts.extension and not path.endswith(opts.extension):
                    continue
                filename = path.split("/")[-1]
                query_lower = query.lower()
                if query_lower not in path.lower() and query_lower not in filename.lower():
                    continue
                fsr = FileSearchResultModel(
                    path=path,
                    name=filename,
                    type="file",
                    size=item.get("size"),
                    sha=item.get("sha"),
                    url=item.get("url"),
                    # 可以实现一个简单 score 函数
                    score=self._calculate_score(path, filename, query),
                )
                if opts.include_content:
                    try:
                        content = await self.read_file(path, ref=self.default_ref)
                        fsr.content = content
                    except Exception as e:
                        fsr.content = None
                results.append(fsr)
                count += 1
                if count >= opts.max_results:
                    break
            # 排序
            results.sort(key=lambda x: x.score or 0, reverse=True)
            return results

    async def get_directory_structure(self, path: str = "", ref: Optional[str] = None) -> List[FileSearchResultModel]:
        """
        实现 getDirectoryStructure
        """
        ref = ref or self.default_ref
        # contents API: GET /repos/{owner}/{repo}/contents/{path}?ref={ref}
        endpoint = f"/repos/{self.owner}/{self.repo}/contents/{path}"
        try:
            resp = await self._gh.getitem(endpoint, params={"ref": ref})
        except GraphQLException:
            raise FileNotFoundError(f"Directory or file not found: {path} (ref: {ref})")
        # resp 要么是 list（目录），要么单个文件 dict
        results: List[FileSearchResultModel] = []
        if isinstance(resp, list):
            for item in resp:
                name = item.get("name")
                item_type = item.get("type")  # "file" or "dir"
                size = item.get("size", None)
                sha = item.get("sha", None)
                url = item.get("url", None)
                fsr = FileSearchResultModel(
                    path=item.get("path"),
                    name=name,
                    type="file" if item_type == "file" else "directory",
                    size=size,
                    sha=sha,
                    url=url,
                )
                results.append(fsr)
        else:
            # 是单个文件
            name = resp.get("name")
            item_type = resp.get("type")
            size = resp.get("size", None)
            sha = resp.get("sha", None)
            url = resp.get("url", None)
            fsr = FileSearchResultModel(
                path=resp.get("path"),
                name=name,
                type="file" if item_type == "file" else "directory",
                size=size,
                sha=sha,
                url=url,
            )
            results.append(fsr)
        return results

    def _calculate_score(self, path: str, filename: str, query: str) -> float:
        # 类似你 JS 中的 calculateScore
        ql = query.lower()
        fnl = filename.lower()
        pl = path.lower()
        score = 0.0
        if fnl == ql:
            score += 100
        elif fnl.startswith(ql):
            score += 80
        elif ql in fnl:
            score += 60
        elif ql in pl:
            score += 40
        # 深度 bonus
        depth = path.count('/')
        score += max(0, 20 - depth)
        # 常见扩展名 bonus
        for ext in [".py", ".ts", ".js", ".md", ".json", ".tsx", ".jsx"]:
            if filename.endswith(ext):
                score += 5
                break
        return score

    async def close(self):
        await self._session.close()