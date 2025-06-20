# LocalGrammer API仕様書

## 概要
LocalGrammerアプリケーションのRESTful API仕様書です。地域密着型の写真投稿SNSアプリのバックエンドAPIを提供します。

## ベースURL
```
http://127.0.0.1:5002/api
```

## 認証方式
セッションベース認証（Cookie使用）

---

## 🔐 認証API (Authentication APIs)

### 1. ユーザー登録
新規ユーザーアカウントを作成します。

```http
POST /register
Content-Type: application/json
```

**リクエストボディ:**
```json
{
  "username": "string",
  "password": "string"
}
```

**レスポンス:**
```json
{
  "success": true,
  "message": "User registered successfully."
}
```

**エラーレスポンス:**
```json
{
  "success": false,
  "message": "Username already exists."
}
```

---

### 2. ログイン
ユーザー認証を行い、セッションを開始します。

```http
POST /login
Content-Type: application/json
```

**リクエストボディ:**
```json
{
  "username": "string",
  "password": "string"
}
```

**レスポンス:**
```json
{
  "success": true,
  "message": "Login successful.",
  "user": {
    "user_id": "uuid",
    "username": "string"
  }
}
```

**エラーレスポンス:**
```json
{
  "success": false,
  "message": "Invalid credentials."
}
```

---

### 3. ログアウト
現在のセッションを終了します。

```http
POST /logout
```

**レスポンス:**
```json
{
  "success": true,
  "message": "Logged out successfully."
}
```

---

### 4. ログイン状態確認
現在のログイン状態を確認します。

```http
GET /status
```

**レスポンス（ログイン中）:**
```json
{
  "logged_in": true,
  "user": {
    "user_id": "uuid",
    "username": "string"
  }
}
```

**レスポンス（未ログイン）:**
```json
{
  "logged_in": false
}
```

---

## 📝 投稿API (Post APIs)

### 5. ホームフィード取得
ユーザーの地域・タグ設定に基づいてフィルタリングされた投稿一覧を取得します。

```http
GET /home_feed
Authorization: Required (Session)
```

**レスポンス:**
```json
[
  {
    "id": "uuid",
    "user_id": "uuid",
    "username": "string",
    "tag": "string",
    "region": {
      "region": "string"
    },
    "images": ["filename1.jpg", "filename2.jpg"],
    "created_at": "2024-01-01T12:00:00",
    "comment_count": 5,
    "comments": [
      {
        "id": "uuid",
        "post_id": "uuid",
        "user_id": "uuid",
        "username": "string",
        "comment": "string",
        "created_at": "2024-01-01T12:00:00"
      }
    ],
    "like_count": 10,
    "user_liked": false,
    "latitude": 35.1803,
    "longitude": 136.9066
  }
]
```

---

### 6. 自分の投稿取得（日記機能）
ログインユーザーの投稿一覧を取得します。

```http
GET /my_posts
Authorization: Required (Session)
```

**レスポンス:**
```json
[
  {
    "id": "uuid",
    "user_id": "uuid",
    "username": "string",
    "tag": "string",
    "region": {
      "region": "string"
    },
    "images": ["filename1.jpg"],
    "created_at": "2024-01-01T12:00:00",
    "comment_count": 3,
    "comments": [...],
    "like_count": 5,
    "user_liked": true,
    "latitude": 35.1803,
    "longitude": 136.9066
  }
]
```

---

### 7. 投稿作成
新しい投稿を作成します。

```http
POST /posts
Content-Type: multipart/form-data
Authorization: Required (Session)
```

**リクエストボディ（Form Data）:**
```
tag: string (required) - 投稿タグ
region: string (optional) - 地域名（自動判定される場合は省略可）
latitude: float (optional) - 緯度
longitude: float (optional) - 経度
image1: File (optional) - 画像ファイル1
image2: File (optional) - 画像ファイル2
image3: File (optional) - 画像ファイル3
image4: File (optional) - 画像ファイル4
```

**レスポンス:**
```json
{
  "success": true,
  "message": "Post created successfully.",
  "post": {
    "id": "uuid",
    "user_id": "uuid",
    "username": "string",
    "tag": "string",
    "region": {
      "region": "string"
    },
    "images": ["filename1.jpg"],
    "created_at": "2024-01-01T12:00:00",
    "latitude": 35.1803,
    "longitude": 136.9066
  }
}
```

---

### 8. 投稿削除
指定した投稿を削除します。

```http
DELETE /posts/{post_id}
Authorization: Required (Session)
```

**パラメータ:**
- `post_id`: 削除する投稿のID

**レスポンス:**
```json
{
  "success": true,
  "message": "Post deleted successfully."
}
```

**エラーレスポンス:**
```json
{
  "success": false,
  "message": "Post not found."
}
```

---

### 9. いいねした投稿一覧取得
ユーザーがいいねした投稿一覧を取得します。

```http
GET /liked_posts
Authorization: Required (Session)
```

**レスポンス:**
```json
[
  {
    "id": "uuid",
    "user_id": "uuid",
    "username": "string",
    "tag": "string",
    "region": {
      "region": "string"
    },
    "images": ["filename1.jpg"],
    "created_at": "2024-01-01T12:00:00",
    "comment_count": 2,
    "comments": [...],
    "like_count": 8,
    "user_liked": true,
    "latitude": 35.1803,
    "longitude": 136.9066
  }
]
```

