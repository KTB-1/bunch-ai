import logging
from dotenv import load_dotenv
import os
import time

# .env 파일 로드
load_dotenv()

# Naver news API 호출 시 설정
# SEARCH_QUERIES=["주식", "채권", "금융", "금리", "환율 및 외환 시장", "금융 규제", "경제 지표"]
# DISPLAY_COUNT=10
# START_INDEX=1
# END_INDEX=300
# SORT_ORDER=sim
SEARCH_QUERIES=["주식"]
DISPLAY_COUNT=5
START_INDEX=1
END_INDEX=5
SORT_ORDER='date'

# 로그 설정
LOG_FILE='news_project.log'

# 성능 관련 설정
CONCURRENCY=5  # 동시 실행 설정
CHUNK_SIZE=30   # 청크 사이즈 설정
TIMEOUT=30      # 타임아웃 설정 (초)
MAX_RETRIES=2   # 최대 재시도 횟수
RETRY_DELAY=1   # 재시도 대기 시간 (초)

# 네이버 API의 클라이언트 ID와 시크릿 키 설정
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.FileHandler(LOG_FILE, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    # 로그 파일에 구분선 추가
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write("\n" + "=" * 50 + "\n")
        f.write(f"New scraping session started at {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 50 + "\n")

# DB 설정
MYSQL_HOST = os.getenv("DB_HOST", "localhost")
MYSQL_PORT = int(os.getenv("DB_PORT", 3306))
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE")