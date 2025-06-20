from flask import Blueprint, request, session, jsonify, current_app
import uuid
import os
from datetime import datetime
from utils.json_utils import load_json, save_json
from utils.file_utils import save_uploaded_file, delete_file
from utils.location_utils import get_region_from_coordinates
from utils.exif_utils import extract_gps_from_multiple_images
from config import REGIONS, TAGS

api_bp = Blueprint('api', __name__)

# ==============================================
# ヘルパー関数（Helper Functions）
# ==============================================

def get_post_details(post, user_id):
    """
    ヘルパー関数: 投稿にコメントといいねの詳細を追加
    
    Args:
        post (dict): 投稿データ
        user_id (str): 現在のユーザーID
    
    Returns:
        dict: 詳細情報が追加された投稿データ
    """
    comments = load_json('Comments.json')
    likes = load_json('Likes.json')
    
    post_id = post['id']
    
    post_comments = [c for c in comments if c['post_id'] == post_id]
    post['comment_count'] = len(post_comments)
    post['comments'] = post_comments
    
    post_likes = likes.get(post_id, [])
    post['like_count'] = len(post_likes)
    post['user_liked'] = user_id in post_likes
    
    return post

# ==============================================
# 認証API（Authentication APIs）
# ==============================================

@api_bp.route('/register', methods=['POST'])
def api_register():
    """
    API: ユーザー登録
    
    Request Body:
        {
            "username": str,
            "password": str
        }
    
    Returns:
        JSON: 登録結果
    """
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': 'Request body must be JSON.'}), 400
        
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'success': False, 'message': 'Username and password are required.'}), 400

    users = load_json('Userdata.json')

    if any(user_data['username'] == username for user_data in users.values()):
        return jsonify({'success': False, 'message': 'Username already exists.'}), 409

    user_id = str(uuid.uuid4())
    users[user_id] = {
        'username': username,
        'password': password,
        'created_at': datetime.now().isoformat()
    }
    save_json('Userdata.json', users)

    # 初期プロフィール設定
    regions = load_json('Regions.json')
    regions[user_id] = {'region': '東海圏'}
    save_json('Regions.json', regions)

    tags = load_json('Tags.json')
    tags[user_id] = TAGS.copy()
    save_json('Tags.json', tags)

    return jsonify({'success': True, 'message': 'User registered successfully.'}), 201

@api_bp.route('/login', methods=['POST'])
def api_login():
    """
    API: ログイン
    
    Request Body:
        {
            "username": str,
            "password": str
        }
    
    Returns:
        JSON: ログイン結果とユーザー情報
    """
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': 'Request body must be JSON.'}), 400

    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'success': False, 'message': 'Username and password are required.'}), 400

    users = load_json('Userdata.json')
    for user_id, user_data in users.items():
        if user_data['username'] == username and user_data['password'] == password:
            session['user_id'] = user_id
            session['username'] = username
            return jsonify({
                'success': True,
                'message': 'Login successful.',
                'user': {
                    'user_id': user_id,
                    'username': username
                }
            })

    return jsonify({'success': False, 'message': 'Invalid credentials.'}), 401

@api_bp.route('/logout', methods=['POST'])
def api_logout():
    """
    API: ログアウト
    
    Returns:
        JSON: ログアウト結果
    """
    session.clear()
    return jsonify({'success': True, 'message': 'Logged out successfully.'})

@api_bp.route('/status', methods=['GET'])
def api_status():
    """
    API: ログイン状態確認
    
    Returns:
        JSON: ログイン状態とユーザー情報
    """
    if 'user_id' in session:
        return jsonify({
            'logged_in': True,
            'user': {
                'user_id': session['user_id'],
                'username': session['username']
            }
        })
    return jsonify({'logged_in': False})

# ==============================================
# 投稿API（Post APIs）
# ==============================================

