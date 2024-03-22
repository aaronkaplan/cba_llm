"""Simple module to translate a string in a language to the reference language (english)"""


# from pydantic import BaseModel, Field

from langchain import hub
from langchain_openai import ChatOpenAI
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.output_parsers import JsonOutputParser

class Translation(BaseModel):
    original_text: str =  Field(description="The original text to translate")
    translated_text: str = Field(description="The translated text")
    # original_language: str = Field(description="The original language of the text")
    translated_language:  str = Field(description="The language the text was translated to")

    def __init__(self, data):
        super().__init__(**data)


def translate(original_text: str, output_language: str = 'english') -> str:
    """Translate a string to the reference language (english)

    Arguments:
    text -- the string to translate
    output_language -- the destination language (default 'english')

    Returns:
    str -- the translated string
    """


    # first initialize the connectoin to  the llm 
    model = ChatOpenAI(model='gpt-3.5-turbo', temperature=0)
    output_parser = JsonOutputParser(pydantic_object=Translation)

    # first get the input language
    # XXX detect the input language and set the input_language variable
    # ... here we could make another prompt which detect the input language
    # and then it might be safer to use the right language model. --> Later
    #   example: input_language = "spanish"
    # then we will also have to adjust the prompt again to contain {input_language} 

    # nowfirst get the right prompt
    prompt = hub.pull("aaronkaplan/basic_translation")
    prompt = prompt.partial(format_instructions=output_parser.get_format_instructions())
    chain = prompt | model | output_parser

    # now use the llm with the prompt to translate the text
    result = chain.invoke({"text": original_text, "output_language": output_language})

    translation = Translation({'original_text': original_text,
                               'translated_text': result['translated_text'], 
                               'translated_language': output_language})
    return translation.translated_text

