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

init_json_files()

# 愛知県の市町村リスト
AICHI_CITIES = [
    '名古屋市', '一宮市', '瀬戸市', '春日井市', '犬山市', '江南市', '小牧市', '稲沢市', 
    '尾張旭市', '岩倉市', '豊明市', '日進市', '清須市', '北名古屋市', '長久手市', 
    '東郷町', '豊山町', '大口町', '扶桑町', '津島市', '愛西市', '弥富市', 'あま市', 
    '大治町', '蟹江町', '飛島村', '半田市', '常滑市', '東海市', '大府市', '知多市', 
    '阿久比町', '東浦町', '南知多町', '美浜町', '武豊町', '岡崎市', '碧南市', '刈谷市', 
    '豊田市', '安城市', '西尾市', '知立市', '高浜市', 'みよし市', '幸田町', '豊橋市', 
    '豊川市', '蒲郡市', '新城市', '田原市', '設楽町', '東栄町', '豊根村'
]

# タグリスト
TAGS = ['景色', '動物', 'スイーツ', '映え']

def load_json(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_json(filename, data):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
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
        
        user_id = str(uuid.uuid4())
        users = load_json('Userdata.json')
        
        users[user_id] = {
            'username': username,
            'password': password,
            'created_at': datetime.now().isoformat()
        }
        
        save_json('Userdata.json', users)
        
        # 初期プロフィール設定
        regions = load_json('Regions.json')
        regions[user_id] = {
            'prefecture': '愛知県',
            'city': '豊田市'
        }
        save_json('Regions.json', regions)
        
        tags = load_json('Tags.json')
        tags[user_id] = TAGS.copy()
        save_json('Tags.json', tags)
        
        flash('ユーザ情報が登録されました', 'success')
    
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
    
    for post in posts:
        # 地域とタグがマッチする投稿のみ表示
        if (post.get('region', {}).get('city') == user_region.get('city') and
            post.get('tag') in user_tags):
            filtered_posts.append(post)
    
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
        prefecture = request.form['prefecture']
        city = request.form['city']
        
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
                'prefecture': prefecture,
                'city': city
            },
            'images': uploaded_images,
            'created_at': datetime.now().isoformat()
        }
        
        posts = load_json('Posts.json')
        posts.append(post_data)
        save_json('Posts.json', posts)
        
        flash('ポストしました。', 'success')
        return redirect(url_for('home'))
    
    return render_template('post.html', cities=AICHI_CITIES, tags=TAGS)

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
        if 'city' in request.form:
            city = request.form['city']
            regions = load_json('Regions.json')
            regions[user_id] = {
                'prefecture': '愛知県',
                'city': city
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
    
    current_region = regions.get(user_id, {'prefecture': '愛知県', 'city': '豊田市'})
    current_tags = tags.get(user_id, TAGS.copy())
    
    return render_template('profile.html', 
                         cities=AICHI_CITIES, 
                         all_tags=TAGS, 
                         current_region=current_region, 
                         current_tags=current_tags)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

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