#!/bin/bash

MODEL_DIR="/app/models"
MODEL_FILE_1="$MODEL_DIR/gemma2_latest"
MODEL_FILE_2="$MODEL_DIR/gemma2_2b"

# ollama 명령어가 있는지 확인
if ! command -v ollama &> /dev/null; then
    echo "ollama 명령어를 찾을 수 없습니다. PATH를 확인하세요."
    exit 1
fi

# 설치된 ollama의 경로를 출력
echo "ollama 경로: $(which ollama)"

# ollama 서버를 백그라운드에서 실행
echo "ollama 서버를 시작합니다..."
ollama serve 
