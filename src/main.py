import schedule
import time
from fetch_news import fetch_all_news
import asyncio
from async_scrape_newspaper3k import main as scrape_main
from summarize import summarize_news
from database import create_tables
from embed_news import get_data_and_store_chroma, http_chroma
from config import setup_logging, ROOP_TIME
import logging

# 로그 설정
setup_logging()

# aidb 데이터베이스, 테이블 없는 경우 생성
create_tables()

async def run_pipeline():
    """
    전체 파이프라인을 실행합니다.
    """
    logging.info("="*50)
    logging.info("파이프라인 시작...")
    fetch_all_news()  # 뉴스 데이터 가져오기
    await scrape_main() # 뉴스 url에서 본문만 스크랩
    summarize_news() # gemma2 사용해 뉴스 분석
    logging.info("파이프라인 완료.")
    
    ## persistent client
    get_data_and_store_chroma()
    ## http client
    # http_chroma()

def scheduled_job():
    asyncio.run(run_pipeline())

def main():
    logging.info(f"프로그램 시작. {ROOP_TIME}분마다 실행됩니다.")
    schedule.every(ROOP_TIME).minutes.do(scheduled_job)
    
    # 즉시 첫 실행
    scheduled_job()

    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    main()