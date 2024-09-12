FROM --platform=linux/amd64 python:3.11.9-slim

WORKDIR /app

# 필요한 패키지 설치 및 업데이트
RUN apt-get update && \
    apt-get install -y gcc curl build-essential libreadline-dev && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /app/models

# Python 패키지 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 소스 코드 복사
COPY ./src ./src

# 애플리케이션 실행을 위한 entrypoint 스크립트 복사
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# 애플리케이션 실행
CMD ["/entrypoint.sh"]
