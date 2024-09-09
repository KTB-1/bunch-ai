FROM python:3.10.11-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y gcc curl

# curl 및 ollama 설치
RUN apt-get update && apt-get install -y curl && \
    curl -fsSL https://ollama.com/install.sh | sh && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# requirements.txt 복사 및 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 소스 코드 복사
COPY ./src ./src

# 애플리케이션 실행을 위한 entrypoint 스크립트 복사
COPY app-entrypoint.sh /app-entrypoint.sh
RUN chmod +x /app-entrypoint.sh

# 애플리케이션 실행
CMD ["/app-entrypoint.sh"]
