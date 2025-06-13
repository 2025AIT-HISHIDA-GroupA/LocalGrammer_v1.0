from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import uuid
from datetime import datetime
from utils.json_utils import load_json, save_json
from config import TAGS

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/')
def index():
    """ルートページ - ログイン済みの場合はホームページにリダイレクト"""
    if 'user_id' in session:
        return redirect(url_for('main.home'))
    return redirect(url_for('auth.login'))

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """ログインページ"""
    # すでにログイン済みの場合はホームページにリダイレクト
    if 'user_id' in session:
        return redirect(url_for('main.home'))
        
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        users = load_json('Userdata.json')
        
        for user_id, user_data in users.items():
            if user_data['username'] == username and user_data['password'] == password:
                session['user_id'] = user_id
                session['username'] = username
                return redirect(url_for('main.home'))
        
        flash('Ops！何かがおかしいようです。', 'error')
    
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """ユーザー登録ページ"""
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
        return redirect(url_for('auth.login'))
    
    return render_template('register.html')

@auth_bp.route('/logout')
def logout():
    """ログアウト"""
    session.clear()
    return redirect(url_for('auth.login'))