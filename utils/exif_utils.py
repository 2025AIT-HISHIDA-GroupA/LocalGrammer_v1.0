"""
画像のEXIFデータから座標を抽出するユーティリティ
複数の方法でGPS情報を取得
"""
import exifread
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import os

def extract_gps_from_image(image_path):
    """画像からGPS情報を抽出する"""
    try:
        print(f"=== GPS情報抽出開始: {image_path} ===")
        
        # まずPILで試行
        gps_data = extract_gps_with_pil(image_path)
        if gps_data:
            print(f"PIL でGPS情報を取得: {gps_data}")
            return gps_data
        
        # PILで取得できない場合はExifReadで試行
        gps_data = extract_gps_with_exifread(image_path)
        if gps_data:
            print(f"ExifRead でGPS情報を取得: {gps_data}")
            return gps_data
            
        print("GPS情報が見つかりませんでした")
        return None
        
    except Exception as e:
        print(f"GPS抽出エラー: {e}")
        return None

def extract_gps_from_multiple_images(image_paths):
    """複数画像からGPS情報を抽出する"""
    try:
        print(f"=== 複数画像からGPS情報抽出開始: {len(image_paths)}枚 ===")
        
        gps_results = []
        
        for i, image_path in enumerate(image_paths):
            if image_path and os.path.exists(image_path):
                print(f"画像 {i+1}/{len(image_paths)}: {image_path}")
                gps_data = extract_gps_from_image(image_path)
                
                if gps_data:
                    gps_results.append({
                        'image_path': image_path,
                        'image_index': i,
                        'latitude': gps_data['latitude'],
                        'longitude': gps_data['longitude']
                    })
                    print(f"画像 {i+1} からGPS情報を取得: {gps_data}")
                else:
                    print(f"画像 {i+1} にはGPS情報がありません")
            else:
                print(f"画像 {i+1} は存在しないかパスが無効です: {image_path}")
        
        if gps_results:
            # 最初に見つかったGPS情報を返す
            first_gps = gps_results[0]
            print(f"複数画像GPS抽出結果: {len(gps_results)}枚からGPS情報を取得、最初の画像の座標を使用")
            return {
                'latitude': first_gps['latitude'],
                'longitude': first_gps['longitude'],
                'source_image': first_gps['image_path'],
                'source_index': first_gps['image_index'],
                'total_gps_images': len(gps_results),
                'all_gps_data': gps_results
            }
        else:
            print("すべての画像でGPS情報が見つかりませんでした")
            return None
            
    except Exception as e:
        print(f"複数画像GPS抽出エラー: {e}")
        return None

def extract_gps_with_pil(image_path):
    """PILを使用してGPS情報を抽出"""
    try:
        print("=== PIL ライブラリで処理 ===")
        with Image.open(image_path) as image:
            exifdata = image.getexif()
            
            if not exifdata:
                print("EXIF データが見つかりません")
                return None
            
            # GPS情報を探す
            for tag_id in exifdata:
                tag = TAGS.get(tag_id, tag_id)
                if tag == "GPSInfo":
                    gps_data = exifdata[tag_id]
                    print(f"PIL GPS データ: {gps_data}")
                    
                    if gps_data:
                        return parse_gps_data_pil(gps_data)
            
            print("GPS情報が見つかりません（PIL）")
            return None
            
    except Exception as e:
        print(f"PIL GPS抽出エラー: {e}")
        return None

def extract_gps_with_exifread(image_path):
    """ExifReadを使用してGPS情報を抽出"""
    try:
        print("=== ExifRead ライブラリで処理 ===")
        with open(image_path, 'rb') as f:
            tags = exifread.process_file(f)
            
        print(f"ExifRead で読み取ったタグ数: {len(tags)}")
        
        # GPS関連タグを抽出
        gps_tags = [tag for tag in tags.keys() if tag.startswith('GPS')]
        print(f"GPS関連タグ: {gps_tags}")
        
        if not gps_tags:
            print("GPS関連タグが見つかりません")
            return None
        
        # 必要なGPSタグを取得
        gps_latitude = tags.get('GPS GPSLatitude')
        gps_longitude = tags.get('GPS GPSLongitude')
        gps_latitude_ref = tags.get('GPS GPSLatitudeRef')
        gps_longitude_ref = tags.get('GPS GPSLongitudeRef')
        
        print(f"ExifRead GPSLatitude: {gps_latitude}")
        print(f"ExifRead GPSLongitude: {gps_longitude}")
        print(f"ExifRead GPSLatitudeRef: {gps_latitude_ref}")
        print(f"ExifRead GPSLongitudeRef: {gps_longitude_ref}")
        
        if gps_latitude and gps_longitude and gps_latitude_ref and gps_longitude_ref:
            return parse_gps_data_exifread(gps_latitude, gps_longitude, gps_latitude_ref, gps_longitude_ref)
        
        print("必要なGPS情報が不足しています")
        return None
        
    except Exception as e:
        print(f"ExifRead GPS抽出エラー: {e}")
        return None

