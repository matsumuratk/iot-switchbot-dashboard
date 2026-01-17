# Grafana Flux クエリ集

このファイルには、SwitchBot温湿度センサーダッシュボード用のFluxクエリが含まれています。

## 基本設定

- **Bucket**: `switchbot`
- **Measurement**: `WoIOSensor`
- **Tags**: `device_name` (デバイス名)
- **Fields**: `temperature` (温度), `humidity` (湿度), `battery` (バッテリー残量)

---

## 1. 現在の温度（最新値）

```flux
from(bucket: "switchbot")
  |> range(start: -1h)
  |> filter(fn: (r) => r["_field"] == "temperature")
  |> filter(fn: (r) => r["device_name"] == "${device_name}")
  |> last()
```

**説明**: 指定したデバイスの最新の温度を取得します。
**変数**: `${device_name}` - デバイス名（例: "11_thermohygrometer"）

---

## 2. 現在の湿度（最新値）

```flux
from(bucket: "switchbot")
  |> range(start: -1h)
  |> filter(fn: (r) => r["_measurement"] == "WoIOSensor")
  |> filter(fn: (r) => r["_field"] == "humidity")
  |> filter(fn: (r) => r["device_name"] == "${device_name}")
  |> last()
```

**説明**: 指定したデバイスの最新の湿度を取得します。
**変数**: `${device_name}` - デバイス名

---

## 3. バッテリー残量（最新値）

```flux
from(bucket: "switchbot")
  |> range(start: -1h)
  |> filter(fn: (r) => r["_measurement"] == "WoIOSensor")
  |> filter(fn: (r) => r["_field"] == "battery")
  |> filter(fn: (r) => r["device_name"] == "${device_name}")
  |> last()
```

**説明**: 指定したデバイスの最新のバッテリー残量を取得します。
**変数**: `${device_name}` - デバイス名

---

## 4. 温度の時系列グラフ（複数デバイス対応）

```flux
from(bucket: "switchbot")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["_measurement"] == "WoIOSensor")
  |> filter(fn: (r) => r["_field"] == "temperature")
  |> aggregateWindow(every: v.windowPeriod, fn: mean, createEmpty: false)
  |> yield(name: "mean")
```

**説明**: すべてのデバイスの温度を時系列グラフで表示します。
**特徴**:
- `v.timeRangeStart` / `v.timeRangeStop` でGrafanaの時間範囲を自動適用
- `v.windowPeriod` で自動的にデータを集約（ズームレベルに応じて調整）

---

## 5. 湿度の時系列グラフ（複数デバイス対応）

```flux
from(bucket: "switchbot")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["_measurement"] == "WoIOSensor")
  |> filter(fn: (r) => r["_field"] == "humidity")
  |> aggregateWindow(every: v.windowPeriod, fn: mean, createEmpty: false)
  |> yield(name: "mean")
```

**説明**: すべてのデバイスの湿度を時系列グラフで表示します。

---

## 6. 特定デバイスの温度時系列

```flux
from(bucket: "switchbot")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["_measurement"] == "WoIOSensor")
  |> filter(fn: (r) => r["_field"] == "temperature")
  |> filter(fn: (r) => r["device_name"] == "${device_name}")
  |> aggregateWindow(every: v.windowPeriod, fn: mean, createEmpty: false)
  |> yield(name: "mean")
```

**説明**: 特定のデバイスの温度の時系列データを表示します。
**変数**: `${device_name}` - デバイス名

---

## 6-2. 特定デバイスの温度と湿度（デュアルY軸）

Grafanaで左軸に温度、右軸に湿度を表示するには、2つのクエリを使用します。

### クエリA（温度 - 左軸用）

```flux
from(bucket: "switchbot")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["_measurement"] == "WoIOSensor")
  |> filter(fn: (r) => r["_field"] == "temperature")
  |> filter(fn: (r) => r["device_name"] == "${device_name}")
  |> aggregateWindow(every: v.windowPeriod, fn: mean, createEmpty: false)
  |> yield(name: "temperature")
```

