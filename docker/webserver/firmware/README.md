# ファームウェア配信ディレクトリ

M5Stick(SIM7080G版)のOTA更新で配信する`.bin`ファイルを手動配置するディレクトリ。
`GET /api/firmware/latest`が`manifest.json`を読み、`GET /firmware/<file>`が実体を配信する。

## 新しいファームウェアを配信する手順

1. `.bin`ファイルをこのディレクトリに配置する（例: `2.0.1.bin`）。`.bin`ファイルはgit管理外（`.gitignore`参照）なので、
   サーバーへは`scp`等で直接転送するか、サーバー上でビルドする。
2. `manifest.json`を更新する:
   ```json
   {
     "version": "2.0.1",
     "file": "2.0.1.bin",
     "md5": "<2.0.1.binのMD5ハッシュ(32文字, 省略可)>"
   }
   ```
   `md5`はMD5ハッシュが不要なら省略可（キー自体を消すか空文字にする）。
   ```bash
   md5sum 2.0.1.bin
   ```
3. M5Stickが次回起動時に`GET /api/firmware/latest`をポーリングし、`version`が自機の`FIRMWARE_VERSION`と
   異なっていれば自動でダウンロード・書き込み・再起動する。単純な文字列比較なので、
   ロールバックしたい場合は`manifest.json`の`version`を古い値に戻せばよい。

## 更新を配信しない状態に戻す

`version`を現在配信中のファームウェアと同じ値に戻すか、`manifest.json`自体を削除する
（削除した場合`/api/firmware/latest`は404を返し、M5Stick側は「更新チェックをスキップ」として安全に処理する）。
