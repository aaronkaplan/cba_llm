"""
A helper library for calculating the number of tokens in a text (string),
for different LLM providers and tokenization methods.
Also, this library provides helper functions for tokenizing a text (string)
"""

import os
import sys
import re
import tiktoken
import voyageai

import pandas as pd

from pprint import pprint


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


def fetch_texts(directory: str) -> list[str]:
    """
    Fetch texts from a directory
    :param directory: a string, the directory path
    :return: a list of strings, the texts
    """
    texts = []
    for filename in os.listdir(directory):
        print(f"Reading file: {filename}")
        if filename.endswith('.txt'):
            with open(os.path.join(directory, filename), 'r', encoding='utf-8') as f:
                texts.append(f.read())
    return texts

def calculate_tokens(directory: str, method='tiktoken', model='gpt-3.5-turbo') -> dict[str, int]:
    """
    Calculate the number of tokens in texts from a directory
    :param directory: a string, the directory path
    :param method: a string, the tokenization method
    :return: a dictionary, the number of tokens in each text
    """
    texts = fetch_texts(directory)
    tokens = {}
    for i, text in enumerate(texts):
        tokens[f'text_{i}'] = calc_tokens(text, method, model)
    return tokens


if __name__ == "__main__":
    token_stats = calculate_tokens(sys.argv[1], method='tiktoken', model='gpt-3.5-turbo')

    pprint(token_stats)
    df = pd.DataFrame(token_stats.items(), columns=['Text', 'Tokens'])
    print(df.describe())