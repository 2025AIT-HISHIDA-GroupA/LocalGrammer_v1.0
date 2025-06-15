# パッケージ初期化ファイル
from .json_utils import (
    load_json,
    save_json,
    init_json_files,
    delete_comment_from_json,
    cleanup_orphaned_comments,
    generate_unique_id,
    get_user_by_id,
    get_post_by_id,
    get_comments_by_post_id,
    get_likes_by_post_id
)

__all__ = [
    'load_json',
    'save_json', 
    'init_json_files',
    'delete_comment_from_json',
    'cleanup_orphaned_comments',
    'generate_unique_id',
    'get_user_by_id',
    'get_post_by_id',
    'get_comments_by_post_id',
    'get_likes_by_post_id'
]