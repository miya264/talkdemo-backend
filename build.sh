#!/usr/bin/env bash

# Render の環境では root 権限がないため sudo を使う
sudo apt-get update -o Acquire::Check-Valid-Until=false -o Acquire::Check-Date=false
sudo apt-get install -y portaudio19-dev

# poetry を使っている場合
poetry install
