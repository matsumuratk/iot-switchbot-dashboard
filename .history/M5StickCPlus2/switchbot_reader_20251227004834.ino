#include <M5StickCPlus2.h>
#include <BLEDevice.h>
#include <BLEUtils.h>
#include <BLEScan.h>
#include <BLEAdvertisedDevice.h>

// 対応するSwitchBot温湿度計のMACアドレスリスト
const char* TARGET_MACS[] = {
  "d4:0e:84:86:51:16",  // デバイス1
  "dd:42:06:46:2f:81",  // デバイス2
  // "yy:yy:yy:yy:yy:yy"   // デバイス3（追加する場合）
};
const int NUM_DEVICES = 2; // 現在のデバイス数（増やす場合は変更）

const unsigned long UPDATE_INTERVAL = 600000; // 10分
const int MAX_RETRY = 3; // 最大再試行回数

// デバイス情報を保持する構造体
struct DeviceData {
  String mac;
  String name;
  float temperature;
  int humidity;
  int battery;
  bool dataFound;
  unsigned long lastUpdate;
};

DeviceData devices[3]; // 最大3台まで対応
int currentDeviceIndex = 0; // 現在表示中のデバイス
unsigned long lastScanTime = 0;
BLEScan* pBLEScan;
int scanCount = 0;

bool parseSwitchBotManufacturerData(uint8_t* data, size_t length, DeviceData& device) {
  if (length < 13) return false;
  
  // SwitchBot Company ID確認 (0x0969)
  if (data[0] != 0x69 || data[1] != 0x09) return false;
  
  // 温度計算
  int tempRaw = (data[9] << 8) | data[10];
  float tempValue = (tempRaw / 10.0) - 29.0;
  
  // 温度の範囲チェック（-40℃〜80℃が妥当な範囲）
  if (tempValue < -40.0 || tempValue > 80.0) {
    Serial.print("  Invalid temperature: ");
    Serial.print(tempValue);
    Serial.println("C - Will retry");
    return false;
  }
  
  device.temperature = tempValue;
  
  // 湿度計算
  device.humidity = data[11] - 90;
  
  // 湿度の範囲チェック（0%〜100%）
  if (device.humidity < 0 || device.humidity > 100) {
    Serial.print("  Invalid humidity: ");
    Serial.print(device.humidity);
    Serial.println("% - Will retry");
    return false;
  }
  
  // バッテリー
  device.battery = data[12] & 0x7F;
  
  Serial.print("  Temp: ");
  Serial.print(device.temperature, 1);
  Serial.print("C, Humid: ");
  Serial.print(device.humidity);
  Serial.print("%, Bat: ");
  Serial.print(device.battery);
  Serial.println("%");
  
  return true;
}

class MyAdvertisedDeviceCallbacks: public BLEAdvertisedDeviceCallbacks {
  void onResult(BLEAdvertisedDevice advertisedDevice) {
    String address = advertisedDevice.getAddress().toString().c_str();
    address.toLowerCase();
    
    // 登録されているデバイスか確認
    for (int i = 0; i < NUM_DEVICES; i++) {
      String targetMac = devices[i].mac;
      targetMac.toLowerCase();
      
      if (address == targetMac) {
        Serial.print("[Device ");
        Serial.print(i + 1);
        Serial.print("] ");
        Serial.print(address);
        Serial.println(" <- TARGET!");
        
        // Manufacturer Dataを取得
        if (advertisedDevice.haveManufacturerData()) {
          String mfgData = advertisedDevice.getManufacturerData();
          uint8_t* data = (uint8_t*)mfgData.c_str();
          
          if (parseSwitchBotManufacturerData(data, mfgData.length(), devices[i])) {
            devices[i].dataFound = true;
            devices[i].lastUpdate = millis();
          }
        }
        break;
      }
    }
  }
};

