FROM python:3.11.9-slim

WORKDIR /app

# 필요한 패키지 설치 및 업데이트
RUN apt-get update && \
    apt-get install -y gcc curl build-essential libreadline-dev && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# curl 및 ollama 설치
RUN curl -fsSL https://ollama.com/install.sh | sh

# Python 패키지 설치 (ChromaDB 포함)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 소스 코드 복사
COPY ./src ./src

# 애플리케이션 실행을 위한 entrypoint 스크립트 복사
COPY app-entrypoint.sh /app-entrypoint.sh
RUN chmod +x /app-entrypoint.sh

# 애플리케이션 실행
CMD ["/app-entrypoint.sh"]
