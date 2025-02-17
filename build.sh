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

