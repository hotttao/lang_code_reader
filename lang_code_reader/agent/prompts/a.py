from pydantic import BaseModel, Field, RootModel
from typing import Literal

class EntryFileFound(BaseModel):
    decision: Literal["entry_file_found"]
    next_file: dict

class NeedMoreInfo(BaseModel):
    decision: Literal["need_more_info"]
    ask_user: str

class LLMResponse(RootModel):
    __root__: EntryFileFound | NeedMoreInfo = Field(discriminator="decision")

from langchain.output_parsers import PydanticOutputParser

parser = PydanticOutputParser(pydantic_object=LLMResponse)
print(parser.get_format_instructions())