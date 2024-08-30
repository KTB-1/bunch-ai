import torch
import chromadb
from tqdm import tqdm
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
import pandas as pd
from chromadb.config import Settings
from langchain_core.documents import Document
from datetime import datetime
from sqlalchemy import create_engine
from dbconnect import create_connection_mariadb, get_embedding_zero_rows, get_and_update_embedding_zero_rows
from dbconnect import get_userID_from_usernewsviews, get_user_news_views_data, insert_user_news_views_data
from dbconnect import get_news_summaries_by_usernewsviews
from database import get_decoded_summaries_modified_V1
from datetime import datetime, timedelta

def get_data_and_store_chroma():
    
    summaries = get_decoded_summaries_modified_V1()

    embedding_model = OllamaEmbeddings(model='gemma2:2b')

    chroma_client = Chroma(
        collection_name="news_embedding_testing_1",
        embedding_function=embedding_model,
        collection_metadata={"hnsw:space":"cosine"},
        persist_directory="chroma_langchain_db",
    )

    # ChromaDB에 데이터 삽입
    tmp_docus = []
    for idx, row in enumerate(summaries):
        sum_summary = row['summary']['point_1'] + ' ' + row['summary']['point_2'] + ' ' + row['summary']['point_3']
        tmp = Document(
            page_content=sum_summary,
            metadata={
                "news_id": str(row['news_id'])
            },
            id=int(row['news_id']),
        )
        tmp_docus.append(tmp)
    chroma_client.add_documents(documents=tmp_docus)

    # query = "비트코인 채굴업체들이 반감기 이후 수익 감소 문제를 해결하기 위해 AI 애플리케이션에 컴퓨팅 파워를 제공하는 새로운 사업 모델을 모색하고 있다. AI 시장의 성장과 함께, 비트코인 채굴업체들은 이미 가진 전력 및 데이터 센터 인프라를 활용하여 AI 수요에 부응할 수 있는 위치에 있다. 비트코인 채굴업체들은 AI 기반 사업으로 수익을 창출하며"
    # results = chroma_client.similarity_search_with_score(query=query, k=5)

    # # 결과 출력
    # for i, (result, score) in enumerate(results, 1):
    #     print(f"Article {i}:")
    #     print(f"Score: {score}")
    #     print(f"Description: {result.page_content}")
    #     print(f"Metadata: {result.metadata}")
    #     print()

def recc_item(userid, cnt):

    df = get_userID_from_usernewsviews(user_id=userid, k=cnt)
    # print(df)

    print(df.columns)
    ###
    # view_date를 datetime 형식으로 변환
    df['view_date'] = pd.to_datetime(df['view_date'], format='%Y-%m-%d %H:%M:%S')

    # 현재 시간으로부터 5일 전의 날짜 계산
    cutoff_date = datetime.now() - timedelta(days=5)

    # 5일보다 오래된 날짜의 행 삭제
    df = df[df['view_date'] >= cutoff_date]
    ###

    ### result_list 로 가져오는 개수 조정 (date 에 따라서)
    result_list = get_news_summaries_by_usernewsviews(df)
    result_list = result_list[:5]
    # print(result_list)
    
    check_same = []
    for it, tmp in enumerate(result_list):
        check_same.append(tmp['news_id'])
 
    embedding_model = OllamaEmbeddings(model="gemma2:2b")

    chroma_client = Chroma(
        collection_name="news_embedding_testing_1",
        embedding_function=embedding_model,
        collection_metadata={"hnsw:space":"cosine"},
        persist_directory="chroma_langchain_db",
    )

    recc_list = []
    for row in result_list:
        query = row['summary']['point_1'] + ' ' + row['summary']['point_2'] + ' ' + row['summary']['point_3']
        results = chroma_client.similarity_search_with_score(query=query, k=5)
        
        for i, (result, score) in enumerate(results, 1):
            recc_list.append(int(result.metadata['news_id']))

        # # 결과 출력
        # for i, (result, score) in enumerate(results, 1):
        #     print(f"Article {i}:")
        #     print(f"Score: {score}")
        #     print(f"Description: {result.page_content}")
        #     print(f"Metadata: {result.metadata}")
        #     print()

    recc_list = [item for item in recc_list if item not in check_same]
    recc_list = list(set(recc_list))
    # print(recc_list)

    return recc_list

if __name__ == "__main__":
    # get_data_and_store_chroma()
    
    recc_item(1, 3)

    # df = get_embedding_zero_rows()
    # print(df)

    # if df is not None and len(df) > 0:
    #     insert_user_news_views_data(df)
    # else:
    #     print("추가할 데이터가 없습니다.")