FROM python:3.10.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

RUN curl -fsSL https://ollama.com/install.sh | sh

COPY ./src ./src

# Entrypoint 스크립트를 사용하여 모델 다운로드 및 애플리케이션 실행
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

CMD ["/entrypoint.sh"]