### クエリB（湿度 - 右軸用）

```flux
from(bucket: "switchbot")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["_measurement"] == "WoIOSensor")
  |> filter(fn: (r) => r["_field"] == "humidity")
  |> filter(fn: (r) => r["device_name"] == "${device_name}")
  |> aggregateWindow(every: v.windowPeriod, fn: mean, createEmpty: false)
  |> yield(name: "humidity")
```

**Grafanaパネル設定手順**:

1. **パネルの作成**
   - 「Add panel」→「Add visualization」をクリック
   - Visualization type: **Time series** を選択

2. **クエリの追加**
   - Query A に温度のクエリを設定
   - 「+ Query」をクリックして Query B に湿度のクエリを設定

3. **Field overrides（フィールド上書き）の設定**
   - 右側の設定パネルで「**Overrides**」タブを選択
   
   **温度の設定（左軸）:**
   - 「**Add field override**」をクリック
   - 「**Fields with name**」を選択し、`temperature` を入力
   - 「**Add override property**」から以下を設定:
     - `Standard options > Unit` → `Temperature > Celsius (°C)`
     - `Standard options > Display name` → `温度`
     - `Axis > Placement` → **`Left`** ⬅️ 重要！
     - `Graph styles > Line width` → `2`
     - `Standard options > Color scheme` → 赤系の色（例: `Red` または `#FF6B6B`）

   **湿度の設定（右軸）:**
   - 「**Add field override**」をクリック
   - 「**Fields with name**」を選択し、`humidity` を入力
   - 「**Add override property**」から以下を設定:
     - `Standard options > Unit` → `Misc > Humidity (%H)`
     - `Standard options > Display name` → `湿度`
     - `Axis > Placement` → **`Right`** ⬅️ 重要！
     - `Graph styles > Line width` → `2`
     - `Standard options > Color scheme` → 青系の色（例: `Blue` または `#4ECDC4`）
     - `Standard options > Min` → `0`
     - `Standard options > Max` → `100`

4. **パネルオプション**
   - 右側パネルの「**Panel options**」セクション:
     - `Title` → `温度と湿度`
   
   - 「**Legend**」セクション:
     - `Visibility` → **`Show legend`** を有効化
     - `Placement` → `Bottom`
     - `Values` → `Last` と `Mean` にチェック

5. **保存**
   - 右上の「**Apply**」をクリックしてパネルを保存

### 📊 完成イメージ

```
グラフ:
温度(°C)                                      湿度(%)
30 ┤                                         100
25 ┤     ╱─╲                                  80
20 ┤   ╱─   ─╲    [赤線: 温度]   [青線: 湿度]   60
15 ┤ ╱─       ─╲╱─                             40
10 ┤─           ╲                              20
   └─────────────────────────────────────────  0
   0h   6h   12h  18h  24h
```

**説明**: 
- 温度を左軸（赤系）、湿度を右軸（青系）に表示
- 同一グラフで温度と湿度の相関関係を視覚的に確認可能
- 各軸が独立したスケールで表示されるため、両方の値の変化が見やすい
- 変数 `${device_name}` でデバイスを選択

**変数**: `${device_name}` - デバイス名

---

## 7. 全デバイスの最新値テーブル

```flux
from(bucket: "switchbot")
  |> range(start: -1h)
  |> filter(fn: (r) => r["_measurement"] == "WoIOSensor")
  |> filter(fn: (r) => r["_field"] == "temperature" or r["_field"] == "humidity" or r["_field"] == "battery")
  |> last()
  |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
  |> keep(columns: ["_time", "device_name", "temperature", "humidity", "battery"])
```

**説明**: すべてのデバイスの最新の温度、湿度、バッテリー残量をテーブル形式で表示します。
**特徴**:
- `pivot()` で行データを列形式に変換
- 見やすいテーブル形式で表示

---

## 8. 統計情報（最小・最大・平均）

### 温度の統計

