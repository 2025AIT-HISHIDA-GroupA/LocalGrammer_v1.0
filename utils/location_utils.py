from config import REGION_BOUNDARIES

def detect_region_from_coordinates(latitude, longitude):
    """
    緯度・経度から地域を判定
    
    Args:
        latitude (float): 緯度
        longitude (float): 経度
    
    Returns:
        str or None: 検出された地域名、または None（どの地域にも該当しない場合）
    """
    try:
        print(f"座標から地域を判定中: 緯度={latitude}, 経度={longitude}")
        
        # 各地域の境界をチェック
        for region_name, boundaries in REGION_BOUNDARIES.items():
            lat_min, lat_max = boundaries['lat_range']
            lng_min, lng_max = boundaries['lng_range']
            
            # 座標が境界内にあるかチェック
            if (lat_min <= latitude <= lat_max and 
                lng_min <= longitude <= lng_max):
                print(f"地域判定成功: {region_name}")
                return region_name
        
        print("どの地域にも該当しませんでした")
        return None
        
    except Exception as e:
        print(f"地域判定エラー: {e}")
        return None

def get_region_info(latitude, longitude):
    """
    座標から地域情報と詳細を取得
    
    Returns:
        dict: 地域情報辞書
    """
    region = detect_region_from_coordinates(latitude, longitude)
    
    if region:
        return {
            'region': region,
            'detected': True,
            'confidence': 'high',  # 境界内なので高信頼度
            'coordinates': {
                'latitude': latitude,
                'longitude': longitude
            }
        }
    else:
        # どの地域にも該当しない場合、最も近い地域を計算
        closest_region = find_closest_region(latitude, longitude)
        return {
            'region': closest_region,
            'detected': False,
            'confidence': 'low',   # 推測なので低信頼度
            'coordinates': {
                'latitude': latitude,
                'longitude': longitude
            }
        }

def find_closest_region(latitude, longitude):
    """
    最も近い地域を距離で計算
    """
    try:
        from config import REGION_DEFAULT_COORDINATES
        import math
        
        min_distance = float('inf')
        closest_region = '首都圏'  # デフォルト
        
        for region_name, center_coords in REGION_DEFAULT_COORDINATES.items():
            center_lat, center_lng = center_coords
            
            # 簡易的な距離計算（ハーヴァサイン公式の簡略版）
            lat_diff = latitude - center_lat
            lng_diff = longitude - center_lng
            distance = math.sqrt(lat_diff**2 + lng_diff**2)
            
            if distance < min_distance:
                min_distance = distance
                closest_region = region_name
        
        print(f"最も近い地域: {closest_region} (距離: {min_distance:.3f})")
        return closest_region
        
    except Exception as e:
        print(f"最近地域計算エラー: {e}")
        return '首都圏'  # エラー時のデフォルト