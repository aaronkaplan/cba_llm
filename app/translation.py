"""Simple module to translate a string in a language to the reference language (english)"""


# from pydantic import BaseModel, Field
import os
import logging

import deepl

from langchain import hub
from langchain_openai import ChatOpenAI
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.output_parsers import JsonOutputParser

from langchain_anthropic import ChatAnthropic



class Translation(BaseModel):
    """Pydantic class to represent a translation result."""
    src_text: str = Field(description="The original text to translate")
    dst_text: str = Field(description="The translated text")
    src_language: str = Field(description="The original language of the text", required=False)
    dst_language: str = Field(description="The language the text was translated to", required=False)

    def __init__(self, data):
        super().__init__(**data)
        if 'src_language' not in data:
            self.src_language = "de"        # safe assumption
        if 'dst_language' not in data:
            self.dst_language = "en"        # safe assumption

    def __str__(self):
        return f"Translation(src_text='{self.src_text}', dst_text='{self.dst_text}', src_language='{self.src_language}', dst_language='{self.dst_language}')"

    def __repr__(self):
        return self.__str__()


def translate(src_text: str, dst_language: str = 'english', _src_language: str = None) -> str:
    """Translate a string to the reference language (english)

    Args:
      src_text -- the string to translate
      dst_language -- the destination language (default 'english')

    Returns:
      str -- the translated string
    """

    # first initialize the connectoin to  the llm
    if os.getenv('LLM_PROVIDER').lower() == 'openai':
        logging.info("Using OpenAI")
        model = ChatOpenAI(model='gpt-3.5-turbo', temperature=0)
        # model = model.with_structured_output(schema=Translation, method="json_mode")      # this is currently broken in langchain 0.1.13
    elif os.getenv('LLM_PROVIDER').lower() == 'anthropic':
        logging.info("Using Claude (Anthropic)")
        model = ChatAnthropic(model="claude-3-haiku-20240307", temperature=0)
    else:
        raise ValueError("Unknown LLM_PROVIDER")
    output_parser = JsonOutputParser(pydantic_object=Translation)
    # print(f"{output_parser.get_format_instructions()=}")
    # first get the input language
    # XXX detect the input language and set the input_language variable
    # ... here we could make another prompt which detect the input language
    # and then it might be safer to use the right language model. --> Later
    #   example: input_language = "spanish"
    # then we will also have to adjust the prompt again to contain {input_language}

    # nowfirst get the right prompt
    prompt = hub.pull("aaronkaplan/basic_translation")
    data = {"src_text": src_text, "dst_language": dst_language}

    # prompt = prompt.partial(format_instructions=output_parser.get_format_instructions())
    chain = prompt | model | output_parser

    # now use the llm with the prompt to translate the text
    result = chain.invoke(data)

    try:
        translation = Translation({'src_text': src_text,
                                   'dst_text': result['dst_text'],
                                   'src_language': result['src_language'],
                                   'dst_language': dst_language
                                   })
    except Exception as e:
        logging.error("Translation failed: %s" % str(e))
        logging.error("LLM result: %s" % result)
        raise e
    return translation.dst_text


def translate_via_deepl(src_text: str, dst_language: str = 'english', _src_language: str = None) -> str:
    """Translate a string to to the dst_language using DeepL

    Args:
      src_text -- the string to translate
      dst_language -- the destination language (default 'english')

    Returns:
      str -- the translated string
    """
    deepl_api_key = os.getenv("DEEPL_API_KEY", '')
    if not deepl_api_key:
        raise ValueError("DEEPL_API_KEY not set")

    try:
        translator = deepl.Translator(deepl_api_key)
        result = translator.translate_text(src_text, target_lang=dst_language)
        return result.text
    except Exception as e:
        logging.error("Translation failed: %s" % str(e))
        raise e


if __name__ == "__main__":
    print(translate("Esto es una prueba 1", dst_language="english"))
    print("Using DeepL...")
    print(translate_via_deepl("Esto es una prueba 2", dst_language="english"))
