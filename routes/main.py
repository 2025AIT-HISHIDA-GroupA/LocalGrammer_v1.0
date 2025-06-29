from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from utils.json_utils import load_json, save_json
from config import REGIONS, TAGS

main_bp = Blueprint('main', __name__)

def get_post_details(post, user_id):
    """投稿にコメントといいねの詳細を追加するヘルパー関数"""
    comments = load_json('Comments.json')
    likes = load_json('Likes.json')
    
    post_id = post['id']
    
    # コメントを取得（最新順）
    post_comments = [c for c in comments if c['post_id'] == post_id]
    post_comments.sort(key=lambda x: x['created_at'], reverse=True)
    
    post['comment_count'] = len(post_comments)
    post['comments'] = post_comments
    
    # いいね情報を追加
    post_likes = likes.get(post_id, [])
    post['like_count'] = len(post_likes)
    post['user_liked'] = user_id in post_likes if user_id else False
    
    return post

@main_bp.route('/home')
def home():
    """ホームページ - フィルタリングされた投稿を表示"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
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
        region_match = post.get('region', {}).get('region') == user_region.get('region')
        tag_match = post.get('tag') in user_tags
        
        if region_match and tag_match:
            detailed_post = get_post_details(post, user_id)
            filtered_posts.append(detailed_post)
    
    return render_template('home.html', posts=filtered_posts, username=session['username'])

@main_bp.route('/diary')
def diary():
    """日記ページ - 自分の投稿のみ表示"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    user_id = session['user_id']
    posts = load_json('Posts.json')
    
    # 自分の投稿のみフィルタリング
    user_posts = [post for post in posts if post['user_id'] == user_id]
    
    # 投稿の詳細情報を追加
    detailed_posts = []
    for post in user_posts:
        detailed_post = get_post_details(post, user_id)
        detailed_posts.append(detailed_post)
    
    return render_template('diary.html', posts=detailed_posts)

@main_bp.route('/liked_posts')
def liked_posts():
    """いいねした投稿一覧ページ"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
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
            detailed_post = get_post_details(post, user_id)
            liked_posts.append(detailed_post)
    
    # 作成日時でソート（新しい順）
    liked_posts.sort(key=lambda x: x['created_at'], reverse=True)
    
    return render_template('liked_posts.html', posts=liked_posts, username=session['username'])

@main_bp.route('/profile', methods=['GET', 'POST'])
def profile():
    """プロフィール設定ページ"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
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
        return redirect(url_for('main.profile'))
    
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

@main_bp.route('/map/<region>')
def show_map(region):
    """地図表示ページ - ログイン不要"""
    posts = load_json('Posts.json')
    
    # デバッグ情報を出力
    print(f"=== 地図表示デバッグ情報 ===")
    print(f"要求された地域: {region}")
    print(f"全投稿数: {len(posts)}")
    
    # 地域に一致する投稿を検索
    region_posts = []
    for post in posts:
        post_region = post.get('region', {}).get('region')
        has_latitude = post.get('latitude') is not None
        has_longitude = post.get('longitude') is not None
        has_coords = has_latitude and has_longitude
        
        print(f"投稿ID: {post.get('id')}, 地域: {post_region}, 緯度: {post.get('latitude')}, 経度: {post.get('longitude')}, 座標有無: {has_coords}")
        
        if post_region == region:
            region_posts.append(post)
            print(f"  → 地域一致! 座標有無: {has_coords}")
    
    print(f"地域一致投稿数: {len(region_posts)}")
    coords_posts = [p for p in region_posts if p.get('latitude') is not None and p.get('longitude') is not None]
    print(f"座標付き投稿数: {len(coords_posts)}")
    print("=== デバッグ情報終了 ===")
    
    return render_template('map.html', region=region, posts=region_posts)

@main_bp.route('/debug')
def debug():
    """デバッグ用: JSONファイルの状態を確認"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    debug_info = {
        'users': load_json('Userdata.json'),
        'posts': load_json('Posts.json'),
        'comments': load_json('Comments.json'),
        'likes': load_json('Likes.json'),
        'regions': load_json('Regions.json'),
        'tags': load_json('Tags.json')
    }
    
    return jsonify(debug_info)

@main_bp.route('/delete_comment', methods=['POST'])
def delete_comment():
    """コメント削除エンドポイント"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'ログインが必要です'})
    
    comment_id = request.form.get('comment_id')
    post_id = request.form.get('post_id')
    user_id = session['user_id']
    
    if not comment_id:
        return jsonify({'success': False, 'message': 'コメントIDが無効です'})
    
    # ユーティリティ関数を使用
    from utils.json_utils import delete_comment_from_json
    result = delete_comment_from_json(comment_id, user_id)
    
    return jsonify(result)

@main_bp.route('/post/<string:post_id>')
def post_detail(post_id):
    """投稿詳細ページ - ログイン不要"""
    posts = load_json('Posts.json')
    post = None
    
    for p in posts:
        if p['id'] == post_id:
            post = p
            break
    
    if not post:
        flash('投稿が見つかりません', 'error')
        # ログインしていない場合は、ログインページにリダイレクト
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        return redirect(url_for('main.home'))
    
    # ログイン状態を確認
    user_id = session.get('user_id', None)
    is_logged_in = user_id is not None
    
    # 投稿詳細を取得
    detailed_post = get_post_details(post, user_id)
    
    return render_template('post_detail.html', 
                         post=detailed_post, 
                         username=session.get('username', ''),
                         is_logged_in=is_logged_in)