```flux
from(bucket: "switchbot")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["_measurement"] == "WoIOSensor")
  |> filter(fn: (r) => r["_field"] == "temperature")
  |> filter(fn: (r) => r["device_name"] == "${device_name}")
  |> aggregateWindow(every: 1h, fn: mean, createEmpty: false)
  |> yield(name: "mean")
```

### 最小温度

```flux
from(bucket: "switchbot")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["_measurement"] == "WoIOSensor")
  |> filter(fn: (r) => r["_field"] == "temperature")
  |> filter(fn: (r) => r["device_name"] == "${device_name}")
  |> min()
```

### 最大温度

```flux
from(bucket: "switchbot")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["_measurement"] == "WoIOSensor")
  |> filter(fn: (r) => r["_field"] == "temperature")
  |> filter(fn: (r) => r["device_name"] == "${device_name}")
  |> max()
```

### 平均温度

```flux
from(bucket: "switchbot")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["_measurement"] == "WoIOSensor")
  |> filter(fn: (r) => r["_field"] == "temperature")
  |> filter(fn: (r) => r["device_name"] == "${device_name}")
  |> mean()
```

---

## 9. デバイス名の一覧（変数用）

### 9-1. すべてのデバイス名を取得

```flux
import "influxdata/influxdb/schema"

schema.tagValues(
  bucket: "switchbot",
  tag: "device_name",
  predicate: (r) => r._measurement == "WoIOSensor",
  start: -30d
)
```

**説明**: 過去30日間に記録されたすべてのデバイス名を取得します。

### 9-2. 特定のsuffixを持つデバイスのみ取得（推奨）

**方法1: strings.hasSuffix() を使用（推奨）**

```flux
import "influxdata/influxdb/schema"
import "strings"

schema.tagValues(
  bucket: "switchbot",
  tag: "device_name",
  predicate: (r) => r._measurement == "WoIOSensor",
  start: -30d
)
  |> filter(fn: (r) => strings.hasSuffix(v: r._value, suffix: "thermohygrometer"))
```

**方法2: 正規表現を使用**

```flux
import "influxdata/influxdb/schema"

schema.tagValues(
  bucket: "switchbot",
  tag: "device_name",
  predicate: (r) => r._measurement == "WoIOSensor",
  start: -30d
)
  |> filter(fn: (r) => r._value =~ /thermohygrometer$/)
```

**説明**: 
- デバイス名が `thermohygrometer` で終わるものだけを選択肢に表示
- 例: `11_thermohygrometer`, `12_thermohygrometer` などが表示される
- 他のデバイスタイプ（例: `contact_sensor`, `plug` など）は除外される

**用途**: Grafanaの変数（Variable）として使用し、ドロップダウンでデバイスを選択可能にします。

### 📝 Grafana変数の設定方法（詳細手順）

#### ステップ1: ダッシュボード設定を開く

1. ダッシュボードの右上の **⚙️（歯車アイコン）** をクリック
2. 「Settings」を選択

#### ステップ2: 変数を作成

1. 左サイドバーの **Variables** タブをクリック
2. **New variable** または **Add variable** ボタンをクリック

#### ステップ3: 変数の基本設定

以下の項目を設定します：

| 設定項目 | 設定値 | 説明 |
|---------|--------|------|
| **Name** | `device_name` | クエリで `${device_name}` として参照される名前 |
| **Type** | `Query` | データソースからクエリで値を取得 |
| **Label** | `デバイス` または `Device` | ダッシュボード上部に表示される名称 |
| **Description** | （任意）`センサーデバイスを選択` | ホバー時に表示される説明文 |

#### ステップ4: データソース設定

| 設定項目 | 設定値 |
|---------|--------|
| **Data source** | `InfluxDB` | あなたのInfluxDBデータソースを選択 |
| **Query type** | `Flux` | クエリ言語としてFluxを選択 |

#### ステップ5: クエリの入力

**Query** フィールドに以下のFluxクエリを入力：

```flux
import "influxdata/influxdb/schema"

schema.tagValues(
  bucket: "switchbot",
  tag: "device_name",
  predicate: (r) => r._measurement == "WoIOSensor",
  start: -30d
)
```

