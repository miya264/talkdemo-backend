#!/usr/bin/env bash

<<<<<<< HEAD
# Render の環境では root 権限がないため sudo を使う
sudo apt-get update -o Acquire::Check-Valid-Until=false -o Acquire::Check-Date=false
sudo apt-get install -y portaudio19-dev

# poetry を使っている場合
poetry install
=======
# 環境のパッケージリストを更新
apt-get update -o Acquire::Check-Valid-Until=false -o Acquire::Check-Date=false
apt-get install -y portaudio19-dev libasound2-dev

# Poetry のセットアップ
if [ -f "pyproject.toml" ]; then
    poetry install
else
    echo "Error: pyproject.toml not found"
    exit 1
fi
>>>>>>> 39b1ce9 (修正)
