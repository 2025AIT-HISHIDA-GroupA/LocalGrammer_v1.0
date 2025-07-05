from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify, current_app
import uuid
import os
from datetime import datetime
from utils.json_utils import load_json, save_json
from utils.file_utils import save_uploaded_file, delete_file
from utils.location_utils import get_region_from_coordinates
from utils.exif_utils import extract_gps_from_multiple_images
from utils.validation import validate_comment, validate_tag, validate_region, validate_coordinates, sanitize_input
from config import REGIONS, TAGS

posts_bp = Blueprint('posts', __name__)

@posts_bp.route('/post', methods=['GET', 'POST'])
def post():
    """投稿作成ページ"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        tag = request.form.get('tag', '').strip()
        region = request.form.get('region', '').strip()
        
        # 入力値検証
        tag_valid, tag_error = validate_tag(tag)
        if not tag_valid:
            flash(tag_error, 'error')
            return render_template('post.html', regions=REGIONS, tags=TAGS)
        
        # 座標情報の取得
        latitude = request.form.get('latitude')
        longitude = request.form.get('longitude')
        
        # 座標検証
        coords_valid, coords_error = validate_coordinates(latitude, longitude)
        if not coords_valid:
            flash(coords_error, 'error')
            return render_template('post.html', regions=REGIONS, tags=TAGS)
        
        # 画像ファイルの処理
        uploaded_images = []
        uploaded_image_paths = []
        
        # 最大4枚まで処理
        for i in range(1, 5):  # image1, image2, image3, image4
            file_key = f'image{i}'
            if file_key in request.files:
                file = request.files[file_key]
                try:
                    filename = save_uploaded_file(file, current_app.config['UPLOAD_FOLDER'])
                    if filename:
                        uploaded_images.append(filename)
                        uploaded_image_paths.append(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                except Exception as e:
                    flash(f'画像{i}のアップロードに失敗しました: {str(e)}', 'error')
        
        # 座標が手動設定されていない場合、画像からGPS情報を抽出
        if not latitude or not longitude:
            if uploaded_image_paths:
                coordinates = extract_gps_from_multiple_images(uploaded_image_paths)
                if coordinates:
                    latitude, longitude = coordinates
        
        # 座標がある場合は自動で地域を判定
        if latitude and longitude:
            try:
                auto_region = get_region_from_coordinates(latitude, longitude)
                if not region:  # 地域が手動選択されていない場合は自動判定を使用
                    region = auto_region
            except (ValueError, TypeError):
                pass  # 座標が不正な場合は手動選択された地域を使用
        
        # 地域が設定されていない場合はエラー
        if not region:
            flash('地域を選択するか、位置情報を許可してください。', 'error')
            return render_template('post.html', regions=REGIONS, tags=TAGS)
        
        # 地域検証
        region_valid, region_error = validate_region(region)
        if not region_valid:
            flash(region_error, 'error')
            return render_template('post.html', regions=REGIONS, tags=TAGS)
        
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
        
        # 座標情報があれば追加
        if latitude and longitude:
            try:
                post_data['latitude'] = float(latitude)
                post_data['longitude'] = float(longitude)
            except (ValueError, TypeError):
                pass  # 座標が不正な場合は座標なしで保存
        
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
    
    post_id = request.form.get('post_id', '').strip()
    comment_text = request.form.get('comment_text', '').strip()
    
    # 入力値検証
    if not post_id:
        return jsonify({'success': False, 'message': '投稿IDが無効です'})
    
    comment_valid, comment_error = validate_comment(comment_text)
    if not comment_valid:
        return jsonify({'success': False, 'message': comment_error})
    
    # コメントをサニタイズ
    comment_text = sanitize_input(comment_text)
    
    comment_data = {
        'id': str(uuid.uuid4()),
        'post_id': post_id,
        'user_id': session['user_id'],
        'username': session['username'],
        'comment': comment_text,
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

@posts_bp.route('/post/<string:post_id>')
def post_detail(post_id):
    """
    投稿詳細ページ - ログイン不要
    
    URLパラメータ:
        - auth_token: 認証トークン（オプション）
    """
    # URLパラメータから認証トークンを取得
    auth_token = request.args.get('auth_token')
    
    # 認証トークンがある場合は自動的にログイン
    if auth_token and 'user_id' not in session:
        # temp_auth_tokensをインポート
        from routes.api import temp_auth_tokens
        
        if auth_token in temp_auth_tokens:
            token_data = temp_auth_tokens[auth_token]
            
            # トークンの有効期限をチェック
            if datetime.now() < token_data['expires_at']:
                session['user_id'] = token_data['user_id']
                session['username'] = token_data['username']
                
                # 使用済みトークンを削除
                del temp_auth_tokens[auth_token]
            else:
                # 期限切れトークンを削除
                del temp_auth_tokens[auth_token]
    
    posts = load_json('Posts.json')
    post = None
    
    for p in posts:
        if p['id'] == post_id:
            post = p
            break
    
    if not post:
        flash('投稿が見つかりません。', 'error')
        # ログインしていない場合は、ログインページにリダイレクト
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        return redirect(url_for('main.home'))
    
    # コメントとライク情報を取得
    comments = load_json('Comments.json')
    likes = load_json('Likes.json')
    
    post_comments = [c for c in comments if c['post_id'] == post_id]
    post_likes = likes.get(post_id, [])
    
    # ユーザーがログインしているかチェック
    is_logged_in = 'user_id' in session
    user_liked = False
    
    if is_logged_in:
        user_liked = session['user_id'] in post_likes
    
    # 投稿に詳細情報を追加
    post['comments'] = post_comments
    post['comment_count'] = len(post_comments)
    post['like_count'] = len(post_likes)
    post['user_liked'] = user_liked
    
    return render_template('post_detail.html', 
                         post=post, 
                         comments=post_comments,
                         likes=post_likes,
                         user_liked=user_liked,
                         is_logged_in=is_logged_in,
                         username=session.get('username', ''),
                         regions=REGIONS,
                         tags=TAGS)