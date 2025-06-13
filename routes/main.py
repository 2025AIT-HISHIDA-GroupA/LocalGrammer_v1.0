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
    post['user_liked'] = user_id in post_likes
    
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
    """地図表示ページ"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    posts = load_json('Posts.json')
    region_posts = [
        post for post in posts
        if post.get('region') and post['region']['region'] == region
        and post.get('latitude') and post.get('longitude')
    ]
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