#### ステップ6: 選択オプションの設定

| 設定項目 | 設定値 | 説明 |
|---------|--------|------|
| **Multi-value** | ☐（無効） | 複数選択を許可する場合は有効化 |
| **Include All option** | ☑（有効推奨） | 「All」オプションを追加し全デバイス表示可能に |
| **Custom all value** | （空欄または `.*`） | Allを選択した際の値（正規表現使用可） |

#### ステップ7: リフレッシュ設定

| 設定項目 | 設定値 | 説明 |
|---------|--------|------|
| **Refresh** | `On dashboard load` | ダッシュボード読み込み時に変数を更新 |

**その他のオプション:**
- `On time range change`: 時間範囲変更時に更新
- `Never`: 手動更新のみ

#### ステップ8: プレビューと保存

1. 下部の **Preview of values** で取得されるデバイス名一覧を確認
2. 期待通りのデバイス名が表示されていることを確認
3. **Apply** または **Save** ボタンをクリック
4. ダッシュボード設定画面の右上の **Save dashboard** をクリック

#### ステップ9: パネルで変数を使用

パネルのクエリで以下のように変数を参照：

```flux
from(bucket: "switchbot")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["_measurement"] == "WoIOSensor")
  |> filter(fn: (r) => r["_field"] == "temperature")
  |> filter(fn: (r) => r["device_name"] == "${device_name}")
  |> aggregateWindow(every: v.windowPeriod, fn: mean, createEmpty: false)
```

**重要ポイント:**
- 変数は `${variable_name}` の形式で参照
- クエリ内で文字列として展開されるため、ダブルクォートで囲む必要がある
- 複数選択を有効にした場合、`=~ /${device_name}/` のような正規表現を使用

### 🎯 複数デバイス選択を許可する場合の設定

Multi-valueを有効にした場合のクエリ例：

```flux
from(bucket: "switchbot")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["_measurement"] == "WoIOSensor")
  |> filter(fn: (r) => r["_field"] == "temperature")
  |> filter(fn: (r) => r["device_name"] =~ /^(${device_name:pipe})$/)
  |> aggregateWindow(every: v.windowPeriod, fn: mean, createEmpty: false)
```

**説明:**
- `${device_name:pipe}` は複数選択時に `device1|device2|device3` のような形式に展開
- `=~` は正規表現マッチ演算子

### ✅ 動作確認

1. ダッシュボード上部にドロップダウンメニューが表示される
2. デバイス名が選択肢として表示される
3. デバイスを選択すると、すべてのパネルが自動的に更新される
4. 「All」を選択すると、全デバイスのデータが表示される

### 🔧 トラブルシューティング

**Q: デバイス名が表示されない**
- A: InfluxDBにデータが存在するか確認。過去30日間のデータがない場合は `start: -30d` を `start: -90d` などに変更

**Q: 変数が更新されない**
- A: Refreshオプションを確認。必要に応じて手動で変数を更新（変数の右側の🔄アイコンをクリック）

**Q: 「All」オプションで全デバイスが表示されない**
- A: クエリで `==` ではなく `=~` 演算子を使用し、正規表現でマッチさせる必要がある

### 📺 選択中のデバイス名をダッシュボードに表示する方法

ダッシュボード上で現在選択されているデバイス名を視覚的に表示する方法を3つ紹介します。

#### 方法1: パネルのタイトルに表示（最も簡単）

各パネルのタイトルに変数を埋め込みます。

**設定手順:**
1. パネルの編集画面を開く
2. 右側の「**Panel options**」セクションの「**Title**」に以下を入力:

```
${device_name} の温度と湿度
```

または

```
デバイス: ${device_name}
```

**表示例:**
```
┌─────────────────────────────────────┐
│ 11_thermohygrometer の温度と湿度    │
│                                     │
│  [グラフが表示される]                │
└─────────────────────────────────────┘
```

#### 方法2: Textパネルで大きく表示（推奨）

ダッシュボードの上部にTextパネルを配置して、選択中のデバイス名を大きく表示します。

