from typing import Iterable
import typing
from src.utils.client import Client
from src.data.config import TESTING
from .config import *
import os
from typing import Union

def get_stop_words(client: Client) -> list:
    path = _get_path_to(STOP_WORDS, client)
    if os.path.exists(path):
        with open(path, 'r') as f:
            text = f.read()
            if text:
                return text.split('\n')
    return []

def _get_path_to(data_type: str, client: Client) -> str:
    path =  'tests/TestClientData' if TESTING else 'ClientsData/data'
    for i in ('', f'/{client.id}/', f'/{msg_categories[client.sending_mode]}'):
        path += i
        if not os.path.exists(path):
            os.mkdir(path)
    return path + f'/{data_type}'

def get_path_to_filter(client: Client) -> str:
    path =  _get_path_to(STOP_WORDS, client)
    if not os.path.exists(path):
        open(path, 'w').close()
    return path

def add_stop_words(client: Client, words: Union[str, Iterable]):
    path = _get_path_to(STOP_WORDS, client)
    file = None
    _words = []
    if not isinstance(words, Iterable):
        _words.append(words)
    else:
        _words = words
    if os.path.exists(path):
        file = open(path, 'r')
        current_words = file.read().split('\n')
        file.close()
        file = open(path, 'a')
        for w in _words:
            if w not in current_words:
                file.write('\n'+w)
    else:
        file = open(path, 'w')
        file.write('\n'.join(_words))
    file.close()

def delete_stop_word(client: Client, word: str):
    path = _get_path_to(STOP_WORDS, client)
    if not os.path.exists(path):
        raise ValueError("Client does not have any stop words")
    with open(path, 'r') as file:
        words = file.read().split('\n')  
    try:
        words.pop(words.index(word))
    except ValueError:
        raise ValueError(f'Client does not have the word "{word}"')
    words = '\n'.join(words)
    with open(path, 'w') as file:
        file.write(words)
    
def clear_filter(client: Client):
    path = _get_path_to(STOP_WORDS, client)
    if not os.path.exists(path):
        raise ValueError("Client does not have filter")
    file =  open(path, 'w')
    file.close()

def edit_bot_filter(
    filter: typing.Dict[str, typing.List[str]], words: typing.List[str], category: int, action: str):
    category = str(category)
    add = action == 'add'
    if category not in filter:
        filter[category] = words if add else []
    elif add:
        for w in words:
            if w not in filter[category]:
                filter[category].append(w)
    else: # delete
        for w in words:
            if w in filter[category].copy():
                filter[category].pop(filter[category].index(w))