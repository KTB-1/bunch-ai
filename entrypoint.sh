#!/bin/bash

# ollama 명령어가 존재하는지 확인
if ! command -v ollama &> /dev/null; then
    echo "ollama 명령어를 찾을 수 없습니다. PATH를 확인하세요."
    exit 1
fi

# 설치된 ollama의 경로를 출력
echo "ollama 경로: $(which ollama)"

# ollama 서버 시작 (백그라운드에서 실행)
ollama serve &

# 서버가 시작될 시간을 주기 위해 잠시 대기
sleep 5

# 모델 다운로드
ollama pull gemma2:latest
if [ $? -ne 0 ]; then
    echo "gemma2:latest 모델 다운로드에 실패했습니다."
    exit 1
fi

ollama pull gemma2:2b
if [ $? -ne 0 ]; then
    echo "gemma2:2b 모델 다운로드에 실패했습니다."
    exit 1
fi

echo "모든 모델이 성공적으로 다운로드되었습니다."