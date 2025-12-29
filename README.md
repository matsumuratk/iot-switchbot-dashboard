# IoT SwitchBot ダッシュボード

InfluxDBとGrafanaを使用したSwitchBot温湿度センサーのダッシュボード。

## 機能

- **SwitchBot API統合**: SwitchBotデバイスからセンサーデータを自動取得（ポーリングモード）
- **HTTP REST API**: M5StickC Plus2やその他の外部ソースからHTTP POST経由でセンサーデータを受信（プッシュモード）
- **M5StickC Plus2統合**: BLE経由でSwitchBotデバイスからセンサーデータを収集
- **InfluxDB**: 時系列センサーデータの保存
- **Grafana**: ダッシュボードによるセンサーデータの可視化

## アーキテクチャ

- **python**: SwitchBot APIポーリングサービス（5分ごとにスケジュール実行）
- **webserver**: M5StickC Plus2などからセンサーデータを受信するHTTP REST APIサーバー
- **influxdb**: 時系列データベース（バージョン 2.7.11）
- **grafana**: ダッシュボード可視化（バージョン 11.3.4）
- **M5StickCPlus2**: SwitchBotセンサーデータを読み取りwebserverに送信するBLEスキャナー

## セットアップ

### 前提条件

- Docker と Docker Compose
- SwitchBot API認証情報（ポーリングモードを使用する場合、オプション）
- M5StickC Plus2（BLEスキャンモードを使用する場合、オプション）

### インストール

1. リポジトリをクローン:
```bash
git clone <repository-url>
cd iot-switchbot-dashboard
```

2. SwitchBot API認証情報を含む`.env`ファイルを作成:
```bash
INFLUXDB_TOKEN=  # 手順3の後に入力
```

3. Dockerコンテナを起動:
```bash
docker-compose up -d --build
```

4. 設定ファイルからInfluxDBトークンを取得:
```bash
# Windows/WSLの場合
cat ./docker/influxdb/config/influx-configs
```

5. 手順4で取得したトークンで`.env`ファイルの`INFLUXDB_TOKEN`を更新。

6. サービスを再起動:
```bash
docker-compose restart
```

## 使い方

### ログの確認

```bash
docker-compose logs -f
```

### サービスへのアクセス

- **InfluxDB**: http://localhost:8086 (ユーザー名: `user`, パスワード: `password`)
- **Grafana**: http://localhost:3000 (ユーザー名: `admin`, パスワード: セットアップ時に設定)

## HTTP REST API

webserverは、M5StickC Plus2やその他の外部ソースからセンサーデータを受信するためのREST APIエンドポイントを提供します。

### Webserverの起動

webserverは`docker-compose up`で自動的に起動します。ポート5000で実行されます。

### APIエンドポイント

#### ヘルスチェック
サーバーが稼働しているか確認します。

```bash
GET http://localhost:5000/health
```

**レスポンス:**
```json
{
  "status": "ok",
  "timestamp": "2025-12-27T15:52:16.471046"
}
```

#### デバイスリストの取得
登録されているSwitchBotデバイスのリストを取得します。

```bash
GET http://localhost:5000/api/devices
```

**レスポンス:**
```json
{
  "devices": [
    {
      "deviceId": "CA5F46463F21",
      "deviceName": "11_thermohygrometer",
      "deviceType": "WoIOSensor",
      "enableCloudService": true,
      "hubDeviceId": "D879924895A8"
    }
  ],
  "count": 6,
  "timestamp": "2025-12-27T15:05:03.622423"
}
```

#### センサーデータの送信
InfluxDBに保存するセンサーデータを送信します。M5StickC Plus2やその他の外部データソースによって使用されます。

```bash
POST http://localhost:5000/api/sensor-data
Content-Type: application/json
```

