"""Simple module to translate a string in a language to the reference language (english)"""



from langchain import hub


def translate(text: str, dest: str = 'en') -> str:
    """Translate a string to the reference language (english)

    Arguments:
    text -- the string to translate
    dest -- the destination language (default 'en')

    Returns:
    str -- the translated string
    """

    # first get the right prompt
    obj = hub.pull("patrickmosby/translator")

    print(obj)

    return "foo"
