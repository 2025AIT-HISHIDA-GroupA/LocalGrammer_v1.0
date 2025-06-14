from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import os

# HEIC形式のサポート
try:
    from PIL import ImageFile
    from pillow_heif import register_heif_opener
    register_heif_opener()
    print("HEIC形式のサポートが有効になりました")
except ImportError:
    print("HEIC形式のサポートが利用できません (pillow-heif未インストール)")

def get_coordinates_from_image(image_path):
    """
    画像ファイルから緯度・経度を取得
    返り値: (latitude, longitude) または None
    """
    try:
        print(f"画像ファイルを解析中: {image_path}")
        
        # ファイル情報を出力
        file_size = os.path.getsize(image_path)
        file_ext = os.path.splitext(image_path)[1].lower()
        print(f"ファイルサイズ: {file_size} bytes, 拡張子: {file_ext}")
        
        # 画像ファイルを開く
        try:
            image = Image.open(image_path)
            print(f"画像形式: {image.format}, サイズ: {image.size}, モード: {image.mode}")
        except Exception as e:
            print(f"画像ファイルを開けませんでした: {e}")
            return None
        
        # 複数の方法でGPS情報を取得を試行
        coordinates = None
        
        # 方法1: 新しいPillowのgetexif()とget_ifd()を使用
        try:
            exifdata = image.getexif()
            print(f"EXIF データの存在: {bool(exifdata)}")
            
            # EXIFデータがある場合、全タグを出力（デバッグ用）
            if exifdata:
                print("=== 主要なEXIF データ ===")
                important_tags = ['Make', 'Model', 'DateTime', 'GPS GPSLatitude', 'GPS GPSLongitude']
                for tag_id in exifdata:
                    tag = TAGS.get(tag_id, tag_id)
                    if any(important in str(tag) for important in ['GPS', 'Make', 'Model', 'DateTime']):
                        print(f"{tag}: {exifdata[tag_id]}")
                
                # GPS情報のオフセットを探す
                gps_offset = None
                for tag_id in exifdata:
                    tag = TAGS.get(tag_id, tag_id)
                    if tag == "GPSInfo":
                        gps_offset = exifdata[tag_id]
                        print(f"GPS情報のオフセット: {gps_offset}")
                        break
                
                if gps_offset is not None:
                    try:
                        # GPS IFDを取得
                        gps_ifd = exifdata.get_ifd(gps_offset)
                        if gps_ifd:
                            print("方法1: GPS IFDから座標を抽出中...")
                            coordinates = extract_coordinates_from_gps_dict(dict(gps_ifd))
                            if coordinates:
                                print(f"方法1で座標取得成功: {coordinates}")
                                return coordinates
                    except Exception as e:
                        print(f"方法1のGPS IFD取得エラー: {e}")
        except Exception as e:
            print(f"方法1のエラー: {e}")
        
        # 方法2: 古いPillowの_getexif()を使用
        try:
            print("方法2: 古い_getexif()メソッドを試行中...")
            if hasattr(image, '_getexif'):
                exif_dict = image._getexif()
                if exif_dict is not None:
                    print(f"_getexif()でEXIFデータ取得: {len(exif_dict)} エントリ")
                    
                    # 重要なEXIFタグを出力
                    if 271 in exif_dict:  # Make
                        print(f"カメラメーカー: {exif_dict[271]}")
                    if 272 in exif_dict:  # Model
                        print(f"カメラモデル: {exif_dict[272]}")
                    if 306 in exif_dict:  # DateTime
                        print(f"撮影日時: {exif_dict[306]}")
                    
                    gps_info = exif_dict.get(34853)  # GPS情報のタグID
                    if gps_info:
                        print(f"方法2でGPS情報を発見: {type(gps_info)}")
                        coordinates = extract_coordinates_from_gps_dict(gps_info)
                        if coordinates:
                            print(f"方法2で座標取得成功: {coordinates}")
                            return coordinates
                    else:
                        print("方法2: GPS情報(34853)が見つかりません")
                        # 全てのタグを確認（デバッグ用）
                        print("利用可能なEXIFタグ:")
                        for tag_id, value in exif_dict.items():
                            tag_name = TAGS.get(tag_id, f"Unknown_{tag_id}")
                            if 'GPS' in str(tag_name) or tag_id in [34853, 34854, 34855]:
                                print(f"  {tag_name} ({tag_id}): {value}")
                else:
                    print("方法2: _getexif()がNoneを返しました")
            else:
                print("方法2: _getexif()メソッドが存在しません")
        except Exception as e:
            print(f"方法2のエラー: {e}")
        
        # 方法3: ExifRead ライブラリを使用
        try:
            print("方法3: ExifReadライブラリを試行中...")
            coordinates = parse_exif_manually(image_path)
            if coordinates:
                print(f"方法3で座標取得成功: {coordinates}")
                return coordinates
        except Exception as e:
            print(f"方法3のエラー: {e}")
        
        # 方法4: 画像メタデータの詳細確認
        try:
            print("方法4: 画像メタデータの詳細確認...")
            if hasattr(image, 'info'):
                print(f"画像info: {image.info}")
        except Exception as e:
            print(f"方法4のエラー: {e}")
        
        print("すべての方法で GPS情報の取得に失敗しました")
        print("=== 診断情報 ===")
        print("- 画像がスマートフォンで撮影されたオリジナルファイルか確認してください")
        print("- Googleフォト等からダウンロードした画像は位置情報が削除されている可能性があります")
        print("- SNSやメッセージアプリを経由した画像は位置情報が削除されます")
        return None
        
    except Exception as e:
        print(f"画像から位置情報を取得できませんでした: {e}")
        import traceback
        traceback.print_exc()
        return None