**リクエストボディ** ([sample_request.json](sample_request.json)を参照):
```json
{
  "devices": [
    {
      "deviceName": "11_thermohygrometer",
      "temperature": 23.5,
      "humidity": 55,
      "battery": 100
    },
    {
      "deviceName": "12_thermohygrometer",
      "temperature": 24.2,
      "humidity": 52,
      "battery": 95
    }
  ]
}
```

**注意**: 
- `deviceId`と`deviceType`は`deviceName`に基づいて`device_list.json`から自動的に取得されます
- `device_list.json`をお使いのデバイス情報で更新する必要があります

**レスポンス:**
```json
{
  "success": true,
  "saved": 2,
  "total": 2,
  "timestamp": "2025-12-27T15:52:16.530052"
}
```

### APIのテスト

#### curlを使用（Linux/WSL）

```bash
# ヘルスチェック
curl http://localhost:5000/health

# デバイスリストを取得
curl http://localhost:5000/api/devices

# センサーデータを送信
curl -X POST http://localhost:5000/api/sensor-data \
  -H "Content-Type: application/json" \
  -d @sample_request.json
```

#### サンプルスクリプトを使用

```bash
# WSL または Git Bash の場合
chmod +x sample_curl.sh
./sample_curl.sh

# Windows WSL の場合
wsl -e bash -c "cd /mnt/c/Users/<your-path>/iot-switchbot-dashboard && bash sample_curl.sh"
```

## M5StickC Plus2 セットアップ

M5StickC Plus2はBLE経由でSwitchBot温湿度センサーをスキャンし、データをwebserverに送信します。

### ハードウェア要件
- M5StickC Plus2
- SwitchBot 温湿度センサー

### 設定

1. Arduino IDEで[M5StickCPlus2/switchbot_reader.ino](M5StickCPlus2/switchbot_reader.ino)を開く
2. ターゲットのMACアドレスを更新:
```cpp
const char* TARGET_MACS[] = {
  "d4:0e:84:86:51:16",  // デバイス1
  "dd:42:06:46:2f:81",  // デバイス2
};
const int NUM_DEVICES = 2;
```
3. コード内のサーバーURLとWiFi認証情報を更新
4. M5StickC Plus2にアップロード

### 機能
- 複数のSwitchBotデバイスをスキャン
- 10分ごとに更新（設定変更可能）
- LCD上に温度、湿度、バッテリー残量を表示
- 接続失敗時の自動リトライ
- ボタン操作による手動デバイス切り替え

## プロジェクト構成

```
.
├── app/                    # Python APIポーリングアプリケーション
├── docker/
│   ├── grafana/           # Grafanaデータと設定
│   ├── influxdb/          # InfluxDBデータと設定
│   └── webserver/         # HTTP REST APIサーバー
│       ├── server.py      # Flaskサーバー実装
│       ├── device_list.json # デバイス設定
│       └── requirements.txt
├── M5StickCPlus2/         # M5StickC Plus2 Arduinoコード
│   └── switchbot_reader.ino
├── compose.yml            # Docker Compose設定
├── pyproject.toml         # Pythonプロジェクト設定
├── sample_curl.sh         # サンプルAPIテストスクリプト
└── sample_request.json    # サンプルAPIリクエストデータ
```

## 開発

### Python依存関係

プロジェクトはPython依存関係の管理にPoetryを使用しています:

```bash
# 依存関係をインストール
poetry install

# 仮想環境で実行
poetry run python app/main.py
```

### デバイスリストの設定

`docker/webserver/device_list.json`をお使いのSwitchBotデバイス情報で更新してください:

```json
[
  {
    "deviceId": "YOUR_DEVICE_ID",
    "deviceName": "YOUR_DEVICE_NAME",
    "deviceType": "WoIOSensor",
    "hubDeviceId": "YOUR_HUB_ID"
  }
]
```

## AWS Lightsailへのデプロイ

### 1. VMの立ち上げ

