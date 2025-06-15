"""
地域判定のためのユーティリティ関数
座標から地域を自動判定する機能
"""

def get_region_from_coordinates(latitude, longitude):
    """
    緯度経度から地域を判定する
    
    Args:
        latitude (float): 緯度
        longitude (float): 経度
    
    Returns:
        str: 地域名
    """
    lat = float(latitude)
    lon = float(longitude)
    
    print(f"地域判定: 緯度={lat}, 経度={lon}")
    
    # 各地域の境界を定義（より正確な境界）
    
    # 北海道（北海道本島と周辺諸島）
    if lat >= 41.3:
        print("判定結果: 北海道")
        return '北海道'
    
    # 沖縄（沖縄県全域）
    if lat <= 26.5:
        print("判定結果: 沖縄")
        return '沖縄'
    
    # 東北（青森、岩手、宮城、秋田、山形、福島）
    if lat >= 37.0 and lat < 41.3:
        print("判定結果: 東北")
        return '東北'
    
    # 九州（福岡、佐賀、長崎、熊本、大分、宮崎、鹿児島）
    if lat <= 34.0 and lon <= 132.0:
        print("判定結果: 九州")
        return '九州'
    
    # 中国・四国（鳥取、島根、岡山、広島、山口、徳島、香川、愛媛、高知）
    if lat <= 35.7 and lon <= 134.8:
        print("判定結果: 中国・四国")
        return '中国・四国'
    
    # 関西圏（大阪、京都、兵庫、奈良、和歌山、滋賀）
    if lat >= 33.8 and lat <= 35.8 and lon >= 134.8 and lon <= 136.2:
        print("判定結果: 関西圏")
        return '関西圏'
    
    # 東海圏（愛知、岐阜、三重、静岡）
    if lat >= 34.0 and lat <= 36.5 and lon >= 136.2 and lon <= 139.0:
        print("判定結果: 東海圏")
        return '東海圏'
    
    # 首都圏（東京、神奈川、埼玉、千葉、茨城、栃木、群馬）
    if lat >= 35.0 and lat <= 37.5 and lon >= 139.0 and lon <= 141.0:
        print("判定結果: 首都圏")
        return '首都圏'
    
    # 北陸・甲信越（新潟、富山、石川、福井、山梨、長野）
    if ((lat >= 35.5 and lat <= 38.5 and lon >= 136.0 and lon < 139.0) or  # 北陸
        (lat >= 35.0 and lat <= 36.5 and lon >= 138.0 and lon < 139.0)):   # 甲信越
        print("判定結果: 北陸・甲信越")
        return '北陸・甲信越'
    
    # デフォルト判定（最も近い地域を推定）
    print(f"境界外の座標: 緯度={lat}, 経度={lon}")
    
    # 経度による大まかな判定
    if lon < 135.0:
        if lat > 35.0:
            print("判定結果: 中国・四国 (デフォルト)")
            return '中国・四国'
        else:
            print("判定結果: 九州 (デフォルト)")
            return '九州'
    elif lon < 137.0:
        if lat > 35.5:
            print("判定結果: 北陸・甲信越 (デフォルト)")
            return '北陸・甲信越'
        else:
            print("判定結果: 関西圏 (デフォルト)")
            return '関西圏'
    elif lon < 139.0:
        print("判定結果: 東海圏 (デフォルト)")
        return '東海圏'
    else:
        print("判定結果: 首都圏 (デフォルト)")
        return '首都圏'


def is_coordinate_in_region(latitude, longitude, region_name):
    """
    指定した座標が指定した地域に含まれるかチェック
    
    Args:
        latitude (float): 緯度
        longitude (float): 経度
        region_name (str): 地域名
    
    Returns:
        bool: 地域に含まれる場合True
    """
    detected_region = get_region_from_coordinates(latitude, longitude)
    return detected_region == region_name


def debug_coordinate_bounds():
    """
    デバッグ用: 各地域の境界座標を表示
    """
    test_coordinates = [
        # 首都圏
        (35.6895, 139.6917, "東京駅"),
        (35.4437, 139.6380, "横浜"),
        (35.8617, 139.6455, "さいたま"),
        (35.6074, 140.1233, "千葉"),
        
        # 関西圏
        (34.6937, 135.5023, "大阪"),
        (35.0116, 135.7681, "京都"),
        (34.6901, 135.1956, "神戸"),
        
        # 東海圏
        (35.1803, 136.9066, "名古屋"),
        (34.9756, 138.3828, "静岡"),
        
        # 北陸・甲信越
        (36.5613, 136.6562, "金沢"),
        (36.6513, 138.1812, "長野"),
        (35.6642, 138.5681, "甲府"),
    ]
    
    for lat, lon, name in test_coordinates:
        region = get_region_from_coordinates(lat, lon)
        print(f"{name}: ({lat}, {lon}) -> {region}")


if __name__ == "__main__":
    # テスト実行
    debug_coordinate_bounds()