void setup() {
  auto cfg = M5.config();
  StickCP2.begin(cfg);
  
  StickCP2.Display.setRotation(1);
  StickCP2.Display.setTextSize(2);
  StickCP2.Display.fillScreen(BLACK);
  
  Serial.begin(9600);
  delay(2000);
  
  Serial.println("\n\n========================================");
  Serial.println("SwitchBot Multi-Device Scanner");
  Serial.println("========================================");
  Serial.print("Number of devices: ");
  Serial.println(NUM_DEVICES);
  
  // デバイス情報を初期化
  for (int i = 0; i < NUM_DEVICES; i++) {
    devices[i].mac = String(TARGET_MACS[i]);
    devices[i].name = "Device " + String(i + 1);
    devices[i].temperature = 0.0;
    devices[i].humidity = 0;
    devices[i].battery = 0;
    devices[i].dataFound = false;
    devices[i].lastUpdate = 0;
    
    Serial.print("Device ");
    Serial.print(i + 1);
    Serial.print(": ");
    Serial.println(devices[i].mac);
  }
  Serial.println("========================================\n");
  
  StickCP2.Display.setCursor(10, 10);
  StickCP2.Display.setTextColor(WHITE);
  StickCP2.Display.println("SwitchBot");
  StickCP2.Display.setCursor(10, 30);
  StickCP2.Display.print("Multi(");
  StickCP2.Display.print(NUM_DEVICES);
  StickCP2.Display.println(")");
  
  // BLE初期化
  Serial.println("Initializing BLE...");
  BLEDevice::init("");
  Serial.println("BLE initialized");
  
  pBLEScan = BLEDevice::getScan();
  pBLEScan->setAdvertisedDeviceCallbacks(new MyAdvertisedDeviceCallbacks());
  pBLEScan->setActiveScan(true);
  pBLEScan->setInterval(100);
  pBLEScan->setWindow(99);
  
  Serial.println("Setup complete!");
  Serial.println("BtnA: Switch device");
  Serial.println("BtnB: Manual scan\n");
  
  delay(2000);
}

void performScan() {
  // スキャン前に全デバイスのdataFoundをリセット
  for (int i = 0; i < NUM_DEVICES; i++) {
    devices[i].dataFound = false;
  }
  
  // 5秒間スキャン
  BLEScanResults* foundDevices = pBLEScan->start(5, false);
  pBLEScan->clearResults();
}

void scanAndUpdate() {
  scanCount++;
  
  Serial.println("\n========================================");
  Serial.print("SCAN #");
  Serial.println(scanCount);
  Serial.println("========================================");
  
  StickCP2.Display.fillScreen(BLACK);
  StickCP2.Display.setCursor(10, 10);
  StickCP2.Display.setTextColor(YELLOW);
  StickCP2.Display.println("Scanning");
  StickCP2.Display.setCursor(10, 40);
  StickCP2.Display.setTextSize(1);
  StickCP2.Display.print("All ");
  StickCP2.Display.print(NUM_DEVICES);
  StickCP2.Display.println(" devices");
  
  // 初回スキャン
  performScan();
  
  // 再試行ループ
  int retryCount = 0;
  while (retryCount < MAX_RETRY) {
    // 取得失敗したデバイスをチェック
    bool needRetry = false;
    Serial.print("Check: ");
    for (int i = 0; i < NUM_DEVICES; i++) {
      if (!devices[i].dataFound) {
        needRetry = true;
        Serial.print("Device ");
        Serial.print(i + 1);
        Serial.print(" missing, ");
      }
    }
    
    if (!needRetry) {
      Serial.println("All devices OK!");
      break;
    }
    
    // 再スキャン
    retryCount++;
    Serial.println();
    Serial.print(">>> Retry #");
    Serial.print(retryCount);
    Serial.println(" <<<");
    
    StickCP2.Display.fillScreen(BLACK);
    StickCP2.Display.setCursor(10, 10);
    StickCP2.Display.setTextColor(ORANGE);
    StickCP2.Display.println("Retrying");
    StickCP2.Display.setCursor(10, 40);
    StickCP2.Display.setTextSize(1);
    StickCP2.Display.print("Attempt ");
    StickCP2.Display.print(retryCount);
    StickCP2.Display.print("/");
    StickCP2.Display.println(MAX_RETRY);
    
    delay(1000); // 1秒待機
    performScan();
  }
  
  lastScanTime = millis();
  
  // 最終結果を表示
  int foundCount = 0;
  for (int i = 0; i < NUM_DEVICES; i++) {
    if (devices[i].dataFound) {
      foundCount++;
    }
  }
  
  Serial.print("Final result: ");
  Serial.print(foundCount);
  Serial.print("/");
  Serial.print(NUM_DEVICES);
  Serial.println(" devices found");
  
  if (foundCount < NUM_DEVICES) {
    Serial.println("WARNING: Some devices not found or have invalid data");
  }
  Serial.println();
}

