from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify, current_app
import uuid
import os
from datetime import datetime
from utils.json_utils import load_json, save_json
from utils.file_utils import save_uploaded_file, delete_file
from config import REGIONS, TAGS

posts_bp = Blueprint('posts', __name__)

@posts_bp.route('/post', methods=['GET', 'POST'])
def post():
    """投稿作成ページ"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        tag = request.form['tag']
        region = request.form['region']
        
        # 画像ファイルの処理
        uploaded_images = []
        
        # 最大4枚まで処理
        for i in range(1, 5):  # image1, image2, image3, image4
            file_key = f'image{i}'
            if file_key in request.files:
                file = request.files[file_key]
                try:
                    filename = save_uploaded_file(file, current_app.config['UPLOAD_FOLDER'])
                    if filename:
                        uploaded_images.append(filename)
                except Exception as e:
                    flash(f'画像{i}のアップロードに失敗しました: {str(e)}', 'error')
        
        # 投稿データを作成
        post_data = {
            'id': str(uuid.uuid4()),
            'user_id': session['user_id'],
            'username': session['username'],
            'tag': tag,
            'region': {
                'region': region
            },
            'images': uploaded_images,
            'created_at': datetime.now().isoformat()
        }
        
        posts = load_json('Posts.json')
        posts.insert(0, post_data)  # 最新の投稿を先頭に追加
        save_json('Posts.json', posts)
        
        flash('ポストしました。', 'success')
        return redirect(url_for('main.home'))
    
    return render_template('post.html', regions=REGIONS, tags=TAGS)

@posts_bp.route('/add_comment', methods=['POST'])
def add_comment():
    """コメント追加"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'ログインが必要です'})
    
    post_id = request.form.get('post_id')
    comment_text = request.form.get('comment_text')
    
    if not post_id or not comment_text:
        return jsonify({'success': False, 'message': 'コメントが空です'})
    
    comment_data = {
        'id': str(uuid.uuid4()),
        'post_id': post_id,
        'user_id': session['user_id'],
        'username': session['username'],
        'comment': comment_text.strip(),
        'created_at': datetime.now().isoformat()
    }
    
    comments = load_json('Comments.json')
    comments.insert(0, comment_data)  # 最新のコメントを先頭に追加
    save_json('Comments.json', comments)
    
    return jsonify({
        'success': True, 
        'comment': comment_data,
        'message': 'コメントを追加しました'
    })

@posts_bp.route('/toggle_like', methods=['POST'])
def toggle_like():
    """いいね切り替え"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'ログインが必要です'})
    
    post_id = request.form.get('post_id')
    user_id = session['user_id']
    
    if not post_id:
        return jsonify({'success': False, 'message': '投稿IDが無効です'})
    
    likes = load_json('Likes.json')
    
    if post_id not in likes:
        likes[post_id] = []
    
    if user_id in likes[post_id]:
        # いいねを取り消し
        likes[post_id].remove(user_id)
        liked = False
        action = 'removed'
    else:
        # いいねを追加
        likes[post_id].append(user_id)
        liked = True
        action = 'added'
    
    save_json('Likes.json', likes)
    
    return jsonify({
        'success': True,
        'liked': liked,
        'like_count': len(likes[post_id]),
        'action': action
    })

@posts_bp.route('/delete_post', methods=['POST'])
def delete_post():
    """投稿削除"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'ログインが必要です'})
    
    post_id = request.form.get('post_id')
    user_id = session['user_id']
    
    if not post_id:
        return jsonify({'success': False, 'message': '投稿IDが無効です'})
    
    # 投稿を取得
    posts = load_json('Posts.json')
    post_to_delete = None
    post_index = -1
    
    for i, post in enumerate(posts):
        if post['id'] == post_id:
            post_to_delete = post
            post_index = i
            break
    
    if not post_to_delete:
        return jsonify({'success': False, 'message': '投稿が見つかりません'})
    
    # 投稿者本人または管理者のみ削除可能
    if post_to_delete['user_id'] != user_id:
        return jsonify({'success': False, 'message': '削除権限がありません'})
    
    # 投稿に関連する画像ファイルを削除
    if 'images' in post_to_delete and post_to_delete['images']:
        for image_filename in post_to_delete['images']:
            delete_file(image_filename, current_app.config['UPLOAD_FOLDER'])
    
    # 投稿を削除
    posts.pop(post_index)
    save_json('Posts.json', posts)
    
    # 関連するコメントを削除
    comments = load_json('Comments.json')
    comments = [c for c in comments if c['post_id'] != post_id]
    save_json('Comments.json', comments)
    
    # 関連するいいねを削除
    likes = load_json('Likes.json')
    if post_id in likes:
        del likes[post_id]
        save_json('Likes.json', likes)
    
    return jsonify({'success': True, 'message': '投稿を削除しました'})