from .caspian_config import get_files_index
import os
import json

ROUTE_FILES_PATH = './settings/files-list.json'


def get_route_files():
    if os.path.exists(ROUTE_FILES_PATH):
        with open(ROUTE_FILES_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


def get_loading_files():
    idx = get_files_index()
    loading_content = ''

    for loading in idx.loadings:
        if os.path.exists(loading.file.lstrip('./')):
            with open(loading.file.lstrip('./'), 'r', encoding='utf-8') as f:
                content = f.read()
            loading_content += f'<div pp-loading-url="{loading.url_scope}">{content}</div>'

    return f'<div style="display: none;" id="loading-file-1B87E">{loading_content}</div>' if loading_content else ''
