#!/usr/bin/env bash

# 必要なシステムパッケージをインストール
apt-get update && apt-get install -y portaudio19-dev

# Python の依存関係をインストール
pip install --upgrade pip
pip install -r requirements.txt
