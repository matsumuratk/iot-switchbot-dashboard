# Lightsailへのデプロイ手順

このドキュメントでは、コード修正後にAWS Lightsailにデプロイする手順を説明します。

## 前提条件

- AWS Lightsailインスタンスが既に起動している
- SSH接続が設定済み
- プロジェクトが既にクローン済み

## デプロイ手順

### 1. ローカルでの変更をコミット

```bash
# 変更ファイルを確認
git status

# 変更をステージング
git add .

# コミット
git commit -m "Update: M5Stick data format support"

# リモートリポジトリにプッシュ
git push origin main
```

### 2. Lightsailインスタンスに接続

```bash
# Windows + WSLの場合
ssh -i ~/.ssh/LightsailDefaultKey-ap-northeast-1.pem ubuntu@35.79.71.96

# Mac/Linuxの場合
ssh -i /path/to/LightsailDefaultKey-ap-northeast-1.pem ubuntu@<パブリックIP>
```

### 3. プロジェクトディレクトリに移動

```bash
cd ~/iot-switchbot-dashboard
```

### 4. 最新のコードを取得

```bash
# 現在のブランチを確認
git branch

# 最新のコードをプル
git pull origin main

# 変更内容を確認
git log -1
```

### 5. 現在のコンテナを停止

```bash
# コンテナを停止（データは保持）
docker compose down

# 必要に応じてログを確認
docker compose logs
```

### 6. コンテナを再ビルド・起動

```bash
# イメージを再ビルドして起動
docker compose up -d --build

# 起動状態を確認
docker compose ps
```

### 7. デプロイ確認

```bash
# 全体のログを確認
docker compose logs -f

# 特定のサービスのログを確認
docker compose logs -f webserver

# ヘルスチェック
curl http://localhost:5000/health

# コンテナの状態を確認
docker ps
```

### 8. 動作テスト

#### ヘルスチェック
```bash
curl http://localhost:5000/health
```

期待されるレスポンス:
```json
{
  "status": "ok",
  "timestamp": "2026-01-16T12:00:00.000000"
}
```

#### デバイスリスト取得
```bash
curl http://localhost:5000/api/devices
```

#### センサーデータ送信テスト
```bash
curl -X POST http://localhost:5000/api/sensor-data \
  -H "Content-Type: application/json" \
  -d '{
    "m5stick": {
      "batteryVoltage": 3800,
      "batteryLevel": 85,
      "isCharging": false
    },
    "devices": [
      {
        "deviceName": "Device1",
        "temperature": 23.5,
        "humidity": 60,
        "battery": 95
      }
    ]
  }'
```

期待されるレスポンス:
```json
{
  "success": true,
  "saved": 1,
  "total": 1,
  "m5stick_saved": true,
  "timestamp": "2026-01-16T12:00:00.000000"
}
```

### 9. InfluxDBでデータ確認

```bash
# InfluxDB CLIでデータ確認（オプション）
docker compose exec influxdb influx query 'from(bucket:"switchbot") |> range(start: -1h) |> filter(fn: (r) => r._measurement == "M5Stick")'
```

または、ブラウザで`http://<パブリックIP>:8086`にアクセスしてData Explorerで確認。

### 10. Grafanaでダッシュボード確認

ブラウザで`http://<パブリックIP>:3000`にアクセスし、ダッシュボードでM5Stickのデータが表示されることを確認。

## ロールバック手順

デプロイに問題があった場合:

```bash
# 特定のコミットに戻る
git log  # コミットハッシュを確認
git checkout <previous-commit-hash>

# または直前のコミットに戻る
git reset --hard HEAD~1

# コンテナを再ビルド
docker compose down
docker compose up -d --build
```

## トラブルシューティング

### コンテナが起動しない

```bash
# ログを確認
docker compose logs

# コンテナを完全に削除して再作成
docker compose down -v
docker compose up -d --build
```

### ポートが使用中

```bash
# ポートを使用しているプロセスを確認
sudo lsof -i :5000

# プロセスを停止
sudo kill <PID>
```

### ディスク容量不足

```bash
# ディスク使用量を確認
df -h

# Dockerの未使用リソースを削除
docker system prune -a -f

# 古いイメージを削除
docker image prune -a -f
```

### メモリ不足

```bash
# メモリ使用量を確認
free -h

# 使用していないコンテナを停止
docker compose down
docker compose up -d
```

## 定期メンテナンス

### ログのローテーション

```bash
# ログファイルのサイズを確認
docker compose logs --tail=1000

# ログをクリア（必要に応じて）
docker compose down
docker compose up -d
```

### データバックアップ

```bash
# InfluxDBとGrafanaのデータをバックアップ
tar -czf backup-$(date +%Y%m%d-%H%M%S).tar.gz \
  docker/influxdb/data \
  docker/grafana/data

# バックアップを確認
ls -lh backup-*.tar.gz
```

### システムアップデート

```bash
# OSのアップデート
sudo apt update
sudo apt upgrade -y

# Dockerのアップデート
sudo apt install --only-upgrade docker-ce docker-ce-cli containerd.io -y

# 再起動（必要に応じて）
sudo reboot
```

## 緊急時の対応

### サービスの完全停止

```bash
docker compose down
```

### サービスの完全再起動

```bash
docker compose down
docker compose up -d --build --force-recreate
```

### データの完全クリア（注意）

```bash
# 全てのデータを削除
docker compose down -v
rm -rf docker/influxdb/data/*
rm -rf docker/grafana/data/*

# 再構築
docker compose up -d --build
```

## 監視とアラート

### ログ監視

```bash
# リアルタイムでログを監視
docker compose logs -f

# 特定のサービスのみ
docker compose logs -f webserver
```

### リソース監視

```bash
# コンテナのリソース使用状況
docker stats

# システム全体のリソース
htop
```

## 参考情報

- プロジェクト全体のドキュメント: [README.md](README.md)
- サンプルリクエスト: [sample_request.json](sample_request.json)
- AWSコンソール: [https://lightsail.aws.amazon.com/](https://lightsail.aws.amazon.com/)
