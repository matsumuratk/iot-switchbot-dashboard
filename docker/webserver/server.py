import json
import logging
import os
from datetime import datetime

from dotenv import load_dotenv
from flask import Flask, jsonify, request
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

# Logging
formatter = "[%(levelname)-8s] %(asctime)s %(funcName)s %(message)s"
logging.basicConfig(level=logging.INFO, format=formatter)
logger = logging.getLogger(__name__)

load_dotenv(".env")

# Flask
app = Flask(__name__)

# InfluxDB
INFLUXDB_TOKEN = os.environ["INFLUXDB_TOKEN"]
bucket = "switchbot"
client = InfluxDBClient(url="http://influxdb:8086", token=INFLUXDB_TOKEN, org="org")
write_api = client.write_api(write_options=SYNCHRONOUS)


def save_device_data(device_data: dict):
    """HTTPリクエストから受け取ったデバイスデータをInfluxDBに保存する"""

    device_name = device_data.get("deviceName")
    humidity = device_data.get("humidity")
    temperature = device_data.get("temperature")
    battery = device_data.get("battery")

    if not device_name:
        raise ValueError("deviceName is required")

    if humidity is None or temperature is None:
        raise ValueError("humidity and temperature are required")

    # 全てのデータを温湿度センサーとして保存
    p = (
        Point("WoIOSensor")
        .tag("device_name", device_name)
        .field("humidity", float(humidity))
        .field("temperature", float(temperature))
    )

    # バッテリー情報はオプション
    if battery is not None:
        p = p.field("battery", float(battery))

    write_api.write(bucket=bucket, record=p)
    logger.info(f"Saved sensor data: {device_name} (temp={temperature}, hum={humidity}, battery={battery})")


@app.route("/health", methods=["GET"])
def health_check():
    """ヘルスチェックエンドポイント"""
    return jsonify({"status": "ok", "timestamp": datetime.now().isoformat()}), 200


@app.route("/api/devices", methods=["GET"])
def get_devices():
    """デバイス一覧を返すエンドポイント

    device_list.jsonファイルの内容を返す
    """
    try:
        device_file_path = "device_list.json"

        if not os.path.exists(device_file_path):
            logger.error(f"Device list file not found: {device_file_path}")
            return jsonify({"error": "Device list file not found"}), 404

        with open(device_file_path, "r", encoding="utf-8") as f:
            device_list = json.load(f)

        logger.info(f"Returned device list")

        # device_list.jsonをそのまま返す
        return jsonify(device_list), 200

    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {str(e)}")
        return jsonify({"error": "Invalid JSON in device list file"}), 500
    except Exception as e:
        logger.error(f"Error reading device list: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/sensor-data", methods=["POST"])
def receive_sensor_data():
    """センサーデータを受信するエンドポイント

    リクエストボディの形式:
    {
        "devices": [
            {
                "deviceName": "11_thermohygrometer",
                "temperature": 23.5,
                "humidity": 55.0,
                "battery": 100
            },
            {
                "deviceName": "12_thermohygrometer",
                "temperature": 24.2,
                "humidity": 52.3,
                "battery": 95
            }
        ]
    }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        devices = data.get("devices")
        if not devices:
            return jsonify({"error": "devices field is required"}), 400

        if not isinstance(devices, list):
            return jsonify({"error": "devices must be an array"}), 400

        # 各デバイスのデータを保存
        saved_count = 0
        errors = []

        for i, device in enumerate(devices):
            try:
                save_device_data(device)
                saved_count += 1
            except ValueError as e:
                error_msg = f"Device {i}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
            except Exception as e:
                error_msg = f"Device {i}: Unexpected error - {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)

        response = {
            "success": True,
            "saved": saved_count,
            "total": len(devices),
            "timestamp": datetime.now().isoformat()
        }

        if errors:
            response["errors"] = errors

        logger.info(f"Processed {saved_count}/{len(devices)} devices")

        return jsonify(response), 200

    except Exception as e:
        logger.error(f"Request processing error: {str(e)}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    # 0.0.0.0でリッスンしてDockerコンテナ外からもアクセス可能に
    app.run(host="0.0.0.0", port=5000, debug=False)