---

## 👍 いいね・コメントAPI (Like & Comment APIs)

### 10. いいね切り替え
投稿のいいね状態を切り替えます。

```http
POST /posts/{post_id}/like
Authorization: Required (Session)
```

**パラメータ:**
- `post_id`: 投稿ID

**レスポンス:**
```json
{
  "success": true,
  "liked": true,
  "like_count": 11
}
```

---

### 11. コメント追加
投稿にコメントを追加します。

```http
POST /posts/{post_id}/comments
Content-Type: application/json
Authorization: Required (Session)
```

**パラメータ:**
- `post_id`: 投稿ID

**リクエストボディ:**
```json
{
  "comment_text": "string"
}
```

**レスポンス:**
```json
{
  "success": true,
  "comment": {
    "id": "uuid",
    "post_id": "uuid",
    "user_id": "uuid",
    "username": "string",
    "comment": "string",
    "created_at": "2024-01-01T12:00:00"
  },
  "message": "Comment added successfully"
}
```

---

### 12. コメント削除
指定したコメントを削除します。

```http
DELETE /comments/{comment_id}
Authorization: Required (Session)
```

**パラメータ:**
- `comment_id`: コメントID

**レスポンス:**
```json
{
  "success": true,
  "message": "Comment deleted successfully."
}
```

**エラーレスポンス:**
```json
{
  "success": false,
  "message": "Permission denied."
}
```

---

## 👤 プロフィールAPI (Profile APIs)

### 13. プロフィール取得
ユーザーのプロフィール情報を取得します。

```http
GET /profile
Authorization: Required (Session)
```

**レスポンス:**
```json
{
  "region": "東海圏",
  "tags": ["景色", "動物", "スイーツ", "映え"]
}
```

---

### 14. プロフィール更新
ユーザーのプロフィール情報を更新します。

```http
POST /profile
Content-Type: application/json
Authorization: Required (Session)
```

**リクエストボディ:**
```json
{
  "region": "東海圏",
  "tags": ["景色", "動物", "スイーツ"]
}
```

**レスポンス:**
```json
{
  "success": true,
  "message": "Profile updated successfully."
}
```

---

## 📊 静的データAPI (Static Data APIs)

### 15. 静的データ取得
利用可能な地域とタグの一覧を取得します。

```http
GET /static_data
```

**レスポンス:**
```json
{
  "regions": [
    "東海圏",
    "首都圏",
    "関西圏",
    "九州",
    "沖縄",
    "北海道",
    "東北",
    "中国・四国",
    "北陸・甲信越"
  ],
  "tags": [
    "景色",
    "動物",
    "スイーツ",
    "映え",
    "モーニング",
    "ランチ",
    "ディナー",
    "スポーツ"
  ]
}
```

---

## 📍 位置情報API (Location APIs)

### 16. 座標から地域判定
緯度経度から地域を自動判定します。

```http
POST /detect_region
Content-Type: application/json
```

**リクエストボディ:**
```json
{
  "latitude": 35.1803,
  "longitude": 136.9066
}
```

**レスポンス:**
```json
{
  "success": true,
  "region": "東海圏"
}
```

---

### 17. 複数画像からGPS抽出
複数の画像ファイルからGPS情報を抽出します。

```http
POST /extract_gps_from_images
Content-Type: multipart/form-data
```

**リクエストボディ（Form Data）:**
```
image1: File (optional)
image2: File (optional)
image3: File (optional)
image4: File (optional)
```

**レスポンス:**
```json
{
  "success": true,
  "latitude": 35.1803,
  "longitude": 136.9066
}
```

**エラーレスポンス:**
```json
{
  "success": false,
  "message": "No GPS data found in images"
}
```

---

### 18. 単一画像からGPS抽出
単一の画像ファイルからGPS情報を抽出します。

```http
POST /extract_gps_from_single_image
Content-Type: multipart/form-data
```

**リクエストボディ（Form Data）:**
```
image: File (required)
```

**レスポンス:**
```json
{
  "success": true,
  "latitude": 35.1803,
  "longitude": 136.9066,
  "message": "GPS情報を取得しました"
}
```

**エラーレスポンス:**
```json
{
  "success": false,
  "message": "画像にGPS情報が含まれていません"
}
```

---

## エラーコード一覧

| ステータスコード | 意味 | 例 |
|---|---|---|
| 200 | 成功 | データ取得成功 |
| 201 | 作成成功 | 投稿・コメント作成成功 |
| 400 | リクエストエラー | 必須パラメータ不足 |
| 401 | 認証エラー | ログインが必要 |
| 403 | 権限エラー | 削除権限なし |
| 404 | 見つからない | 投稿・コメントが存在しない |
| 409 | 競合エラー | ユーザー名重複 |
| 500 | サーバーエラー | 内部処理エラー |

---

## 注意事項

1. **認証が必要なAPI**: セッションCookieが必要です
2. **画像アップロード**: 対応形式は PNG, JPG, JPEG, GIF, WebP
3. **ファイルサイズ制限**: 最大16MB
4. **画像枚数制限**: 1投稿あたり最大4枚
5. **GPS情報**: EXIF情報から自動抽出、対応していない場合は手動設定が必要