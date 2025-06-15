import json
import os
from datetime import datetime

def load_json(filename):
    """JSONファイルを読み込む"""
    try:
        if not os.path.exists(filename):
            return []
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return []

def save_json(filename, data):
    """JSONファイルに保存する"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"JSON保存エラー: {e}")

def init_json_files():
    """JSONファイルを初期化する"""
    files = [
        'Userdata.json',
        'Posts.json', 
        'Comments.json',
        'Likes.json',
        'Tags.json',
        'Regions.json'
    ]
    
    for file in files:
        if not os.path.exists(file):
            save_json(file, [])
            print(f"{file} を作成しました")

def delete_comment_from_json(comment_id, user_id):
    """
    JSONファイルからコメントを完全削除する
    
    Args:
        comment_id (str): 削除するコメントのID
        user_id (str): 削除を要求するユーザーのID
    
    Returns:
        dict: 削除結果
    """
    try:
        comments = load_json('Comments.json')
        
        # 削除前のコメント数
        original_count = len(comments)
        
        # 削除対象のコメントを検索
        target_comment = None
        for comment in comments:
            if comment.get('id') == comment_id:
                target_comment = comment
                break
        
        if not target_comment:
            return {'success': False, 'message': 'コメントが見つかりません'}
        
        # 削除権限確認
        if target_comment.get('user_id') != user_id:
            return {'success': False, 'message': '削除権限がありません'}
        
        # コメントを削除（フィルタリング）
        filtered_comments = []
        for comment in comments:
            if comment.get('id') != comment_id:
                filtered_comments.append(comment)
        
        # JSONファイルに保存
        save_json('Comments.json', filtered_comments)
        
        # 削除確認
        updated_comments = load_json('Comments.json')
        deleted_successfully = len(updated_comments) == original_count - 1
        
        if deleted_successfully:
            return {
                'success': True,
                'message': 'コメントを削除しました',
                'deleted_comment_id': comment_id,
                'post_id': target_comment.get('post_id'),
                'original_count': original_count,
                'new_count': len(updated_comments)
            }
        else:
            return {'success': False, 'message': 'JSONファイルからの削除に失敗しました'}
            
    except Exception as e:
        return {'success': False, 'message': f'削除処理でエラーが発生しました: {str(e)}'}

def cleanup_orphaned_comments():
    """
    存在しない投稿に紐づいているコメントを削除する
    """
    try:
        comments = load_json('Comments.json')
        posts = load_json('Posts.json')
        
        # 存在する投稿IDのセット
        existing_post_ids = {post.get('id') for post in posts if post.get('id')}
        
        # 有効なコメントのみを残す
        valid_comments = [
            comment for comment in comments 
            if comment.get('post_id') in existing_post_ids
        ]
        
        if len(valid_comments) != len(comments):
            save_json('Comments.json', valid_comments)
            print(f"孤立したコメント {len(comments) - len(valid_comments)} 件を削除しました")
            
    except Exception as e:
        print(f"コメント整理エラー: {e}")

def generate_unique_id(prefix=""):
    """一意のIDを生成する"""
    import random
    import string
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    random_str = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
    return f"{prefix}{timestamp}_{random_str}"

def get_user_by_id(user_id):
    """ユーザーIDからユーザー情報を取得"""
    users = load_json('Userdata.json')
    for user in users:
        if user.get('id') == user_id:
            return user
    return None

def get_post_by_id(post_id):
    """投稿IDから投稿情報を取得"""
    posts = load_json('Posts.json')
    for post in posts:
        if post.get('id') == post_id:
            return post
    return None

def get_comments_by_post_id(post_id):
    """投稿IDに関連するコメントを取得"""
    comments = load_json('Comments.json')
    return [comment for comment in comments if comment.get('post_id') == post_id]

def get_likes_by_post_id(post_id):
    """投稿IDに関連するいいねを取得"""
    likes = load_json('Likes.json')
    return [like for like in likes if like.get('post_id') == post_id]