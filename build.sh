#!/bin/bash

# システムのアップデートと PortAudio のインストール
apt-get update && apt-get install -y portaudio19-dev

# 確認用のログ出力（重要！）
dpkg -l | grep portaudio

# Python のパッケージをインストール
pip install --upgrade pip
pip install -r requirements.txt
