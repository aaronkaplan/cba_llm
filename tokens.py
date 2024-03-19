"""
A helper library for calculating the number of tokens in a text (string),
for different LLM providers and tokenization methods.
Also, this library provides helper functions for tokenizing a text (string)
"""

import sys
import re
import tiktoken
import voyageai


# Tokenization methods
def calc_tokens(text: str, method='tiktoken', model='gpt-3.5-turbo'):
    """
    Calculate the number of tokens in a text (string)
    :param text: a string
    :param method: a string, the tokenization method
    :return: an integer, the number of tokens
    """
    if not text:
        return 0
    if method == 'tiktoken':
        encoding = tiktoken.encoding_for_model(model)
        return len(encoding.encode(text))
    if method == 'anthropic':
        vo = voyageai.Client()
        return vo.count_tokens([text])
    if method == 'word':
        return len(re.findall(r'\b\w+\b', text))
    if method == 'char':
        return len(text)
    else:
        raise ValueError('Unknown tokenization method')


if __name__ == "__main__":
    with open(sys.argv[1], 'r', encoding='utf-8') as f:
        text = f.read()
        print(f"Tokens (toktoken): {calc_tokens(text, method='tiktoken', model='gpt-3.5-turbo')}")
        print(f"Tokens (anthropic): {calc_tokens(text, method='anthropic')}")
        print(f"Tokens (word): {calc_tokens(text, method='word')}")
        print(f"Tokens (char): {calc_tokens(text, method='char')}")
        # print(f"Tokens (unknown): {calc_tokens(text, method='unknown')}")