def extract_coordinates_from_gps_dict(gps_info):
    """
    GPS辞書から座標を抽出
    """
    try:
        print(f"GPS辞書の内容: {gps_info}")
        print(f"GPS辞書のタイプ: {type(gps_info)}")
        
        # GPSタグの詳細を出力
        print("=== GPS データ詳細 ===")
        for key, value in gps_info.items():
            gps_tag = GPSTAGS.get(key, f"Unknown_{key}")
            print(f"{gps_tag} ({key}): {value} (type: {type(value)})")
        
        def convert_to_degrees(value):
            """GPS座標を度数法に変換"""
            try:
                print(f"座標変換対象: {value}, タイプ: {type(value)}")
                
                # 様々な形式に対応
                if isinstance(value, (list, tuple)) and len(value) == 3:
                    d, m, s = value
                    # 分数オブジェクトの場合は float に変換
                    if hasattr(d, 'numerator') and hasattr(d, 'denominator'):
                        d = float(d.numerator) / float(d.denominator)
                    if hasattr(m, 'numerator') and hasattr(m, 'denominator'):
                        m = float(m.numerator) / float(m.denominator)
                    if hasattr(s, 'numerator') and hasattr(s, 'denominator'):
                        s = float(s.numerator) / float(s.denominator)
                    
                    result = float(d) + (float(m) / 60.0) + (float(s) / 3600.0)
                    print(f"変換結果: {result}")
                    return result
                else:
                    print(f"予期しない座標形式: {value}")
                    return None
            except (TypeError, ValueError, ZeroDivisionError) as e:
                print(f"座標変換エラー: {e}")
                return None
        
        # 緯度の取得 (GPSLatitude=2, GPSLatitudeRef=1)
        lat = None
        lat_ref = None
        if 2 in gps_info and 1 in gps_info:
            print("緯度データを処理中...")
            lat = convert_to_degrees(gps_info[2])
            lat_ref = gps_info[1]
            print(f"緯度参照: {lat_ref}")
            if lat is not None and lat_ref == 'S':
                lat = -lat
                print("南緯のため負の値に変換")
        
        # 経度の取得 (GPSLongitude=4, GPSLongitudeRef=3)
        lon = None
        lon_ref = None
        if 4 in gps_info and 3 in gps_info:
            print("経度データを処理中...")
            lon = convert_to_degrees(gps_info[4])
            lon_ref = gps_info[3]
            print(f"経度参照: {lon_ref}")
            if lon is not None and lon_ref == 'W':
                lon = -lon
                print("西経のため負の値に変換")
        
        print(f"最終結果 - 緯度: {lat}, 経度: {lon}")
        
        if lat is not None and lon is not None:
            return (lat, lon)
        
        return None
        
    except Exception as e:
        print(f"座標抽出エラー: {e}")
        import traceback
        traceback.print_exc()
        return None

def parse_exif_manually(image_path):
    """
    手動でEXIFデータを解析する方法
    """
    try:
        # exifread ライブラリを試行（利用可能な場合）
        try:
            import exifread
            with open(image_path, 'rb') as f:
                tags = exifread.process_file(f)
                
            # GPS情報を探す
            lat_tag = tags.get('GPS GPSLatitude')
            lat_ref_tag = tags.get('GPS GPSLatitudeRef')
            lon_tag = tags.get('GPS GPSLongitude')
            lon_ref_tag = tags.get('GPS GPSLongitudeRef')
            
            if lat_tag and lon_tag and lat_ref_tag and lon_ref_tag:
                print("exifreadで GPS情報を発見")
                
                def convert_dms_to_decimal(dms_tag):
                    """度分秒を10進数に変換"""
                    parts = str(dms_tag).split(', ')
                    if len(parts) == 3:
                        degrees = float(parts[0].split('/')[0]) / float(parts[0].split('/')[1]) if '/' in parts[0] else float(parts[0])
                        minutes = float(parts[1].split('/')[0]) / float(parts[1].split('/')[1]) if '/' in parts[1] else float(parts[1])
                        seconds = float(parts[2].split('/')[0]) / float(parts[2].split('/')[1]) if '/' in parts[2] else float(parts[2])
                        return degrees + minutes/60.0 + seconds/3600.0
                    return None
                
                lat = convert_dms_to_decimal(lat_tag)
                lon = convert_dms_to_decimal(lon_tag)
                
                if lat and lon:
                    if str(lat_ref_tag) == 'S':
                        lat = -lat
                    if str(lon_ref_tag) == 'W':
                        lon = -lon
                    
                    return (lat, lon)
                
        except ImportError:
            print("exifread ライブラリが利用できません")
        
        return None
        
    except Exception as e:
        print(f"手動解析エラー: {e}")
        return None

def extract_coordinates_from_uploaded_images(image_files, upload_folder):
    """
    アップロードされた画像から位置情報を抽出
    返り値: 最初に見つかった座標 (latitude, longitude) または None
    """
    for image_file in image_files:
        if image_file:
            image_path = os.path.join(upload_folder, image_file)
            coordinates = get_coordinates_from_image(image_path)
            if coordinates:
                return coordinates
    return None