@api_bp.route('/home_feed', methods=['GET'])
def api_home_feed():
    """
    API: ホームフィード取得（フィルタリング済み投稿）
    
    Returns:
        JSON: ユーザーの地域・タグ設定に基づいてフィルタリングされた投稿リスト
    """
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Authentication required.'}), 401

    user_id = session['user_id']
    regions = load_json('Regions.json')
    tags = load_json('Tags.json')
    user_region = regions.get(user_id, {})
    user_tags = tags.get(user_id, [])
    
    posts = load_json('Posts.json')
    filtered_posts = []
    
    for post in posts:
        region_match = post.get('region', {}).get('region') == user_region.get('region')
        tag_match = post.get('tag') in user_tags
        if region_match and tag_match:
            detailed_post = get_post_details(post.copy(), user_id)
            filtered_posts.append(detailed_post)

    return jsonify(filtered_posts)

@api_bp.route('/my_posts', methods=['GET'])
def api_my_posts():
    """
    API: 自分の投稿取得（日記機能）
    
    Returns:
        JSON: ログインユーザーの投稿リスト
    """
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Authentication required.'}), 401
    
    user_id = session['user_id']
    posts = load_json('Posts.json')
    user_posts = [post for post in posts if post['user_id'] == user_id]
    
    detailed_posts = [get_post_details(post.copy(), user_id) for post in user_posts]
    
    return jsonify(detailed_posts)