**設定手順:**
1. 「**Add panel**」→「**Visualization**」を選択
2. Visualization type: **Text** を選択
3. 以下のMarkdownを入力:

```markdown
# 📊 選択中のデバイス: ${device_name}

現在表示しているセンサー: **${device_name}**
```

または、よりシンプルに:

```markdown
## デバイス: ${device_name}
```

4. 「**Panel options**」で以下を設定:
   - `Transparent background` → 有効（背景を透明に）
   - `Title` → 空欄（または非表示）

5. パネルサイズを調整（高さ2-3、幅24）してダッシュボード上部に配置

**表示例:**
```
┌─────────────────────────────────────┐
│ 📊 選択中のデバイス: 11_thermohygrometer │
│ 現在表示しているセンサー: 11_thermohygrometer │
└─────────────────────────────────────┘
```

#### 方法3: Statパネルで表示（カスタマイズ性が高い）

変数の値をStatパネルで表示します。

**設定手順:**
1. 「**Add panel**」→「**Visualization**」を選択
2. Visualization type: **Stat** を選択
3. クエリは不要（またはダミークエリを設定）
4. 「**Panel options**」で:
   - `Title` → `選択中のデバイス`
   - `Description` → 空欄

5. **Transform data** タブをクリック
6. 「**Add transformation**」→「**Add field from calculation**」を選択
7. 以下を設定:
   - `Mode` → `Binary operation`
   - `Operation` → `Add`
   - `Value` → 変数を使って手動で表示

**または、より簡単な方法:**

Text パネルを使用し、以下のHTMLを入力:

```html
<div style="text-align: center; padding: 20px;">
  <h2 style="color: #1f77b4; margin: 0;">デバイス名</h2>
  <h1 style="margin: 10px 0; font-size: 2em; color: #333;">${device_name}</h1>
</div>
```

4. 「**Text options**」で:
   - `Mode` → `HTML`

**表示例:**
```
┌──────────────────┐
│   デバイス名      │
│                  │
│ 11_thermohygrometer │
│                  │
└──────────────────┘
```

#### 方法4: ダッシュボードのタイトルに表示

ダッシュボード全体のタイトルに変数を埋め込みます。

**設定手順:**
1. ダッシュボードの右上の **⚙️（歯車アイコン）** をクリック
2. 「**Settings**」→「**General**」タブ
3. 「**Name**」に以下を入力:

```
SwitchBot センサー - ${device_name}
```

**表示例:**
ブラウザのタブとダッシュボード上部に以下が表示されます:
```
SwitchBot センサー - 11_thermohygrometer
```

#### 推奨レイアウト

```
┌─────────────────────────────────────────────┐
│ SwitchBot センサー - 11_thermohygrometer     │  ← ダッシュボードタイトル
├─────────────────────────────────────────────┤
│ デバイス: [11_thermohygrometer ▼]           │  ← 変数ドロップダウン
├─────────────────────────────────────────────┤
│ 📊 現在表示中: 11_thermohygrometer           │  ← Textパネル（高さ2）
├─────────────────────────────────────────────┤
│                                             │
│  [温度と湿度のグラフ]                        │  ← パネルタイトルにも表示
│  11_thermohygrometer の温度と湿度            │
│                                             │
└─────────────────────────────────────────────┘
```

#### 💡 複数デバイス選択時の表示

Multi-value変数を有効にしている場合、複数選択時は以下のように表示されます:

```
デバイス: 11_thermohygrometer, 12_thermohygrometer, 13_thermohygrometer
```

カンマ区切りで表示されるため、見やすくしたい場合は以下のような表記も可能:

```markdown
## 選択中のデバイス

${device_name:csv}
```

または

```markdown
選択デバイス数: ${device_name:count}個
- ${device_name:pipe}
```

---

## 10. 不快指数（Discomfort Index）の計算

