import json
from database import get_news_without_summary, update_news_summary
from config import setup_logging
import logging
import time
from dotenv import load_dotenv
import openai
import os
from openai import OpenAI

# 로깅 설정
setup_logging()

# OpenAI API 키 설정
load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')

# 템플릿 문자열 정의
template_string = """
작업: 다음 뉴스 기사를 분석하여 주요 포인트 3가지와 한 줄 인사이트를 추출하세요.

지시사항:
1. 기사의 내용을 면밀히 분석하세요.
2. 가장 중요하고 관련성 높은 정보를 바탕으로 3가지 주요 포인트를 추출하세요.
3. 3가지 포인트를 추출하기에 정보가 충분하지 않다면, 추출할 수 있는 포인트는 기입하고 그 외에는 '정보불충분'이라고 적어주십시오.
4. 각 포인트는 간결하게 한 문장으로 작성하되, 핵심 정보를 포함해야 합니다.
5. 기사 전체를 고려하여 독자에게 가장 유용할 수 있는 한 줄 인사이트를 도출하세요.
6. 인사이트는 기사의 함의나 잠재적 영향을 포함할 수 있습니다.

point_1 : 추출한 주요 포인트 중 첫번째를 작성하세요.
point_2 : 추출한 주요 포인트 중 두번째를 작성하세요.
point_3 : 추출한 주요 포인트 중 세번째를 작성하세요.
insight: 기사 전체를 고려하여 독자에게 가장 유용할 수 있는 한 줄 인사이트를 도출하세요. 인사이트는 기사의 함의나 잠재적 영향을 포함할 수 있습니다.

뉴스 기사: {text}
"""

def summarize_news():
    logging.info("=" * 50)
    logging.info("뉴스 요약 프로세스 시작..")
    news_items = get_news_without_summary()
    
    for news in news_items:
        news_content = news.description if news.content == 'failed' else news.content
        
        # 템플릿 문자열을 대화 내용으로 완성
        formatted_prompt = template_string.format(text=news_content)
        
        try:
            client = OpenAI(
            api_key=openai.api_key,
            )

            # OpenAI ChatGPT API를 호출하여 응답 받기
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant. Response in json format"},
                    {"role": "user", "content": formatted_prompt}
                ],
                # response_format 지정하기
                response_format = {"type":"json_object"}
            )

            # 응답 메시지를 추출
            customer_response = response.choices[0].message.content
            print(customer_response)
            # JSON 형식으로 파싱
            output_dict = json.loads(customer_response)
            summary_json = json.dumps(output_dict)
            update_news_summary(news.news_id, summary_json)
            logging.info(f"뉴스 ID {news.news_id}의 요약 처리 및 업데이트 완료")
        except Exception as e:
            logging.error(f"뉴스 ID {news.news_id} 처리 중 오류 발생: {e}")


if __name__ == "__main__":
    logging.info("뉴스 요약 프로세스 시작")
    start_time = time.time()
    summarize_news()
    total_time = time.time() - start_time
    logging.info("뉴스 요약 프로세스 완료")
    logging.info(f"총 처리 시간: {total_time:.2f} 초")
    