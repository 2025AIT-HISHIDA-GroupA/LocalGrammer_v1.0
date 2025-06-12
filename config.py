import os

class Config:
    SECRET_KEY = 'your-secret-key-here'
    UPLOAD_FOLDER = 'static/uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

# 許可される画像拡張子
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

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
TAGS = ['景色', '動物', 'スイーツ', '映え', '料理', 'スポーツ']