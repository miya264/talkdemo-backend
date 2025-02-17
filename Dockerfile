# Python 3.10 ベースのイメージ
FROM python:3.10

# 必要なシステムパッケージをインストール
RUN apt-get update && apt-get install -y \
    portaudio19-dev \
    && rm -rf /var/lib/apt/lists/*

# 作業ディレクトリを設定
WORKDIR /app

# 必要なファイルをコピー
COPY requirements.txt ./
COPY main.py ./
COPY start.sh ./

# Pythonパッケージをインストール
RUN pip install --no-cache-dir -r requirements.txt

# 実行権限を付与
RUN chmod +x start.sh

# アプリケーションを起動
CMD ["./start.sh"]
