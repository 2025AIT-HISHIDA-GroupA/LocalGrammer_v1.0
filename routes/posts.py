from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify, current_app
import uuid
import os
from datetime import datetime
from utils.json_utils import load_json, save_json
from utils.file_utils import save_uploaded_file, delete_file, allowed_file
from utils.image_utils import extract_coordinates_from_uploaded_images
from utils.location_utils import get_region_info
from config import REGIONS, TAGS, REGION_DEFAULT_COORDINATES
from werkzeug.utils import secure_filename

def get_region_auto_selection(latitude, longitude):
    """座標から地域自動選択情報を取得"""
    region_info = get_region_info(latitude, longitude)
    return {
        'suggested_region': region_info['region'],
        'auto_detected': region_info['detected'],
        'confidence': region_info['confidence']
    }

posts_bp = Blueprint('posts', __name__)

@posts_bp.route('/post', methods=['GET', 'POST'])
def post():
    """投稿作成ページ"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        tag = request.form['tag']
        region = request.form['region']
        
        # 手動設定された座標を取得
        manual_lat = request.form.get('manual_lat')
        manual_lng = request.form.get('manual_lng')
        
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
        
        # 位置情報の取得
        latitude = None
        longitude = None
        coordinate_source = None
        
        # 手動設定の座標が優先
        if manual_lat and manual_lng:
            try:
                latitude = float(manual_lat)
                longitude = float(manual_lng)
                coordinate_source = 'manual'
            except ValueError:
                flash('座標の形式が正しくありません', 'error')
                return render_template('post.html', regions=REGIONS, tags=TAGS, 
                                     region_coordinates=REGION_DEFAULT_COORDINATES)
        else:
            # 画像から位置情報を抽出
            if uploaded_images:
                coordinates = extract_coordinates_from_uploaded_images(
                    uploaded_images, current_app.config['UPLOAD_FOLDER']
                )
                if coordinates:
                    latitude, longitude = coordinates
                    coordinate_source = 'exif'
        
        # 位置情報が設定されていない場合はエラー
        if latitude is None or longitude is None:
            flash('位置情報が設定されていません。地図上でピンを設定するか、位置情報付きの画像をアップロードしてください。', 'error')
            return render_template('post.html', regions=REGIONS, tags=TAGS, 
                                 region_coordinates=REGION_DEFAULT_COORDINATES)
        
        # 投稿データを作成
        post_id = str(uuid.uuid4())
        post_data = {
            'id': post_id,
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
        
        # 座標情報を保存
        coordinates = load_json('Coordinates.json')
        coordinates[post_id] = {
            'latitude': latitude,
            'longitude': longitude,
            'source': coordinate_source,  # 'manual' または 'exif'
            'created_at': datetime.now().isoformat()
        }
        save_json('Coordinates.json', coordinates)
        
        flash('ポストしました。', 'success')
        return redirect(url_for('main.home'))
    
    return render_template('post.html', regions=REGIONS, tags=TAGS, 
                         region_coordinates=REGION_DEFAULT_COORDINATES)

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
    
    # 関連する座標情報を削除
    coordinates = load_json('Coordinates.json')
    if post_id in coordinates:
        del coordinates[post_id]
        save_json('Coordinates.json', coordinates)
    
    return jsonify({'success': True, 'message': '投稿を削除しました'})

@posts_bp.route('/check_image_coordinates', methods=['POST'])
def check_image_coordinates():
    """アップロードされた画像から位置情報を抽出するAPI"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'ログインが必要です'})
    
    if 'image' not in request.files:
        return jsonify({'success': False, 'message': '画像ファイルが必要です'})
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({'success': False, 'message': '画像ファイルが選択されていません'})
    
    if not allowed_file(file.filename):
        return jsonify({'success': False, 'message': '許可されていないファイル形式です'})
    
    temp_path = None
    try:
        # 一時的にファイルを保存して位置情報を抽出
        temp_filename = f"temp_{uuid.uuid4()}_{secure_filename(file.filename)}"
        temp_path = os.path.join(current_app.config['UPLOAD_FOLDER'], temp_filename)
        
        print(f"一時ファイル保存: {temp_path}")
        file.save(temp_path)
        
        # ファイルサイズとタイプを確認
        file_size = os.path.getsize(temp_path)
        print(f"ファイルサイズ: {file_size} bytes")
        
        # 位置情報を抽出
        from utils.image_utils import get_coordinates_from_image
        print("位置情報抽出を開始...")
        coordinates = get_coordinates_from_image(temp_path)
        print(f"抽出結果: {coordinates}")
        
        # 一時ファイルを削除
        os.remove(temp_path)
        temp_path = None
        
        if coordinates:
            latitude, longitude = coordinates
            return jsonify({
                'success': True,
                'has_coordinates': True,
                'latitude': latitude,
                'longitude': longitude,
                'message': f'画像から位置情報を検出しました (緯度: {latitude:.6f}, 経度: {longitude:.6f})',
                'region_info': get_region_auto_selection(latitude, longitude)
            })
        else:
            print("位置情報なし")
            return jsonify({
                'success': True,
                'has_coordinates': False,
                'message': '画像に位置情報が含まれていません'
            })
            
    except Exception as e:
        print(f"エラー発生: {e}")
        import traceback
        traceback.print_exc()
        
        # エラー時は一時ファイルを削除
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
        
        return jsonify({
            'success': False,
            'message': f'画像の処理中にエラーが発生しました: {str(e)}'
        })