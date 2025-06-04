from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import json
import uuid
import os
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# 許可される画像拡張子
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# アップロードフォルダを作成
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# JSONファイルの初期化
def init_json_files():
    # Userdata.json
    if not os.path.exists('Userdata.json'):
        with open('Userdata.json', 'w', encoding='utf-8') as f:
            json.dump({}, f, ensure_ascii=False, indent=2)
    
    # Regions.jsonの内容は初期状態で、県:愛知県,市町村:名古屋市を登録して。
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

init_json_files()

# 広域エリアリスト
REGIONS = [
    '東海圏',
    '首都圏', 
    '関西圏',
    '九州',
    '沖縄',
    '北海道',
    '東北',
    '中国・四国',
    '北陸・甲信越'
]

# タグリスト
TAGS = ['景色', '動物', 'スイーツ', '映え','料理', 'スポーツ']

def load_json(filename):
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
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

@app.route('/')
def index():
    # ログイン済みの場合はホームページにリダイレクト
    if 'user_id' in session:
        return redirect(url_for('home'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    # すでにログイン済みの場合はホームページにリダイレクト
    if 'user_id' in session:
        return redirect(url_for('home'))
        
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        users = load_json('Userdata.json')
        
        for user_id, user_data in users.items():
            if user_data['username'] == username and user_data['password'] == password:
                session['user_id'] = user_id
                session['username'] = username
                return redirect(url_for('home'))
        
        flash('Ops！何かがおかしいようです。', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        users = load_json('Userdata.json')
        
        # ユーザー名がすでに存在するか確認
        if any(user_data['username'] == username for user_data in users.values()):
            flash('すでに登録済みのIDです。別のIDを使用してください。', 'error')
            return render_template('register.html')
        
        user_id = str(uuid.uuid4())
        users[user_id] = {
            'username': username,
            'password': password,
            'created_at': datetime.now().isoformat()
        }
        
        save_json('Userdata.json', users)
        
        # 初期プロフィール設定
        regions = load_json('Regions.json')
        regions[user_id] = {
            'region': '東海圏'
        }
        save_json('Regions.json', regions)
        
        tags = load_json('Tags.json')
        tags[user_id] = TAGS.copy()
        save_json('Tags.json', tags)
        
        flash('ユーザ情報が登録されました', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/home')
def home():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    
    # ユーザーの地域とタグ設定を取得
    regions = load_json('Regions.json')
    tags = load_json('Tags.json')
    
    user_region = regions.get(user_id, {})
    user_tags = tags.get(user_id, [])
    
    # 投稿を取得してフィルタリング
    posts = load_json('Posts.json')
    filtered_posts = []
    
    print(f"Debug - User region: {user_region}")
    print(f"Debug - User tags: {user_tags}")
    
    for post in posts:
        print(f"Debug - Post region: {post.get('region', {})}")
        print(f"Debug - Post tag: {post.get('tag')}")
        
        # 地域とタグがマッチする投稿のみ表示
        region_match = post.get('region', {}).get('region') == user_region.get('region')
        tag_match = post.get('tag') in user_tags
        
        print(f"Debug - Region match: {region_match}, Tag match: {tag_match}")
        
        if region_match and tag_match:
            filtered_posts.append(post)
            print(f"Debug - Post added to filtered_posts")
    
    print(f"Debug - Total filtered posts: {len(filtered_posts)}")
    
    # コメントとグッド数を追加
    comments = load_json('Comments.json')
    likes = load_json('Likes.json')
    
    for post in filtered_posts:
        post_id = post['id']
        # コメント数を追加
        post_comments = [c for c in comments if c['post_id'] == post_id]
        post['comment_count'] = len(post_comments)
        post['comments'] = post_comments
        
        # グッド数とユーザーがグッドしたかを追加
        post_likes = likes.get(post_id, [])
        post['like_count'] = len(post_likes)
        post['user_liked'] = user_id in post_likes
    
    return render_template('home.html', posts=filtered_posts, username=session['username'])

@app.route('/post', methods=['GET', 'POST'])
def post():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
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
                if file and file.filename != '' and allowed_file(file.filename):
                    # ファイル名を安全にする
                    filename = secure_filename(file.filename)
                    # ユニークなファイル名を生成
                    unique_filename = f"{uuid.uuid4()}_{filename}"
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                    
                    try:
                        file.save(file_path)
                        uploaded_images.append(unique_filename)
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
        posts.append(post_data)
        save_json('Posts.json', posts)
        
        flash('ポストしました。', 'success')
        return redirect(url_for('home'))
    
    return render_template('post.html', regions=REGIONS, tags=TAGS)

@app.route('/diary')
def diary():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    posts = load_json('Posts.json')
    
    # 自分の投稿のみフィルタリング
    user_posts = [post for post in posts if post['user_id'] == user_id]
    
    # コメントとグッド数を追加
    comments = load_json('Comments.json')
    likes = load_json('Likes.json')
    
    for post in user_posts:
        post_id = post['id']
        # コメント数を追加
        post_comments = [c for c in comments if c['post_id'] == post_id]
        post['comment_count'] = len(post_comments)
        post['comments'] = post_comments
        
        # グッド数を追加
        post_likes = likes.get(post_id, [])
        post['like_count'] = len(post_likes)
        post['user_liked'] = user_id in post_likes
    
    return render_template('diary.html', posts=user_posts)

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    
    if request.method == 'POST':
        # 地域の更新
        if 'region' in request.form:
            region = request.form['region']
            regions = load_json('Regions.json')
            regions[user_id] = {
                'region': region
            }
            save_json('Regions.json', regions)
        
        # タグの更新
        selected_tags = request.form.getlist('tags')
        tags = load_json('Tags.json')
        tags[user_id] = selected_tags
        save_json('Tags.json', tags)
        
        flash('プロフィールが更新されました', 'success')
        return redirect(url_for('profile'))
    
    # 現在の設定を取得
    regions = load_json('Regions.json')
    tags = load_json('Tags.json')
    
    current_region = regions.get(user_id, {'region': '東海圏'})
    current_tags = tags.get(user_id, TAGS.copy())
    
    return render_template('profile.html', 
                         regions=REGIONS, 
                         all_tags=TAGS, 
                         current_region=current_region, 
                         current_tags=current_tags)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/debug')
def debug():
    """デバッグ用: JSONファイルの状態を確認"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    debug_info = {
        'users': load_json('Userdata.json'),
        'posts': load_json('Posts.json'),
        'comments': load_json('Comments.json'),
        'likes': load_json('Likes.json'),
        'regions': load_json('Regions.json'),
        'tags': load_json('Tags.json')
    }
    
    return jsonify(debug_info)

@app.route('/add_comment', methods=['POST'])
def add_comment():
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
    comments.append(comment_data)
    save_json('Comments.json', comments)
    
    return jsonify({
        'success': True, 
        'comment': comment_data,
        'message': 'コメントを追加しました'
    })

@app.route('/toggle_like', methods=['POST'])
def toggle_like():
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

if __name__ == '__main__':
    app.run(debug=True)