import requests
from newspaper import Article
from fake_useragent import UserAgent
import psutil
import time
import chardet
import logging
import re
import ssl
from config import (
    setup_logging, CHUNK_SIZE, TIMEOUT, 
    MAX_RETRIES, RETRY_DELAY
)
from database import get_news_without_content, update_news_content, delete_news_entry
from collections import Counter

# 로그 설정
setup_logging()

# User-Agent 랜덤 생성기 설정
ua = UserAgent()

def create_ssl_context():
    context = ssl.create_default_context()
    context.set_ciphers('DEFAULT@SECLEVEL=1')
    context.options |= ssl.OP_NO_SSLv2
    context.options |= ssl.OP_NO_SSLv3
    context.options |= ssl.OP_NO_TLSv1
    context.options |= ssl.OP_NO_TLSv1_1
    return context

def fetch(url, timeout=TIMEOUT, max_retries=MAX_RETRIES):
    ssl_context = create_ssl_context()
    for attempt in range(max_retries):
        try:
            headers = {'User-Agent': ua.random}
            response = requests.get(url, headers=headers, timeout=timeout, verify=ssl_context)
            response.raise_for_status()
            content = response.content
            encoding = chardet.detect(content)['encoding'] or 'utf-8'
            return content.decode(encoding, errors='replace')
        except (requests.Timeout, requests.RequestException, ssl.SSLError, ConnectionResetError) as e:
            logging.warning(f"{url}에 대한 오류 발생, 시도 {attempt + 1}/{max_retries}: {str(e)}")
            if isinstance(e, ssl.SSLError) and attempt < max_retries - 1:
                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
            if attempt < max_retries - 1:
                time.sleep(RETRY_DELAY * (attempt + 1))
        except Exception as e:
            logging.error(f"{url}에 대한 예기치 않은 오류 발생: {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(RETRY_DELAY * (attempt + 1))
    
    logging.error(f"{url}를 {max_retries}회 시도했으나 실패했습니다")
    return None

def parse_article(html, url):
    if html:
        try:
            article = Article(url, language='ko')
            article.download(input_html=html)
            article.parse()
            cleaned_text = clean_text(article.text)
            return cleaned_text
        except Exception as e:
            logging.error(f"{url}을(를) 파싱하는 데 실패했습니다: {str(e)}")
    return None

def extract_news_content(url):
    if not isinstance(url, str) or not url.startswith('http'):
        logging.warning(f"잘못된 URL: {url}")
        return None

    html = fetch(url)
    if html:
        return parse_article(html, url)
    return None

def scrape_urls(urls, chunk_size=CHUNK_SIZE):
    all_results = []
    
    chunks = [urls[i:i+chunk_size] for i in range(0, len(urls), chunk_size)]
    
    for i, chunk in enumerate(chunks):
        results = [extract_news_content(url) for url in chunk]
        all_results.extend(results)
        
        logging.info(f"{len(urls)}개의 URL 중 {len(all_results)}개 처리 완료")
        logging.info(f"CPU 사용량: {psutil.cpu_percent()}%, Memory 사용량: {psutil.virtual_memory().percent}%")
        
        if i < len(chunks) - 1:
            time.sleep(1)

    return all_results

def clean_text(text):
    if text is None:
        return None
    
    ad_patterns = [r'\b광고\b', r'\bAD\b', r'\b스폰서드\b', r'\bsponsored\b']
    for pattern in ad_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    
    text = re.sub(r'\n+', '\n', text)
    text = text.strip()
    
    return text

def update_content_in_db():
    urls_to_scrape = get_news_without_content()
    logging.info(f"스크랩할 URL 찾음 : {len(urls_to_scrape)}")

    if urls_to_scrape:
        scraped_contents = scrape_urls(urls_to_scrape)
        
        for url, content in zip(urls_to_scrape, scraped_contents):
            if content:
                update_news_content(url, content)

def main():
    start_time = time.time()
    logging.info("웹 스크래핑 프로세스 시작...")

    urls_to_scrape = get_news_without_content()
    total_urls = len(urls_to_scrape)
    logging.info(f"스크랩할 총 URL 수: {total_urls}")

    results = Counter()
    failed_urls = []

    if urls_to_scrape:
        scraped_contents = scrape_urls(urls_to_scrape)
        
        for url, content in zip(urls_to_scrape, scraped_contents):
            if content and len(content) > 500:
                update_news_content(url, content)
                logging.info(f"URL 업데이트 완료: {url}")
                results['success'] += 1
            else:
                delete_news_entry(url)
                logging.warning(f"콘텐츠가 없거나 500자 이하여서 삭제됨: {url}")
                results['deleted'] += 1
                failed_urls.append(url)

    total_time = time.time() - start_time
    success_rate = (results['success'] / total_urls) * 100 if total_urls > 0 else 0

    logging.info("=" * 50)
    logging.info("웹 스크래핑 프로세스 완료")
    logging.info(f"총 처리 시간: {total_time:.2f} 초")
    logging.info(f"총 URL 수: {total_urls}")
    logging.info(f"성공: {results['success']}")
    logging.info(f"삭제됨: {results['deleted']}")
    logging.info(f"성공률: {success_rate:.2f}%")
    logging.info("=" * 50)

    if failed_urls:
        logging.info("삭제된 URL 목록:")
        for url in failed_urls:
            logging.info(url)
        logging.info("=" * 50)

    logging.info(f"CPU 사용률: {psutil.cpu_percent()}%")
    logging.info(f"메모리 사용률: {psutil.virtual_memory().percent}%")

if __name__ == "__main__":
    main()