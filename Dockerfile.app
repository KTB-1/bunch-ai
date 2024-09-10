FROM python:3.10.11-slim

WORKDIR /app

# 필요한 패키지 설치
RUN apt-get update && \
    apt-get install -y gcc curl build-essential libreadline-dev && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# SQLite 3.46.1 소스 다운로드 및 빌드
RUN curl -O https://www.sqlite.org/2024/sqlite-autoconf-3460100.tar.gz && \
    tar xzf sqlite-autoconf-3460100.tar.gz && \
    cd sqlite-autoconf-3460100 && \
    ./configure --prefix=/usr/local && \
    make && make install && \
    cd .. && rm -rf sqlite-autoconf-3460100* && \
    rm sqlite-autoconf-3460100.tar.gz

# curl 및 ollama 설치
RUN curl -fsSL https://ollama.com/install.sh | sh

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
