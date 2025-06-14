import json
import os
from config import TAGS

def init_json_files():
    """JSONファイルの初期化"""
    # Userdata.json
    if not os.path.exists('Userdata.json'):
        with open('Userdata.json', 'w', encoding='utf-8') as f:
            json.dump({}, f, ensure_ascii=False, indent=2)
    
    # Regions.json
    if not os.path.exists('Regions.json'):
        with open('Regions.json', 'w', encoding='utf-8') as f:
            json.dump({}, f, ensure_ascii=False, indent=2)
    
    # Tags.json
    if not os.path.exists('Tags.json'):
        with open('Tags.json', 'w', encoding='utf-8') as f:
            json.dump({}, f, ensure_ascii=False, indent=2)
    
    # Posts.json
    if not os.path.exists('Posts.json'):
        with open('Posts.json', 'w', encoding='utf-8') as f:
            json.dump([], f, ensure_ascii=False, indent=2)
    
    # Comments.json
    if not os.path.exists('Comments.json'):
        with open('Comments.json', 'w', encoding='utf-8') as f:
            json.dump([], f, ensure_ascii=False, indent=2)
    
    # Likes.json
    if not os.path.exists('Likes.json'):
        with open('Likes.json', 'w', encoding='utf-8') as f:
            json.dump({}, f, ensure_ascii=False, indent=2)
    
    # Coordinates.json (位置情報)
    if not os.path.exists('Coordinates.json'):
        with open('Coordinates.json', 'w', encoding='utf-8') as f:
            json.dump({}, f, ensure_ascii=False, indent=2)

def load_json(filename):
    """JSONファイルを読み込み"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # 空のファイルや不正なJSONの場合のデフォルト値
            if filename == 'Comments.json' and not isinstance(data, list):
                return []
            elif filename == 'Likes.json' and not isinstance(data, dict):
                return {}
            elif filename == 'Posts.json' and not isinstance(data, list):
                return []
            return data
    except (FileNotFoundError, json.JSONDecodeError):
        # ファイルが存在しないか、JSONが不正な場合のデフォルト値
        if filename.endswith('.json'):
            if 'Comments' in filename or 'Posts' in filename:
                return []
            else:
                return {}
        return {}

def save_json(filename, data):
    """JSONファイルに保存"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)