FROM python:3.11
WORKDIR /app

# webserver用のrequirements.txtをコピーして依存関係をインストール
COPY docker/webserver/requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# webserverアプリケーションコードをコピー
COPY docker/webserver/server.py /app/

# ポート5000を公開
EXPOSE 5000

# HTTPサーバーを起動
CMD ["python", "server.py"]
