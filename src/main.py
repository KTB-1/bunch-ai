import schedule
import time
import asyncio
import signal
import sys
import atexit
import logging
from fetch_news import fetch_all_news
from async_scrape_newspaper3k import main as scrape_main
from summarize import summarize_news
from database import init_database, close_database
from embed_news import get_data_and_store_chroma
from config import setup_logging, ROOP_TIME

# 로그 설정
setup_logging()

def cleanup():
    logging.info("데이터베이스 연결을 정리합니다...")
    close_database()

def signal_handler(signum, frame):
    logging.info(f"Signal {signum} 받음. 프로그램을 종료합니다...")
    sys.exit(0)

# 데이터베이스 초기화
init_database()

# 정상 종료 시 cleanup 함수 실행
atexit.register(cleanup)

# SIGINT와 SIGTERM 시그널 처리
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

async def run_pipeline():
    """
    전체 파이프라인을 실행합니다.
    """
    logging.info("="*50)
    logging.info("파이프라인 시작...")
    try:
        fetch_all_news()  # 뉴스 데이터 가져오기
        scrape_main() # 뉴스 url에서 본문만 스크랩
        summarize_news() # gemma2 사용해 뉴스 분석
        get_data_and_store_chroma() # chromaDB에 news_id, summary 저장
        logging.info("파이프라인 완료.")
    except Exception as e:
        logging.error(f"파이프라인 실행 중 오류 발생: {e}")

def scheduled_job():
    asyncio.run(run_pipeline())

def main():
    logging.info(f"프로그램 시작. {ROOP_TIME}분마다 실행됩니다.")
    schedule.every(ROOP_TIME).minutes.do(scheduled_job)
    
    # 즉시 첫 실행
    scheduled_job()

    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except Exception as e:
        logging.error(f"예외 발생: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()