```flux
from(bucket: "switchbot")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["_measurement"] == "WoIOSensor")
  |> filter(fn: (r) => r["_field"] == "temperature" or r["_field"] == "humidity")
  |> filter(fn: (r) => r["device_name"] == "${device_name}")
  |> aggregateWindow(every: v.windowPeriod, fn: mean, createEmpty: false)
  |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
  |> map(fn: (r) => ({ 
      r with 
      discomfort_index: 0.81 * r.temperature + 0.01 * r.humidity * (0.99 * r.temperature - 14.3) + 46.3
    }))
  |> keep(columns: ["_time", "device_name", "discomfort_index"])
```

**説明**: 温度と湿度から不快指数を計算します。
**不快指数の目安**:
- 55未満: 寒い
- 55-60: 肌寒い
- 60-65: 何も感じない
- 65-70: 快い
- 70-75: 暑くない
- 75-80: やや暑い
- 80-85: 暑くて汗が出る
- 85以上: 暑くてたまらない

---

## 11. 露点温度（Dew Point）の計算

```flux
import "math"

from(bucket: "switchbot")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["_measurement"] == "WoIOSensor")
  |> filter(fn: (r) => r["_field"] == "temperature" or r["_field"] == "humidity")
  |> filter(fn: (r) => r["device_name"] == "${device_name}")
  |> aggregateWindow(every: v.windowPeriod, fn: mean, createEmpty: false)
  |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
  |> map(fn: (r) => ({ 
      r with 
      dew_point: r.temperature - ((100.0 - r.humidity) / 5.0)
    }))
  |> keep(columns: ["_time", "device_name", "dew_point"])
```

**説明**: 温度と湿度から簡易的な露点温度を計算します。
**用途**: 結露のリスクを評価するのに有用です。

---

## 12. デバイス別の比較（ヒートマップ）

```flux
from(bucket: "switchbot")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["_measurement"] == "WoIOSensor")
  |> filter(fn: (r) => r["_field"] == "temperature")
  |> aggregateWindow(every: 10m, fn: mean, createEmpty: false)
  |> keep(columns: ["_time", "_value", "device_name"])
  |> sort(columns: ["device_name"])
```

**説明**: 全デバイスの温度を10分ごとに集約し、デバイス名でソートしてヒートマップで表示します。
**ビジュアライゼーション**: Heatmap パネルを使用

### Grafanaヒートマップ設定

ヒートマップのY軸にデバイス名のみを表示するには、以下の設定を行います：

1. **パネルの作成**
   - Visualization type: **Heatmap** を選択
   - 上記のクエリを貼り付け

2. **Y軸の設定**
   - 右側の設定パネルで「**Heatmap**」セクションを開く
   - `Calculate from data` を有効化
   - `Y Axis` → `Data` を選択
   - Grafanaが自動的に `device_name` をY軸に使用

3. **表示のカスタマイズ（オプション）**
   - 「**Standard options**」セクション:
     - `Unit` → `Temperature > Celsius (°C)`
   
   - 「**Color scheme**」:
     - お好みの配色を選択（例: `Red-Yellow-Green` または `Spectral`）

4. **セルサイズの調整**
   - `Cell gap` → `2`（セル間の間隔）
   - `Cell radius` → `0`（角の丸み）

**表示イメージ:**
```
時刻 →  00:00  01:00  02:00  03:00  04:00
       ┌──────┬──────┬──────┬──────┬──────┐
11_thermohygrometer │ 🟨20° │ 🟧22° │ 🟥25° │ 🟧23° │ 🟨21° │
       ├──────┼──────┼──────┼──────┼──────┤
12_thermohygrometer │ 🟩18° │ 🟨19° │ 🟨20° │ 🟨19° │ 🟩18° │
       ├──────┼──────┼──────┼──────┼──────┤
13_thermohygrometer │ 🟧24° │ 🟥26° │ 🟥27° │ 🟥26° │ 🟧24° │
       └──────┴──────┴──────┴──────┴──────┘
```

**特徴:**
- Y軸にはデバイス名のみが表示される
- 各セルの色で温度の高低を視覚的に確認
- 複数デバイスの温度変化を一目で比較可能

---

## 13. アラート用クエリ（高温検知）

