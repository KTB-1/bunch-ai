FROM python:3.10.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY ./src ./src

CMD ["python", "src/main.py"]