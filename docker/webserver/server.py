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

# デバイス一覧をメモリにキャッシュ
_device_cache = None


def load_device_list():
    """device_list.jsonを読み込んでキャッシュする"""
    global _device_cache
    if _device_cache is None:
        try:
            with open("device_list.json", "r", encoding="utf-8") as f:
                devices = json.load(f)
                # deviceNameをキーとした辞書に変換
                _device_cache = {device["deviceName"]: device for device in devices}
                logger.info(f"Loaded {len(_device_cache)} devices from device_list.json")
        except Exception as e:
            logger.error(f"Failed to load device list: {str(e)}")
            _device_cache = {}
    return _device_cache


def get_device_info(device_name: str):
    """デバイス名からデバイス情報を取得する"""
    device_list = load_device_list()
    return device_list.get(device_name)


def save_device_data(device_data: dict):
    """HTTPリクエストから受け取ったデバイスデータをInfluxDBに保存する"""

    device_name = device_data.get("deviceName")

    if not device_name:
        raise ValueError("deviceName is required")

    # device_list.jsonからデバイス情報を取得
    device_info = get_device_info(device_name)
    if not device_info:
        raise ValueError(f"Device not found in device_list.json: {device_name}")

    device_type = device_info.get("deviceType")
    device_id = device_info.get("deviceId")

    if device_type == "WoIOSensor":
        # 温度・湿度センサーのデータ
        humidity = device_data.get("humidity")
        temperature = device_data.get("temperature")
        battery = device_data.get("battery")

        if humidity is None or temperature is None:
            raise ValueError("humidity and temperature are required for WoIOSensor")

        p = (
            Point("WoIOSensor")
            .tag("device_name", device_name)
            .tag("device_id", device_id)
            .field("humidity", float(humidity))
            .field("temperature", float(temperature))
        )

        # バッテリー情報はオプション
        if battery is not None:
            p = p.field("battery", float(battery))

        write_api.write(bucket=bucket, record=p)
        logger.info(f"Saved WoIOSensor data: {device_name} (temp={temperature}, hum={humidity})")

    else:
        raise ValueError(f"Unsupported device type: {device_type}")


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
            devices = json.load(f)

        logger.info(f"Returned {len(devices)} devices")

        return jsonify({
            "devices": devices,
            "count": len(devices),
            "timestamp": datetime.now().isoformat()
        }), 200

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

    注: deviceIdとdeviceTypeはdevice_list.jsonから自動的に取得されます
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
