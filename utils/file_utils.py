import os
import uuid
from werkzeug.utils import secure_filename
from config import ALLOWED_EXTENSIONS

def allowed_file(filename):
    """ファイルの拡張子が許可されているかチェック"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_uploaded_file(file, upload_folder):
    """アップロードされたファイルを保存し、ファイル名を返す"""
    if file and file.filename != '' and allowed_file(file.filename):
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
    """ファイルを削除"""
    file_path = os.path.join(upload_folder, filename)
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
    except Exception as e:
        print(f"ファイル削除エラー: {e}")
    return False