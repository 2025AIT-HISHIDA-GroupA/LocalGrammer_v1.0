import os

class Config:
    SECRET_KEY = 'your-secret-key-here'
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here'
    UPLOAD_FOLDER = 'static/uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

# 許可される画像ファイル形式
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

# 地域リスト
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
TAGS = ['景色', '動物', 'スイーツ', '映え', 'モーニング','ランチ','ディナー', 'スポーツ']

# 地域ごとのデフォルト座標（中心点）
REGION_DEFAULT_COORDINATES = {
    '東海圏': [35.1803, 136.9066],       # 愛知県庁（名古屋）
    '首都圏': [35.6895, 139.6917],       # 東京駅
    '関西圏': [34.6937, 135.5023],       # 大阪駅
    '九州': [33.5902, 130.4017],         # 福岡市
    '沖縄': [26.2123, 127.6792],         # 那覇市
    '北海道': [43.0642, 141.3469],       # 札幌市
    '東北': [38.2682, 140.8694],         # 仙台市
    '中国・四国': [34.3963, 132.4596],   # 広島市
    '北陸・甲信越': [36.6513, 138.1812]  # 長野市
}

# 地域の境界定義（緯度・経度の範囲）
REGION_BOUNDARIES = {
    '首都圏': {
        'lat_range': (35.0, 36.5),    # 東京、神奈川、埼玉、千葉
        'lng_range': (138.5, 140.5)
    },
    '東海圏': {
        'lat_range': (34.0, 36.0),    # 愛知、岐阜、三重、静岡
        'lng_range': (136.0, 139.0)
    },
    '関西圏': {
        'lat_range': (33.8, 35.8),    # 大阪、京都、兵庫、奈良、滋賀、和歌山
        'lng_range': (134.0, 136.5)
    },
    '九州': {
        'lat_range': (31.0, 34.0),    # 福岡、佐賀、長崎、熊本、大分、宮崎、鹿児島
        'lng_range': (129.0, 132.0)
    },
    '沖縄': {
        'lat_range': (24.0, 27.0),    # 沖縄県
        'lng_range': (122.0, 131.0)
    },
    '北海道': {
        'lat_range': (41.0, 46.0),    # 北海道
        'lng_range': (139.0, 146.0)
    },
    '東北': {
        'lat_range': (37.0, 41.5),    # 青森、岩手、宮城、秋田、山形、福島
        'lng_range': (139.0, 142.0)
    },
    '中国・四国': {
        'lat_range': (33.0, 36.0),    # 鳥取、島根、岡山、広島、山口、徳島、香川、愛媛、高知
        'lng_range': (131.0, 135.0)
    },
    '北陸・甲信越': {
        'lat_range': (35.5, 38.5),   # 新潟、富山、石川、福井、山梨、長野
        'lng_range': (136.0, 140.0)
    }
}
