import re
import html

def sanitize_input(text):
    """入力値をサニタイズ"""
    if not text:
        return ""
    
    # HTMLエスケープ
    text = html.escape(text)
    
    # 改行文字を正規化
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    
    # 連続する改行を制限（最大3個まで）
    text = re.sub(r'\n{4,}', '\n\n\n', text)
    
    # 先頭と末尾の空白を削除
    text = text.strip()
    
    return text

def validate_comment(comment):
    """コメントの検証"""
    if not comment:
        return False, "コメントを入力してください"
    
    # 長さチェック
    if len(comment) > 1000:
        return False, "コメントは1000文字以内で入力してください"
    
    # 危険なパターンをチェック
    dangerous_patterns = [
        r'<script[^>]*>',
        r'javascript:',
        r'onload\s*=',
        r'onerror\s*=',
        r'onclick\s*=',
        r'<iframe[^>]*>',
        r'<object[^>]*>',
        r'<embed[^>]*>'
    ]
    
    comment_lower = comment.lower()
    for pattern in dangerous_patterns:
        if re.search(pattern, comment_lower):
            return False, "使用できない文字が含まれています"
    
    return True, "OK"

def validate_tag(tag):
    """タグの検証"""
    if not tag:
        return False, "タグを選択してください"
    
    # 許可されたタグのリスト
    from config import TAGS
    if tag not in TAGS:
        return False, "無効なタグが選択されています"
    
    return True, "OK"

def validate_region(region):
    """地域の検証"""
    if not region:
        return False, "地域を選択してください"
    
    # 許可された地域のリスト
    from config import REGIONS
    if region not in REGIONS:
        return False, "無効な地域が選択されています"
    
    return True, "OK"

def validate_username(username):
    """ユーザー名の検証"""
    if not username:
        return False, "ユーザー名を入力してください"
    
    # 長さチェック
    if len(username) < 3 or len(username) > 20:
        return False, "ユーザー名は3-20文字で入力してください"
    
    # 文字種チェック（英数字、日本語、一部記号のみ）
    if not re.match(r'^[a-zA-Z0-9ぁ-んァ-ヶー一-龯_-]+$', username):
        return False, "ユーザー名に使用できない文字が含まれています"
    
    return True, "OK"

def validate_password(password):
    """パスワードの検証"""
    if not password:
        return False, "パスワードを入力してください"
    
    # 長さチェック
    if len(password) < 6:
        return False, "パスワードは6文字以上で入力してください"
    
    if len(password) > 100:
        return False, "パスワードは100文字以内で入力してください"
    
    return True, "OK"

def validate_coordinates(latitude, longitude):
    """座標の検証"""
    try:
        if latitude is not None:
            lat = float(latitude)
            if lat < -90 or lat > 90:
                return False, "緯度は-90から90の範囲で入力してください"
        
        if longitude is not None:
            lng = float(longitude)
            if lng < -180 or lng > 180:
                return False, "経度は-180から180の範囲で入力してください"
        
        return True, "OK"
    except (ValueError, TypeError):
        return False, "座標の形式が正しくありません"