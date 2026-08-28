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


def save_m5stick_data(m5stick_data: dict):
    """M5StickのデータをInfluxDBに保存する"""
    
    battery_voltage = m5stick_data.get("batteryVoltage")
    battery_level = m5stick_data.get("batteryLevel")
    is_charging = m5stick_data.get("isCharging")

    if battery_voltage is None:
        raise ValueError("batteryVoltage is required")
    
    # M5Stickのデータを保存
    p = Point("M5Stick").field("batteryVoltage", float(battery_voltage))
    
    if battery_level is not None:
        p = p.field("batteryLevel", float(battery_level))
    
    if is_charging is not None:
        p = p.field("isCharging", bool(is_charging))
    
    write_api.write(bucket=bucket, record=p)
    logger.info(f"Saved M5Stick data: voltage={battery_voltage}, level={battery_level}, charging={is_charging}")


def save_m5stick_extra_sensors(weight, ds18b20_temperature):
    """M5Stick本体に追加されたセンサー（HX711重量センサー、DS18B20温度センサー）のデータをInfluxDBに保存する

    どちらもオプション。呼び出し側は少なくとも一方がNoneでないときのみ呼び出すこと。
    """

    p = Point("M5Stick")

    if weight is not None:
        p = p.field("weight", float(weight))

    if ds18b20_temperature is not None:
        p = p.field("ds18b20Temperature", float(ds18b20_temperature))

    write_api.write(bucket=bucket, record=p)
    logger.info(f"Saved M5Stick extra sensor data: weight={weight}, ds18b20Temperature={ds18b20_temperature}")


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
        ],
        "weight": 123.4,             // HX711重量センサー(g)。任意
        "ds18b20Temperature": 25.3   // DS18B20温度センサー(℃)。任意
    }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        # M5Stickのデータを保存
        m5stick_saved = False
        m5stick_error = None
        m5stick_data = data.get("m5stick")
        if m5stick_data:
            try:
                save_m5stick_data(m5stick_data)
                m5stick_saved = True
            except ValueError as e:
                m5stick_error = f"M5Stick: {str(e)}"
                logger.error(m5stick_error)
            except Exception as e:
                m5stick_error = f"M5Stick: Unexpected error - {str(e)}"
                logger.error(m5stick_error)

        # M5Stick本体の追加センサー（重量・DS18B20温度）を保存
        # どちらも任意項目。存在しない場合は何もしない（エラーにしない）
        extra_sensors_saved = False
        extra_sensors_error = None
        weight = data.get("weight")
        ds18b20_temperature = data.get("ds18b20Temperature")
        if weight is not None or ds18b20_temperature is not None:
            try:
                save_m5stick_extra_sensors(weight, ds18b20_temperature)
                extra_sensors_saved = True
            except Exception as e:
                extra_sensors_error = f"M5Stick extra sensors: Unexpected error - {str(e)}"
                logger.error(extra_sensors_error)

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
            "m5stick_saved": m5stick_saved,
            "extra_sensors_saved": extra_sensors_saved,
            "timestamp": datetime.now().isoformat()
        }

        if m5stick_error:
            if "errors" not in response:
                response["errors"] = []
            response["errors"].append(m5stick_error)

        if extra_sensors_error:
            if "errors" not in response:
                response["errors"] = []
            response["errors"].append(extra_sensors_error)

        if errors:
            if "errors" not in response:
                response["errors"] = []
            response["errors"].extend(errors)

        logger.info(f"Processed {saved_count}/{len(devices)} devices")

        return jsonify(response), 200

    except Exception as e:
        logger.error(f"Request processing error: {str(e)}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    # 0.0.0.0でリッスンしてDockerコンテナ外からもアクセス可能に
    app.run(host="0.0.0.0", port=5000, debug=False)