1. [AWS Lightsail コンソール](https://lightsail.aws.amazon.com/)にアクセス
2. 「インスタンスの作成」をクリック
3. 以下の設定を選択:
   - **インスタンスロケーション**: 東京（ap-northeast-1）
   - **プラットフォーム**: Linux/Unix
   - **ブループリント**: OS のみ → Ubuntu 22.04 LTS
   - **インスタンスプラン**: 2GB以上推奨（$10/月プラン以上）
   - **インスタンス名**: `iot-switchbot-dashboard`
4. 「インスタンスの作成」をクリック

### 2. 初期設定

#### SSHキーのダウンロード
1. Lightsailコンソールで「アカウント」→「SSHキー」
2. デフォルトのキーをダウンロード（例：`LightsailDefaultKey-ap-northeast-1.pem`）
3. キーのパーミッションを設定:
```bash
chmod 400 LightsailDefaultKey-ap-northeast-1.pem
```

#### SSH接続
```bash
ssh -i LightsailDefaultKey-ap-northeast-1.pem ubuntu@<インスタンスのパブリックIP>
```

※Windows＋WSLではchmodができないのでキーファイルを~/.sshにコピーしてchmod 400 として実行
```
ssh -i ~/.ssh/LightsailDefaultKey-ap-northeast-1.pem 
ubuntu@35.79.71.96
```


#### システムアップデート
```bash
sudo apt update
sudo apt upgrade -y
```

### 3. ファイアウォール設定

Lightsailコンソールで「ネットワーキング」タブから以下のポートを開放:

| アプリケーション | プロトコル | ポート範囲 | 説明 |
|-----------------|----------|-----------|------|
| HTTP | TCP | 80 | Nginx（オプション） |
| HTTPS | TCP | 443 | Nginx（オプション） |
| Custom | TCP | 3000 | Grafana |
| Custom | TCP | 5000 | WebServer API |
| Custom | TCP | 8086 | InfluxDB |

### 4. DNS設定（オプション）

独自ドメインを使用する場合:

1. Lightsailコンソールで「ネットワーキング」→「DNSゾーンの作成」
2. ドメイン名を入力（例：`example.com`）
3. Aレコードを追加:
   - **サブドメイン**: `@`（ルートドメイン）または `iot`
   - **送信先**: インスタンスを選択
4. ドメインレジストラでネームサーバーを変更

### 5. Gitのインストール

```bash
sudo apt install git -y
git --version
```

### 6. Dockerのインストール

```bash
# Dockerの公式GPGキーを追加
sudo apt install ca-certificates curl gnupg -y
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# Dockerリポジトリを追加
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Dockerをインストール
sudo apt update
sudo apt install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin -y

# Dockerをサービスとして起動
sudo systemctl enable docker
sudo systemctl start docker

# 現在のユーザーをdockerグループに追加
sudo usermod -aG docker $USER
newgrp docker

# インストール確認
docker --version
docker compose version
```

### 7. プロジェクトのクローンと設定

```bash
# ホームディレクトリに移動
cd ~

# リポジトリをクローン
git clone https://github.com/<your-username>/iot-switchbot-dashboard.git
cd iot-switchbot-dashboard

# .envファイルを作成
nano .env
```

`.env`ファイルの内容:
```bash
INFLUXDB_TOKEN=  # 後で設定
```

保存して終了（Ctrl + O → Enter → Ctrl + X）

### 8. Dockerコンテナの起動

```bash
# コンテナをビルド・起動
docker compose up -d --build

# 起動状態を確認
docker compose ps

# ログを確認
docker compose logs -f
```

### 9. InfluxDBトークンの取得と設定

```bash
# InfluxDBトークンを表示
cat ./docker/influxdb/config/influx-configs

# .envファイルを編集してトークンを追加
nano .env
```

`INFLUXDB_TOKEN=`の行に取得したトークンを貼り付けて保存。

```bash
# コンテナを再起動
docker compose restart
```

### 10. アクセス確認

ブラウザで以下のURLにアクセス:

- **InfluxDB**: `http://<パブリックIP>:8086`
  - ユーザー名: `user`
  - パスワード: `password`

- **Grafana**: `http://<パブリックIP>:3000`
  - 初回アクセス時に管理者パスワードを設定

- **WebServer API**: `http://<パブリックIP>:5000/health`
  - ヘルスチェックエンドポイントで動作確認

### 11. Grafanaの設定

1. Grafanaにログイン（`http://<パブリックIP>:3000`）
2. 「Connections」→「Data sources」→「Add data source」
3. 「InfluxDB」を選択
4. 以下を設定:
   - **Name**: `SwitchBot`
   - **Query Language**: `Flux`
   - **URL**: `http://influxdb:8086`
   - **Organization**: `org`
   - **Token**: `.env`ファイルの`INFLUXDB_TOKEN`
   - **Default Bucket**: `switchbot`
5. 「Save & Test」をクリック

### 12. セキュリティ強化（推奨）

#### ファイアウォールの設定
```bash
# UFWを有効化
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 3000/tcp
sudo ufw allow 5000/tcp
sudo ufw allow 8086/tcp
sudo ufw enable
```

#### Nginxリバースプロキシの設定（オプション）

```bash
# Nginxをインストール
sudo apt install nginx -y

# 設定ファイルを作成
sudo nano /etc/nginx/sites-available/iot-dashboard
```

設定内容:
```nginx
server {
    listen 80;
    server_name <your-domain-or-ip>;

    location /grafana/ {
        proxy_pass http://localhost:3000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /api/ {
        proxy_pass http://localhost:5000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /influxdb/ {
        proxy_pass http://localhost:8086/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
# シンボリックリンクを作成
sudo ln -s /etc/nginx/sites-available/iot-dashboard /etc/nginx/sites-enabled/

# Nginx設定をテスト
sudo nginx -t

# Nginxを再起動
sudo systemctl restart nginx
```

### 13. 自動起動の設定

```bash
# docker-composeの自動起動スクリプトを作成
sudo nano /etc/systemd/system/iot-dashboard.service
```

内容:
```ini
[Unit]
Description=IoT SwitchBot Dashboard
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/ubuntu/iot-switchbot-dashboard
ExecStart=/usr/bin/docker compose up -d
ExecStop=/usr/bin/docker compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
```

```bash
# サービスを有効化
sudo systemctl enable iot-dashboard.service
sudo systemctl start iot-dashboard.service

# ステータス確認
sudo systemctl status iot-dashboard.service
```

### 14. メンテナンスコマンド

```bash
# ログの確認
docker compose logs -f

# コンテナの再起動
docker compose restart

# 最新版へのアップデート
cd ~/iot-switchbot-dashboard
git pull
docker compose down
docker compose up -d --build

# データのバックアップ
tar -czf backup-$(date +%Y%m%d).tar.gz docker/influxdb/data docker/grafana/data

# ディスク使用量の確認
docker system df
docker system prune -a  # 未使用リソースの削除
```

## トラブルシューティング

### InfluxDBトークンの問題
- `docker/influxdb/config/influx-configs`からトークンを必ずコピーしてください
- `.env`ファイルを更新した後、サービスを再起動してください

### M5StickC Plus2の接続問題
- WiFi認証情報を確認してください
- デバイスからサーバーURLにアクセス可能か確認してください
- SwitchBotデバイスが範囲内にあり、BLEが有効になっていることを確認してください

### Dockerの問題
- `docker-compose down -v`を実行してボリュームをクリーンアップしてください
- `docker-compose up -d --build`でリビルドしてください

### Lightsail固有の問題
- ファイアウォール設定でポートが開放されているか確認
- インスタンスのパブリックIPが変わっていないか確認
- メモリ不足の場合はインスタンスプランをアップグレード

## ライセンス

MIT License

