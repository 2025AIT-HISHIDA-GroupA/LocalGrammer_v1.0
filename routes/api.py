from flask import Blueprint, request, session, jsonify, current_app
import uuid
import os
from datetime import datetime
from utils.json_utils import load_json, save_json
from utils.file_utils import save_uploaded_file, delete_file
from config import REGIONS, TAGS

api_bp = Blueprint('api', __name__)

def get_post_details(post, user_id):
    """ヘルパー関数: 投稿にコメントといいねの詳細を追加"""
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

@api_bp.route('/register', methods=['POST'])
def api_register():
    """API: ユーザー登録"""
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

    regions = load_json('Regions.json')
    regions[user_id] = {'region': '東海圏'}
    save_json('Regions.json', regions)

    tags = load_json('Tags.json')
    tags[user_id] = TAGS.copy()
    save_json('Tags.json', tags)

    return jsonify({'success': True, 'message': 'User registered successfully.'}), 201

@api_bp.route('/login', methods=['POST'])
def api_login():
    """API: ログイン"""
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
    """API: ログアウト"""
    session.clear()
    return jsonify({'success': True, 'message': 'Logged out successfully.'})

@api_bp.route('/status')
def api_status():
    """API: ログイン状態確認"""
    if 'user_id' in session:
        return jsonify({
            'logged_in': True,
            'user': {
                'user_id': session['user_id'],
                'username': session['username']
            }
        })
    return jsonify({'logged_in': False})

@api_bp.route('/home_feed')
def api_home_feed():
    """API: ホームフィード取得"""
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

@api_bp.route('/my_posts')
def api_my_posts():
    """API: 自分の投稿取得"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Authentication required.'}), 401
    
    user_id = session['user_id']
    posts = load_json('Posts.json')
    user_posts = [post for post in posts if post['user_id'] == user_id]
    
    detailed_posts = [get_post_details(post.copy(), user_id) for post in user_posts]
    
    return jsonify(detailed_posts)

@api_bp.route('/posts', methods=['POST'])
def api_create_post():
    """API: 投稿作成"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Authentication required.'}), 401

    tag = request.form.get('tag')
    region = request.form.get('region')

    if not tag or not region:
        return jsonify({'success': False, 'message': 'Tag and region are required.'}), 400

    uploaded_images = []
    for i in range(1, 5):
        file_key = f'image{i}'
        if file_key in request.files:
            file = request.files[file_key]
            try:
                filename = save_uploaded_file(file, current_app.config['UPLOAD_FOLDER'])
                if filename:
                    uploaded_images.append(filename)
            except Exception as e:
                return jsonify({'success': False, 'message': str(e)}), 400

    post_data = {
        'id': str(uuid.uuid4()),
        'user_id': session['user_id'],
        'username': session['username'],
        'tag': tag,
        'region': {'region': region},
        'images': uploaded_images,
        'created_at': datetime.now().isoformat()
    }

    posts = load_json('Posts.json')
    posts.insert(0, post_data)
    save_json('Posts.json', posts)

    return jsonify({'success': True, 'message': 'Post created successfully.', 'post': post_data}), 201

@api_bp.route('/posts/<string:post_id>', methods=['DELETE'])
def api_delete_post(post_id):
    """API: 投稿削除"""
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

    if 'images' in post_to_delete and post_to_delete['images']:
        for image_filename in post_to_delete['images']:
            delete_file(image_filename, current_app.config['UPLOAD_FOLDER'])

    posts.pop(post_index)
    save_json('Posts.json', posts)
    
    comments = load_json('Comments.json')
    comments = [c for c in comments if c['post_id'] != post_id]
    save_json('Comments.json', comments)
    
    likes = load_json('Likes.json')
    if post_id in likes:
        del likes[post_id]
        save_json('Likes.json', likes)
        
    return jsonify({'success': True, 'message': 'Post deleted successfully.'})

@api_bp.route('/profile', methods=['GET', 'POST'])
def api_profile():
    """API: プロフィール取得・更新"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Authentication required.'}), 401

    user_id = session['user_id']
    
    if request.method == 'POST':
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'Request body must be JSON.'}), 400
        
        if 'region' in data:
            regions = load_json('Regions.json')
            regions[user_id] = {'region': data['region']}
            save_json('Regions.json', regions)
        
        if 'tags' in data:
            tags = load_json('Tags.json')
            tags[user_id] = data['tags']
            save_json('Tags.json', tags)
            
        return jsonify({'success': True, 'message': 'Profile updated successfully.'})

    regions = load_json('Regions.json')
    tags = load_json('Tags.json')
    
    current_region = regions.get(user_id, {'region': '東海圏'})
    current_tags = tags.get(user_id, TAGS.copy())
    
    return jsonify({
        'region': current_region['region'],
        'tags': current_tags,
    })

@api_bp.route('/static_data')
def api_static_data():
    """API: 静的データ取得（地域・タグ一覧）"""
    return jsonify({
        'regions': REGIONS,
        'tags': TAGS
    })

@api_bp.route('/posts/<string:post_id>/like', methods=['POST'])
def api_toggle_like(post_id):
    """API: いいね切り替え"""
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
    """API: コメント追加"""
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