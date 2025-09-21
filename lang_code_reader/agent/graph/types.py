from dataclasses import dataclass
from pydantic import BaseModel, Field
from typing import Optional, Literal, Union
from dataclasses import dataclass, field
from typing import Literal, Optional, Annotated
from langchain_core.messages import AnyMessage
from langgraph.graph import add_messages

# currentFile
@dataclass
class FileAnalysis:
    understanding: str

@dataclass
class CurrentFile:
    name: str
    analysis: Optional[FileAnalysis] = None


# nextFile
class NextFile(BaseModel):
    name: str = Field(description="匹配到的代码目录内的精确文件路径")
    reason: str = Field(description="选择这个文件的原因")


# userFeedback (四种情况联合类型)
@dataclass
class UserFeedbackAccept:
    action: Literal["accept"]
    reason: Optional[str] = None

@dataclass
class UserFeedbackReject:
    action: Literal["reject"]
    reason: str

@dataclass
class UserFeedbackRefine:
    action: Literal["refine"]
    userUnderstanding: str
    reason: Optional[str] = None
    nextFile: Optional[str] = None

@dataclass
class UserFeedbackFinish:
    action: Literal["finish"]

# Python 联合类型
UserFeedback = Union[
    UserFeedbackAccept,
    UserFeedbackReject,
    UserFeedbackRefine,
    UserFeedbackFinish,
]


FileStatus = Literal["pending", "ignored", "done"]

@dataclass
class FileItem:
    path: str
    status: FileStatus
    type: Literal["file", "directory"]
    understanding: Optional[str] = None  # 分析理解结果，可选

@dataclass
class HistoryEntry:
    filePath: str
    feedback_action: Literal["accept", "reject", "refine", "finish"]
    timestamp: int
    reason: Optional[str] = None


@dataclass
class Basic:
    repo_name: str
    main_goal: str
    files: list[FileItem]
    specific_areas: Optional[str] = None
    github_url: Optional[str] = None
    github_ref: Optional[str] = None
    ask_user: Optional[str] = None
    previous_wrong_path: Optional[str] = None

@dataclass
class State:
    messages: Annotated[list[AnyMessage], add_messages]
    basic: Basic

    history: list[HistoryEntry] = field(default_factory=list)

    current_file: Optional[CurrentFile] = None  # Current file being processed

    next_file: Optional[NextFile] = None  # Next file to process after current file

    user_feedback: Optional[UserFeedback] = None  # User feedback for the current file
    reduced_output: Optional[str] = None  # Reduced output of the current file analysis
    completed: bool = False  # Whether the flow has completed
    call_to_action: Optional[
        Literal["improve_basic_input", "user_feedback", "finish", "null"]
    ] = None  # Call to action for UI to determine what user interaction is needed

    last_heartbeat: Optional[int] = None  # Last heartbeat timestamp for flow execution lock



if __name__ == "__main__":
    basic = Basic(repo_name="test", main_goal="test", files=[])
    state = State(basic=basic)
    print(state)