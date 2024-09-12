#!/bin/bash

MODEL_DIR="/app/models"
MODEL_FILE_1="$MODEL_DIR/gemma2/latest"
MODEL_FILE_2="$MODEL_DIR/gemma2/2b"

# 환경 변수에서 OLLAMA_BASE_URL 설정을 가져옴
OLLAMA_BASE_URL=${OLLAMA_BASE_URL:-"http://localhost:11434"}

# ollama 서버를 백그라운드에서 실행
echo "ollama 서버를 시작합니다..."
OLLAMA_HOST="$OLLAMA_BASE_URL" ollama serve &

echo "ollama 서버 백그라운드 실행"

# ollama 서버가 실행될 때까지 대기
echo "ollama 서버 준비 중..."
while ! curl -s "$OLLAMA_BASE_URL" > /dev/null; do 
  sleep 1
done

echo "ollama 서버가 준비되었습니다."

# 모델이 존재하는지 확인하고, 없으면 다운로드
if [ ! -f "$MODEL_FILE_1" ]; then
    echo "모델 $MODEL_FILE_1이 존재하지 않습니다. 다운로드를 시작합니다."
    OLLAMA_HOST="$OLLAMA_BASE_URL" ollama pull gemma2:latest
    if [ $? -ne 0 ]; then
        echo "gemma2:latest 모델 다운로드에 실패했습니다."
        exit 1
    fi
else
    echo "모델 $MODEL_FILE_1이 이미 존재합니다. 다운로드를 건너뜁니다."
fi

if [ ! -f "$MODEL_FILE_2" ]; then
    echo "모델 $MODEL_FILE_2이 존재하지 않습니다. 다운로드를 시작합니다."
    OLLAMA_HOST="$OLLAMA_BASE_URL" ollama pull gemma2:2b
    if [ $? -ne 0 ]; then
        echo "gemma2:2b 모델 다운로드에 실패했습니다."
        exit 1
    fi
else
    echo "모델 $MODEL_FILE_2이 이미 존재합니다. 다운로드를 건너뜁니다."
fi

echo "모든 필요한 모델이 준비되었습니다."

# 애플리케이션 실행
echo "Python  실행합니다..."
python3 src/app.py & 
python3 src/main.py 