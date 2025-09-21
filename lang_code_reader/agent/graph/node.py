from typing import Literal, Annotated
from pydantic import BaseModel, Field

from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from lang_code_reader.agent.graph.types import State
from lang_code_reader.agent.prompts.template import load_prompt_template
from lang_code_reader.agent.graph.types import NextFile



class EntryFileFound(BaseModel):
    decision: str = Literal["entry_file_found"]
    next_file: NextFile

class NeedMoreInfo(BaseModel):
    decision: str = Literal["need_more_info"]
    ask_user: str = Field(description="你需要哪些额外信息的具体问题")


EntryFileResp = Annotated[
    EntryFileFound | NeedMoreInfo,
    Field(discriminator="decision")
]


def entry_file(state: State):
    """
    Node to handle file entry and analysis.
    """
    
    prompt_template = PromptTemplate.from_template(load_prompt_template("entry_file"), template_format="jinja2")
    # prompt = prompt_template.format(
    #     basic=state.basic,
    #     entry_file_resp=)
    parser = PydanticOutputParser(pydantic_object=EntryFileFound)
    print(parser.get_format_instructions())