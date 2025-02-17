# Pythonイメージをベースに
FROM python:3.10

# 作業ディレクトリを設定
WORKDIR /app

# 必要なファイルをコピー
COPY requirements.txt ./
COPY main.py ./
COPY start.sh ./

# 必要なパッケージをインストール
RUN pip install --no-cache-dir -r requirements.txt

# 実行権限を付与
RUN chmod +x start.sh

# コンテナ起動時にFastAPIアプリを起動
CMD ["./start.sh"]