```flux
from(bucket: "switchbot")
  |> range(start: -5m)
  |> filter(fn: (r) => r["_measurement"] == "WoIOSensor")
  |> filter(fn: (r) => r["_field"] == "temperature")
  |> last()
  |> filter(fn: (r) => r["_value"] > 30.0)
```

**説明**: 過去5分間で温度が30℃を超えているデバイスを検出します。
**用途**: Grafana Alertingと組み合わせて使用

---

## 14. データ更新頻度の確認

```flux
from(bucket: "switchbot")
  |> range(start: -24h)
  |> filter(fn: (r) => r["_measurement"] == "WoIOSensor")
  |> filter(fn: (r) => r["_field"] == "temperature")
  |> filter(fn: (r) => r["device_name"] == "${device_name}")
  |> difference(nonNegative: false, columns: ["_time"])
  |> map(fn: (r) => ({ r with _value: float(v: r._value) / 1000000000.0 }))
  |> mean()
```

**説明**: デバイスのデータ更新間隔の平均（秒）を計算します。
**用途**: データ収集の正常性を監視

---

## 15. 日別の温度推移（集約）

```flux
from(bucket: "switchbot")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["_measurement"] == "WoIOSensor")
  |> filter(fn: (r) => r["_field"] == "temperature")
  |> filter(fn: (r) => r["device_name"] == "${device_name}")
  |> aggregateWindow(every: 1d, fn: mean, createEmpty: false)
  |> yield(name: "daily_mean")
```

**説明**: 日別の平均温度を表示します。

---

## 使い方

### Grafana変数の設定

1. ダッシュボード設定 → Variables → New variable
2. 名前: `device_name`
3. Type: Query
4. Data source: InfluxDB
5. Query: クエリ9番を使用
6. Refresh: On Dashboard Load

### パネルの作成

1. Add Panel → Add new visualization
2. Data source: InfluxDB (Flux)
3. 上記のクエリをコピー&ペースト
4. パネルタイプを選択（Time series, Stat, Gauge, Table等）
5. Panel options で表示をカスタマイズ

### 推奨パネルタイプ

- **温度/湿度グラフ**: Time series
- **最新値表示**: Stat または Gauge
- **全デバイス一覧**: Table
- **統計情報**: Stat
- **不快指数**: Time series または Gauge
- **デバイス比較**: Heatmap

---

## トラブルシューティング

### データが表示されない場合

1. InfluxDBにデータが保存されているか確認:
```bash
docker exec -it iot-switchbot-dashboard-influxdb-1 influx query '
from(bucket: "switchbot")
  |> range(start: -1h)
  |> filter(fn: (r) => r["_measurement"] == "WoIOSensor")
  |> limit(n: 10)
'
```

2. Grafana のデータソース設定を確認
   - Organization: `org`
   - Token: `.env` ファイルの `INFLUXDB_TOKEN` と一致しているか

3. 時間範囲を確認（データがその期間に存在するか）

---

## さらなるカスタマイズ

### 週間レポート

```flux
from(bucket: "switchbot")
  |> range(start: -7d)
  |> filter(fn: (r) => r["_measurement"] == "WoIOSensor")
  |> filter(fn: (r) => r["_field"] == "temperature" or r["_field"] == "humidity")
  |> aggregateWindow(every: 1d, fn: mean, createEmpty: false)
  |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
```

### カスタムしきい値アラート

```flux
from(bucket: "switchbot")
  |> range(start: -10m)
  |> filter(fn: (r) => r["_measurement"] == "WoIOSensor")
  |> filter(fn: (r) => r["_field"] == "humidity")
  |> mean()
  |> filter(fn: (r) => r["_value"] < 30.0 or r["_value"] > 70.0)
```

湿度が30%未満または70%超過をアラート

---

## 参考リンク

- [Flux Language Documentation](https://docs.influxdata.com/flux/)
- [Grafana Flux Query Documentation](https://grafana.com/docs/grafana/latest/datasources/influxdb/query-editor/)
- [InfluxDB 2.x Documentation](https://docs.influxdata.com/influxdb/v2/)