@api_bp.route('/posts', methods=['POST'])
def api_create_post():
    """
    API: 投稿作成
    
    Form Data:
        tag: str (required)
        region: str (optional, 自動判定される場合)
        latitude: float (optional)
        longitude: float (optional)
        image1-4: File (optional, 最大4枚)
    
    Returns:
        JSON: 投稿作成結果
    """
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Authentication required.'}), 401

    tag = request.form.get('tag')
    region = request.form.get('region')
    latitude = request.form.get('latitude')
    longitude = request.form.get('longitude')

    if not tag:
        return jsonify({'success': False, 'message': 'Tag is required.'}), 400

    # 画像ファイルの処理
    uploaded_images = []
    uploaded_image_paths = []
    
    for i in range(1, 5):
        file_key = f'image{i}'
        if file_key in request.files:
            file = request.files[file_key]
            try:
                filename = save_uploaded_file(file, current_app.config['UPLOAD_FOLDER'])
                if filename:
                    uploaded_images.append(filename)
                    uploaded_image_paths.append(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
            except Exception as e:
                return jsonify({'success': False, 'message': str(e)}), 400

    # 座標が手動設定されていない場合、画像からGPS情報を抽出
    if not latitude or not longitude:
        if uploaded_image_paths:
            coordinates = extract_gps_from_multiple_images(uploaded_image_paths)
            if coordinates:
                latitude, longitude = coordinates

    # 座標がある場合は自動で地域を判定
    if latitude and longitude and not region:
        try:
            region = get_region_from_coordinates(latitude, longitude)
        except (ValueError, TypeError):
            pass

    if not region:
        return jsonify({'success': False, 'message': 'Region is required or location permission needed.'}), 400

    post_data = {
        'id': str(uuid.uuid4()),
        'user_id': session['user_id'],
        'username': session['username'],
        'tag': tag,
        'region': {'region': region},
        'images': uploaded_images,
        'created_at': datetime.now().isoformat()
    }

    # 座標情報があれば追加
    if latitude and longitude:
        try:
            post_data['latitude'] = float(latitude)
            post_data['longitude'] = float(longitude)
        except (ValueError, TypeError):
            pass

    posts = load_json('Posts.json')
    posts.insert(0, post_data)
    save_json('Posts.json', posts)

    return jsonify({'success': True, 'message': 'Post created successfully.', 'post': post_data}), 201

@api_bp.route('/posts/<string:post_id>', methods=['DELETE'])
def api_delete_post(post_id):
    """
    API: 投稿削除
    
    Args:
        post_id (str): 削除する投稿のID
    
    Returns:
        JSON: 削除結果
    """
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Authentication required.'}), 401
    
    user_id = session['user_id']
    posts = load_json('Posts.json')
    post_to_delete = None
    post_index = -1
    
    for i, post in enumerate(posts):
        if post['id'] == post_id:
            post_to_delete = post
            post_index = i
            break
            
    if not post_to_delete:
        return jsonify({'success': False, 'message': 'Post not found.'}), 404
        
    if post_to_delete['user_id'] != user_id:
        return jsonify({'success': False, 'message': 'Permission denied.'}), 403

    # 関連画像ファイルを削除
    if 'images' in post_to_delete and post_to_delete['images']:
        for image_filename in post_to_delete['images']:
            delete_file(image_filename, current_app.config['UPLOAD_FOLDER'])

    # 投稿を削除
    posts.pop(post_index)
    save_json('Posts.json', posts)
    
    # 関連コメントを削除
    comments = load_json('Comments.json')
    comments = [c for c in comments if c['post_id'] != post_id]
    save_json('Comments.json', comments)
    
    # 関連いいねを削除
    likes = load_json('Likes.json')
    if post_id in likes:
        del likes[post_id]
        save_json('Likes.json', likes)
        
    return jsonify({'success': True, 'message': 'Post deleted successfully.'})

@api_bp.route('/liked_posts', methods=['GET'])
def api_liked_posts():
    """
    API: いいねした投稿一覧取得
    
    Returns:
        JSON: ユーザーがいいねした投稿リスト
    """
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Authentication required.'}), 401

    user_id = session['user_id']
    
    # いいねデータを取得
    likes = load_json('Likes.json')
    posts = load_json('Posts.json')
    
    # ユーザーがいいねした投稿IDを取得
    liked_post_ids = []
    for post_id, user_list in likes.items():
        if user_id in user_list:
            liked_post_ids.append(post_id)
    
    # いいねした投稿を取得
    liked_posts = []
    for post in posts:
        if post['id'] in liked_post_ids:
            detailed_post = get_post_details(post.copy(), user_id)
            liked_posts.append(detailed_post)
    
    # 作成日時でソート（新しい順）
    liked_posts.sort(key=lambda x: x['created_at'], reverse=True)
    
    return jsonify(liked_posts)

# ==============================================
# いいね・コメントAPI（Like & Comment APIs）
# ==============================================

@api_bp.route('/posts/<string:post_id>/like', methods=['POST'])
def api_toggle_like(post_id):
    """
    API: いいね切り替え
    
    Args:
        post_id (str): 投稿ID
    
    Returns:
        JSON: いいね状態とカウント
    """
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Authentication required'}), 401
    
    user_id = session['user_id']
    likes = load_json('Likes.json')
    
    if post_id not in likes:
        likes[post_id] = []
    
    if user_id in likes[post_id]:
        likes[post_id].remove(user_id)
        liked = False
    else:
        likes[post_id].append(user_id)
        liked = True
    
    save_json('Likes.json', likes)
    
    return jsonify({
        'success': True,
        'liked': liked,
        'like_count': len(likes[post_id])
    })

@api_bp.route('/posts/<string:post_id>/comments', methods=['POST'])
def api_add_comment(post_id):
    """
    API: コメント追加
    
    Args:
        post_id (str): 投稿ID
    
    Request Body:
        {
            "comment_text": str
        }
    
    Returns:
        JSON: 追加されたコメント情報
    """
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Authentication required'}), 401
    
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': 'Request body must be JSON.'}), 400
        
    comment_text = data.get('comment_text')

    if not comment_text:
        return jsonify({'success': False, 'message': 'Comment text is required'}), 400

    comment_data = {
        'id': str(uuid.uuid4()),
        'post_id': post_id,
        'user_id': session['user_id'],
        'username': session['username'],
        'comment': comment_text.strip(),
        'created_at': datetime.now().isoformat()
    }
    
    comments = load_json('Comments.json')
    comments.insert(0, comment_data)
    save_json('Comments.json', comments)
    
    return jsonify({
        'success': True, 
        'comment': comment_data,
        'message': 'Comment added successfully'
    }), 201

@api_bp.route('/comments/<string:comment_id>', methods=['DELETE'])
def api_delete_comment(comment_id):
    """
    API: コメント削除
    
    Args:
        comment_id (str): コメントID
    
    Returns:
        JSON: 削除結果
    """
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Authentication required'}), 401
    
    user_id = session['user_id']
    comments = load_json('Comments.json')
    
    # 削除対象のコメントを検索
    comment_to_delete = None
    comment_index = -1
    
    for i, comment in enumerate(comments):
        if comment['id'] == comment_id:
            comment_to_delete = comment
            comment_index = i
            break
    
    if not comment_to_delete:
        return jsonify({'success': False, 'message': 'Comment not found.'}), 404
    
    # 削除権限確認（コメント作成者のみ）
    if comment_to_delete['user_id'] != user_id:
        return jsonify({'success': False, 'message': 'Permission denied.'}), 403
    
    # コメントを削除
    comments.pop(comment_index)
    save_json('Comments.json', comments)
    
    return jsonify({'success': True, 'message': 'Comment deleted successfully.'})

# ==============================================
# プロフィールAPI（Profile APIs）
# ==============================================

@api_bp.route('/profile', methods=['GET', 'POST'])
def api_profile():
    """
    API: プロフィール取得・更新
    
    GET Returns:
        JSON: ユーザーのプロフィール情報（地域・タグ設定）
    
    POST Request Body:
        {
            "region": str (optional),
            "tags": list (optional)
        }
    
    POST Returns:
        JSON: 更新結果
    """
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Authentication required.'}), 401

    user_id = session['user_id']
    
    if request.method == 'POST':
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'Request body must be JSON.'}), 400
        
        # 地域設定の更新
        if 'region' in data:
            regions = load_json('Regions.json')
            regions[user_id] = {'region': data['region']}
            save_json('Regions.json', regions)
        
        # タグ設定の更新
        if 'tags' in data:
            tags = load_json('Tags.json')
            tags[user_id] = data['tags']
            save_json('Tags.json', tags)
            
        return jsonify({'success': True, 'message': 'Profile updated successfully.'})

    # GET: プロフィール情報取得
    regions = load_json('Regions.json')
    tags = load_json('Tags.json')
    
    current_region = regions.get(user_id, {'region': '東海圏'})
    current_tags = tags.get(user_id, TAGS.copy())
    
    return jsonify({
        'region': current_region['region'],
        'tags': current_tags,
    })