def parse_gps_data_pil(gps_data):
    """PILのGPSデータを解析"""
    try:
        print(f"PILのGPSデータを解析: {gps_data}")
        
        # GPS座標を取得
        lat_ref = gps_data.get(1)  # GPSLatitudeRef
        lat = gps_data.get(2)      # GPSLatitude
        lon_ref = gps_data.get(3)  # GPSLongitudeRef  
        lon = gps_data.get(4)      # GPSLongitude
        
        if lat and lon and lat_ref and lon_ref:
            # 度分秒から度に変換
            latitude = convert_to_degrees(lat)
            longitude = convert_to_degrees(lon)
            
            # 南緯・西経の場合は負の値にする
            if lat_ref == 'S':
                latitude = -latitude
            if lon_ref == 'W':
                longitude = -longitude
            
            print(f"PIL 変換結果: lat={latitude}, lon={longitude}")
            return {
                'latitude': latitude,
                'longitude': longitude
            }
        
        return None
        
    except Exception as e:
        print(f"PIL GPSデータ解析エラー: {e}")
        return None

def parse_gps_data_exifread(gps_latitude, gps_longitude, gps_latitude_ref, gps_longitude_ref):
    """ExifReadのGPSデータを解析"""
    try:
        print("ExifReadのGPSデータを解析")
        
        # ExifReadの値を数値に変換
        lat_values = [float(val.num) / float(val.den) for val in gps_latitude.values]
        lon_values = [float(val.num) / float(val.den) for val in gps_longitude.values]
        
        print(f"緯度の値: {lat_values}")
        print(f"経度の値: {lon_values}")
        
        # 度分秒を度に変換
        latitude = lat_values[0] + lat_values[1] / 60 + lat_values[2] / 3600
        longitude = lon_values[0] + lon_values[1] / 60 + lon_values[2] / 3600
        
        # 方向を考慮
        lat_ref_str = str(gps_latitude_ref).strip()
        lon_ref_str = str(gps_longitude_ref).strip()
        
        print(f"緯度方向: {lat_ref_str}, 経度方向: {lon_ref_str}")
        
        if lat_ref_str == 'S':
            latitude = -latitude
        if lon_ref_str == 'W':
            longitude = -longitude
        
        print(f"ExifRead 最終結果: lat={latitude}, lon={longitude}")
        
        return {
            'latitude': latitude,
            'longitude': longitude
        }
        
    except Exception as e:
        print(f"ExifRead GPSデータ解析エラー: {e}")
        return None

def convert_to_degrees(value):
    """度分秒を度に変換"""
    try:
        if isinstance(value, (list, tuple)) and len(value) >= 3:
            # 度分秒の場合
            degrees = float(value[0])
            minutes = float(value[1])
            seconds = float(value[2])
            return degrees + minutes / 60 + seconds / 3600
        elif isinstance(value, (int, float)):
            # 既に度の場合
            return float(value)
        else:
            print(f"未対応の座標形式: {value}, タイプ: {type(value)}")
            return 0.0
    except Exception as e:
        print(f"座標変換エラー: {e}")
        return 0.0

def extract_creation_date(image_path):
    """画像の撮影日時を抽出"""
    try:
        with Image.open(image_path) as image:
            exifdata = image.getexif()
            
            # 撮影日時を取得
            for tag_id in exifdata:
                tag = TAGS.get(tag_id, tag_id)
                if tag in ["DateTime", "DateTimeOriginal", "DateTimeDigitized"]:
                    return str(exifdata[tag_id])
        
        return None
        
    except Exception as e:
        print(f"撮影日時抽出エラー: {e}")
        return None

def get_image_info(image_path):
    """画像の詳細情報を取得"""
    try:
        info = {
            'gps': extract_gps_from_image(image_path),
            'creation_date': extract_creation_date(image_path),
            'file_size': os.path.getsize(image_path),
            'file_name': os.path.basename(image_path)
        }
        
        with Image.open(image_path) as image:
            info['dimensions'] = image.size
            info['format'] = image.format
        
        return info
        
    except Exception as e:
        print(f"画像情報取得エラー: {e}")
        return None

def process_uploaded_images(image_files, upload_folder):
    """アップロードされた画像を処理してGPS情報を抽出"""
    try:
        saved_files = []
        gps_data = None
        
        for i, image_file in enumerate(image_files):
            if image_file and image_file.filename:
                # ファイルを保存
                filename = f"{i+1}_{image_file.filename}"
                file_path = os.path.join(upload_folder, filename)
                image_file.save(file_path)
                saved_files.append(file_path)
                
                # GPS情報を抽出（最初に見つかったものを使用）
                if not gps_data:
                    extracted_gps = extract_gps_from_image(file_path)
                    if extracted_gps:
                        gps_data = extracted_gps
                        gps_data['source_file'] = filename
                        gps_data['source_index'] = i
        
        return {
            'saved_files': saved_files,
            'gps_data': gps_data,
            'processed_count': len(saved_files)
        }
        
    except Exception as e:
        print(f"画像処理エラー: {e}")
        return {
            'saved_files': [],
            'gps_data': None,
            'processed_count': 0,
            'error': str(e)
        }