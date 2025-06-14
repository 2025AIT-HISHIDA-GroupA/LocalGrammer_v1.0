# 位置情報機能追加ドキュメント

## 概要

画像から自動取得または手動設定できるようにしました。

## 注意！（2点）

### 1. 更新後は必ず依存関係をインストールしてください

```bash
pip install Pillow pillow-heif ExifRead
```

### 2. カメラで撮影した画像をそのまま投稿してください

Googleフォトなど経由しないでください。画像に座標が埋め込まれている場合、自動的に座標と地域が設定されます。

### 3. 



## 追加された機能

### 📍 位置情報必須投稿
- 位置情報（座標または地域）が設定されていない場合、投稿処理を中断し警告を表示
- 投稿時に座標データを`Coordinates.json`に保存（投稿IDと紐付け）

### 📷 画像からの自動位置取得
- 画像のEXIFデータから緯度・経度を自動抽出
- 検出成功時は地図上にピンを自動配置し、座標入力フィールドに値を設定

### 🗺️ 手動位置設定
- 投稿ページに地図を表示
- 地図クリックで任意の位置にピンを設定し、座標入力フィールドに値を設定

### 🌍 地域自動選択
- 設定された座標から適切な地域を自動判定し、地域選択プルダウンに反映
- 全国9地域に対応

### 📌 地図表示
- 各投稿の位置を地図上にピンで表示（地域別マップページにて）
- ピンクリックで投稿詳細を表示（将来的な機能拡張を示唆）

## 主な変更ファイル

```
utils/image_utils.py        # 新規 (または大幅更新): 画像位置情報抽出関連処理
utils/location_utils.py     # 新規 (または大幅更新): 地域判定ロジック
config.py                   # 地域境界定義追加
routes/posts.py             # 位置情報処理、Coordinates.jsonへの保存ロジック追加
routes/api.py               # 位置情報関連APIの追加・更新 (Coordinates.jsonへの保存/削除含む)
templates/post.html         # 地図機能、画像からの位置情報取得UI追加
Coordinates.json            # 新規: 投稿IDと座標データを紐付けて保存
```

## データ形式

投稿IDと座標を紐づけて保存：

```json
{
  "投稿ID": {
    "latitude": 35.699778,
    "longitude": 139.771700,
    "source": "exif"  // または "manual"
  }
}
```

**補足:** `Coordinates.json` には、上記に加えて `created_at` タイムスタンプも保存される場合があります。

## 使用方法

### 1. 投稿時
- 画像をアップロードすると、EXIFから位置情報が自動検出され、地図と座標フィールドに反映されます
- 複数の画像に位置情報がある場合、使用するものを選択できます
- または、地図をクリックして手動で位置を設定します
- 設定された位置情報に基づいて地域が自動選択されます（手動での変更も可能）

### 2. 閲覧時
- 地域ごとの地図ページで、その地域に属する投稿の位置がピンで表示されます

## 既存API変更

### 投稿関連API

位置情報（座標）の扱いが強化され、`Coordinates.json` との連携が追加されました。

#### POST /post（Web UIからの投稿）
- フォームから送信される座標パラメータは `latitude`（緯度）と `longitude`（経度）です
- 地域が未設定、かつ位置情報（座標）も未設定の場合は、投稿前にフロントエンドで警告が表示されます
- 投稿成功時、`Posts.json` に投稿データが保存されると共に、有効な座標があれば `Coordinates.json` にも投稿IDをキーとして座標データが保存されます

#### POST /api/posts（API経由の投稿作成）
- リクエストボディに `latitude`（緯度）と `longitude`（経度）パラメータを含めることができます
- 地域が必須です。座標から自動判定させるか、明示的に指定する必要があります
- 投稿作成時に、有効な座標データがあれば `Coordinates.json` にも投稿IDをキーとして保存されます
- レスポンスに位置情報は含まれません（投稿データ全体が返される場合、その中に含まれる可能性はあります）

#### DELETE /api/posts/{post_id}（API経由の投稿削除）
- 投稿を削除する際、`Posts.json` から投稿データが削除されるのに加え、`Coordinates.json` に関連する座標データが存在すればそれも自動的に削除されます