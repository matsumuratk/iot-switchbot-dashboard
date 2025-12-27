#!/bin/bash

# HTTPサーバーにセンサーデータを送信するサンプルスクリプト

# サーバーURL（ローカル環境の場合）
SERVER_URL="http://35.79.71.96:5000"

# ヘルスチェック
echo "=== Health Check ==="
curl -X GET "${SERVER_URL}/health"
echo -e "\n"

# デバイスリスト取得
echo "=== Get Device List ==="
curl -X GET "${SERVER_URL}/api/devices"
echo -e "\n"

# センサーデータ送信
echo "=== Sending Sensor Data ==="
curl -X POST "${SERVER_URL}/api/sensor-data" \
  -H "Content-Type: application/json" \
  -d @sample_request.json
echo -e "\n"
