#!/usr/bin/env bash

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

# PyAudio の手動インストール（Poetry のインストール後に実行）
pip install --no-cache-dir --force-reinstall pyaudio --global-option="build_ext" --global-option="-I/usr/include" --global-option="-L/usr/lib"
