# Switchbot-dashboard

Dashboard for Switchbot using InfluxDB and Grafana.

## Features

- **SwitchBot API Integration**: Automatically fetch sensor data from SwitchBot devices (polling mode)
- **HTTP REST API**: Receive sensor data from external sources via HTTP POST (push mode)
- **InfluxDB**: Store time-series sensor data
- **Grafana**: Visualize sensor data with dashboards

## Architecture

- **python**: SwitchBot API polling service (scheduled every 5 minutes)
- **webserver**: HTTP REST API server for receiving sensor data
- **influxdb**: Time-series database
- **grafana**: Dashboard visualization

## Basic usage

1.Write Switchbot API key and other information in the `.env` file.
note) Enter `INFLUXDB_TOKEN` after completing step 2.

```
SWITCHBOT_ACCESS_TOKEN=
SWITCHBOT_SECRET=
INFLUXDB_TOKEN=
```

2.Start docker.

```
$ docker-compose up -d --build
```

Obtain `INFLUXDB_TOKEN` from `/docker/influxdb/config/influx-configs` and write it in the `.env` file.

3.Watch logs.

```
$ docker-compose logs -f
```

## HTTP REST API Usage

The webserver component provides REST API endpoints to receive sensor data.

### Start webserver

```bash
docker-compose up -d webserver
```

### Endpoints

#### Health Check
```bash
GET http://localhost:5000/health
```

Response:
```json
{
  "status": "ok",
  "timestamp": "2025-12-26T14:48:33.509318"
}
```

#### Get Device List
```bash
GET http://localhost:5000/api/devices
```

Response:
```json
{
  "devices": [
    {
      "deviceId": "CA5F46463F21",
      "deviceName": "11_thermohygrometer",
      "deviceType": "WoIOSensor",
      "enableCloudService": true,
      "hubDeviceId": "D879924895A8"
    },
    ...
  ],
  "count": 6,
  "timestamp": "2025-12-26T15:05:03.622423"
}
```

#### Send Sensor Data
```bash
POST http://localhost:5000/api/sensor-data
Content-Type: application/json
```

Request body format (see [sample_request.json](sample_request.json)):
```json
{
  "devices": [
    {
      "deviceName": "11_thermohygrometer",
      "temperature": 23.5,
      "humidity": 55.0,
      "battery": 100
    }
  ]
}
```

**Note**: `deviceId` and `deviceType` are automatically retrieved from `device_list.json` based on `deviceName`.

Response:
```json
{
  "success": true,
  "saved": 1,
  "total": 1,
  "timestamp": "2025-12-26T14:50:00.123456"
}
```

### Test with curl

```bash
# Health check
curl http://localhost:5000/health

# Get device list
curl http://localhost:5000/api/devices

# Send sensor data
curl -X POST http://localhost:5000/api/sensor-data \
  -H "Content-Type: application/json" \
  -d @sample_request.json

# Or use the sample script
chmod +x sample_curl.sh
./sample_curl.sh
```


scp -i LightsailDefaultKey-ap-northeast-1.pem -r ./app/main.py ec2-user@52.194.211.20:main.py

AWS LightSail

InfluxDB
http://52.194.211.20:8086
username
password

Grafana
http://52.194.211.20:3000
admin
password

