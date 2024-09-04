FROM python:3.10.11-slim

WORKDIR /app

# requirements.txt 복사 및 pip, torch 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir torch

# curl 설치 및 ollama 설치
RUN apt-get update && apt-get install -y curl && \
    curl -fsSL https://ollama.com/install.sh | sh && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# 소스 코드 복사
COPY ./src ./src

# Entrypoint 스크립트를 복사하고 실행 권한 추가
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Entrypoint 스크립트 실행
CMD ["/entrypoint.sh"]
