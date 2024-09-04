#!/bin/bash

MODEL_DIR="/app/models"  # 마운트된 모델 디렉토리
MODEL_FILE_1="$MODEL_DIR/gemma2_latest"  # 첫 번째 모델 파일 경로
MODEL_FILE_2="$MODEL_DIR/gemma2_2b"  # 두 번째 모델 파일 경로

# ollama 명령어가 존재하는지 확인
if ! command -v ollama &> /dev/null; then
    echo "ollama 명령어를 찾을 수 없습니다. PATH를 확인하세요."
    exit 1
fi

# 설치된 ollama의 경로를 출력
echo "ollama 경로: $(which ollama)"

# ollama 서버 시작 (백그라운드에서 실행)
ollama serve &

# 모델이 존재하는지 확인하고, 없으면 다운로드
if [ ! -f "$MODEL_FILE_1" ]; then
    echo "모델 $MODEL_FILE_1이 존재하지 않습니다. 다운로드를 시작합니다."
    ollama pull gemma2:latest
    if [ $? -ne 0 ]; then
        echo "gemma2:latest 모델 다운로드에 실패했습니다."
        exit 1
    fi
else
    echo "모델 $MODEL_FILE_1이 이미 존재합니다. 다운로드를 건너뜁니다."
fi

if [ ! -f "$MODEL_FILE_2" ]; then
    echo "모델 $MODEL_FILE_2이 존재하지 않습니다. 다운로드를 시작합니다."
    ollama pull gemma2:2b
    if [ $? -ne 0 ]; then
        echo "gemma2:2b 모델 다운로드에 실패했습니다."
        exit 1
    fi
else
    echo "모델 $MODEL_FILE_2이 이미 존재합니다. 다운로드를 건너뜁니다."
fi

echo "모든 필요한 모델이 준비되었습니다."


# 애플리케이션 실행
echo "Starting the Python application..."
python3 src/main.py