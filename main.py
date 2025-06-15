from flask import Flask
import os
from config import Config
# 直接的なインポートに変更
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.json_utils import init_json_files
from routes.auth import auth_bp
from routes.posts import posts_bp
from routes.main import main_bp
from routes.api import api_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # セッション設定
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['SESSION_COOKIE_SECURE'] = False  # 開発環境用
    
    # アップロードフォルダを作成
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # JSONファイルの初期化
    init_json_files()
    
    # ブループリントの登録
    app.register_blueprint(auth_bp)
    app.register_blueprint(posts_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5002,host='0.0.0.0')