void displayData() {
  StickCP2.Display.fillScreen(BLACK);
  
  DeviceData& device = devices[currentDeviceIndex];
  
  // デバイス番号表示
  StickCP2.Display.setTextSize(1);
  StickCP2.Display.setCursor(5, 5);
  StickCP2.Display.setTextColor(WHITE);
  StickCP2.Display.print("Device ");
  StickCP2.Display.print(currentDeviceIndex + 1);
  StickCP2.Display.print("/");
  StickCP2.Display.println(NUM_DEVICES);
  
  if (device.dataFound) {
    // 温度
    StickCP2.Display.setCursor(10, 25);
    StickCP2.Display.setTextColor(ORANGE);
    StickCP2.Display.setTextSize(2);
    StickCP2.Display.println("Temp:");
    StickCP2.Display.setCursor(10, 45);
    StickCP2.Display.setTextSize(3);
    StickCP2.Display.setTextColor(RED);
    StickCP2.Display.printf("%.1fC", device.temperature);
    
    // 湿度
    StickCP2.Display.setCursor(10, 75);
    StickCP2.Display.setTextSize(2);
    StickCP2.Display.setTextColor(CYAN);
    StickCP2.Display.println("Humid:");
    StickCP2.Display.setCursor(10, 95);
    StickCP2.Display.setTextSize(3);
    StickCP2.Display.setTextColor(BLUE);
    StickCP2.Display.printf("%d%%", device.humidity);
    
    // バッテリーと次回更新
    unsigned long elapsed = millis() - lastScanTime;
    unsigned long remaining = UPDATE_INTERVAL - elapsed;
    int remainingSec = remaining / 1000;
    
    StickCP2.Display.setCursor(5, 125);
    StickCP2.Display.setTextSize(1);
    StickCP2.Display.setTextColor(GREEN);
    StickCP2.Display.printf("Bat:%d%%", device.battery);
    
    StickCP2.Display.setCursor(70, 125);
    StickCP2.Display.setTextColor(WHITE);
    StickCP2.Display.printf("Next:%ds", remainingSec);
  } else {
    StickCP2.Display.setCursor(10, 50);
    StickCP2.Display.setTextColor(RED);
    StickCP2.Display.setTextSize(2);
    StickCP2.Display.println("No Data");
    
    // MACアドレスの下8桁を表示
    StickCP2.Display.setCursor(10, 80);
    StickCP2.Display.setTextSize(1);
    StickCP2.Display.setTextColor(WHITE);
    String shortMac = device.mac.substring(device.mac.length() - 8);
    StickCP2.Display.println(shortMac);
  }
  
  // ボタンヘルプ
  StickCP2.Display.setCursor(5, 135);
  StickCP2.Display.setTextSize(1);
  StickCP2.Display.setTextColor(DARKGREY);
  StickCP2.Display.print("A:Next B:Scan");
}

void loop() {
  StickCP2.update();
  
  unsigned long currentMillis = millis();
  
  // BtnA: 次のデバイスに切り替え
  if (StickCP2.BtnA.wasPressed()) {
    if (NUM_DEVICES > 1) {
      currentDeviceIndex = (currentDeviceIndex + 1) % NUM_DEVICES;
      Serial.print("Switched to device ");
      Serial.println(currentDeviceIndex + 1);
      displayData();
    }
  }
  
  // BtnB: 手動スキャン
  if (StickCP2.BtnB.wasPressed()) {
    Serial.println("Manual scan triggered");
    scanAndUpdate();
  }
  
  // 自動スキャン（1分間隔）
  if (lastScanTime == 0 || (currentMillis - lastScanTime >= UPDATE_INTERVAL)) {
    scanAndUpdate();
  }
  
  displayData();
  delay(100);
}