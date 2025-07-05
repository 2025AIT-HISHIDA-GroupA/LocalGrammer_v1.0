import os
import uuid
from werkzeug.utils import secure_filename
from config import ALLOWED_EXTENSIONS
from PIL import Image
try:
    import magic
except ImportError:
    magic = None

def allowed_file(filename):
    """ファイルの拡張子が許可されているかチェック"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_file_content(file):
    """ファイル内容を検証"""
    try:
        # ファイルサイズチェック（5MB制限）
        file.seek(0, 2)  # ファイルの最後に移動
        file_size = file.tell()
        file.seek(0)  # ファイルの最初に戻す
        
        if file_size > 5 * 1024 * 1024:  # 5MB
            return False, "ファイルサイズが5MBを超えています"
        
        # PILで画像として開けるかチェック
        img = Image.open(file)
        img.verify()
        file.seek(0)  # ファイルポインタを戻す
        
        # MIMEタイプをチェック（magicライブラリが利用可能な場合）
        if magic:
            file_data = file.read(1024)
            file.seek(0)
            mime_type = magic.from_buffer(file_data, mime=True)
            
            if not mime_type.startswith('image/'):
                return False, "画像ファイルではありません"
        
        return True, "OK"
    except Exception as e:
        return False, f"ファイル検証エラー: {str(e)}"

def save_uploaded_file(file, upload_folder):
    """アップロードされたファイルを保存し、ファイル名を返す"""
    if file and file.filename != '' and allowed_file(file.filename):
        # ファイル内容を検証
        is_valid, error_message = validate_file_content(file)
        if not is_valid:
            raise Exception(error_message)
        
        # ファイル名を安全にする
        filename = secure_filename(file.filename)
        # ユニークなファイル名を生成
        unique_filename = f"{uuid.uuid4()}_{filename}"
        file_path = os.path.join(upload_folder, unique_filename)
        
        try:
            file.save(file_path)
            return unique_filename
        except Exception as e:
            raise Exception(f'ファイルのアップロードに失敗しました: {str(e)}')
    return None

def delete_file(filename, upload_folder):
    """ファイルを削除（パストラバーサル対策）"""
    # ファイル名の安全性チェック
    if not filename or '/' in filename or '\\' in filename or '..' in filename:
        print(f"不正なファイル名: {filename}")
        return False
    
    file_path = os.path.join(upload_folder, filename)
    
    # パスが upload_folder 内にあることを確認
    if not os.path.abspath(file_path).startswith(os.path.abspath(upload_folder)):
        print(f"不正なパス: {file_path}")
        return False
    
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
    except Exception as e:
        print(f"ファイル削除エラー: {e}")
    return False