# ==============================================
# 静的データAPI（Static Data APIs）
# ==============================================

@api_bp.route('/static_data', methods=['GET'])
def api_static_data():
    """
    API: 静的データ取得（地域・タグ一覧）
    
    Returns:
        JSON: 利用可能な地域とタグのリスト
    """
    return jsonify({
        'regions': REGIONS,
        'tags': TAGS
    })

# ==============================================
# 位置情報API（Location APIs）
# ==============================================

@api_bp.route('/detect_region', methods=['POST'])
def api_detect_region():
    """
    API: 座標から地域を判定
    
    Request Body:
        {
            "latitude": float,
            "longitude": float
        }
    
    Returns:
        JSON: 判定された地域名
    """
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': 'Request body must be JSON.'}), 400
    
    latitude = data.get('latitude')
    longitude = data.get('longitude')
    
    if latitude is None or longitude is None:
        return jsonify({'success': False, 'message': 'Latitude and longitude are required.'}), 400
    
    try:
        region = get_region_from_coordinates(latitude, longitude)
        return jsonify({'success': True, 'region': region})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@api_bp.route('/extract_gps_from_images', methods=['POST'])
def api_extract_gps_from_images():
    """
    API: 複数画像からGPS情報を抽出（既存機能）
    
    Form Data:
        image1-4: File
    
    Returns:
        JSON: 抽出されたGPS座標
    """
    temp_paths = []
    try:
        # アップロードされた画像を一時的に保存
        for i in range(1, 5):
            file_key = f'image{i}'
            if file_key in request.files:
                file = request.files[file_key]
                if file and file.filename != '':
                    # 一時ファイルとして保存
                    temp_filename = f"temp_{uuid.uuid4()}_{file.filename}"
                    temp_path = os.path.join(current_app.config['UPLOAD_FOLDER'], temp_filename)
                    file.save(temp_path)
                    temp_paths.append(temp_path)
                    print(f"一時保存: {temp_path}")
        
        if not temp_paths:
            return jsonify({'success': False, 'message': 'No images uploaded'}), 400
        
        print(f"処理する画像数: {len(temp_paths)}")
        
        # GPS情報を抽出
        coordinates = extract_gps_from_multiple_images(temp_paths)
        
        if coordinates:
            latitude, longitude = coordinates
            print(f"GPS座標抽出成功: lat={latitude}, lon={longitude}")
            return jsonify({
                'success': True,
                'latitude': latitude,
                'longitude': longitude
            })
        else:
            print("GPS情報が見つかりませんでした")
            return jsonify({
                'success': False,
                'message': 'No GPS data found in images'
            })
            
    except Exception as e:
        print(f"GPS抽出エラー: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        # 一時ファイルのクリーンアップ
        for temp_path in temp_paths:
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                    print(f"一時ファイル削除: {temp_path}")
            except Exception as e:
                print(f"一時ファイル削除エラー: {e}")

@api_bp.route('/extract_gps_from_single_image', methods=['POST'])
def extract_gps_from_single_image():
    """
    API: 単一画像からGPS情報を抽出（Flutter向け新機能）
    
    Form Data:
        image: File
    
    Returns:
        JSON: 抽出されたGPS座標
    """
    try:
        if 'image' not in request.files:
            return jsonify({'success': False, 'message': '画像ファイルがありません'})
        
        image_file = request.files['image']
        if image_file.filename == '':
            return jsonify({'success': False, 'message': '画像が選択されていません'})
        
        # ファイル拡張子をチェック
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp', 'tiff'}
        file_extension = image_file.filename.lower().split('.')[-1]
        if file_extension not in allowed_extensions:
            return jsonify({'success': False, 'message': 'サポートされていないファイル形式です'})
        
        # 一時的にファイルを保存
        from datetime import datetime
        temp_filename = f"temp_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{image_file.filename}"
        temp_path = os.path.join(current_app.config['UPLOAD_FOLDER'], temp_filename)
        
        # アップロードフォルダが存在することを確認
        os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
        
        image_file.save(temp_path)
        print(f"一時ファイル保存: {temp_path}")
        
        try:
            # GPS情報を抽出
            from utils.exif_utils import extract_gps_from_image
            gps_data = extract_gps_from_image(temp_path)
            
            print(f"抽出されたGPS情報: {gps_data}")
            
            if gps_data and isinstance(gps_data, dict) and gps_data.get('latitude') and gps_data.get('longitude'):
                latitude = float(gps_data['latitude'])
                longitude = float(gps_data['longitude'])
                
                # 有効な座標範囲をチェック
                if -90 <= latitude <= 90 and -180 <= longitude <= 180:
                    return jsonify({
                        'success': True,
                        'latitude': latitude,
                        'longitude': longitude,
                        'message': 'GPS情報を取得しました'
                    })
                else:
                    return jsonify({
                        'success': False,
                        'message': '無効な座標データです'
                    })
            else:
                return jsonify({
                    'success': False,
                    'message': '画像にGPS情報が含まれていません'
                })
                
        finally:
            # 一時ファイルを削除
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                    print(f"一時ファイル削除: {temp_path}")
            except Exception as cleanup_error:
                print(f"一時ファイル削除エラー: {cleanup_error}")
            
    except Exception as e:
        print(f"GPS抽出エラー: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': 'GPS情報の抽出に失敗しました'
        })