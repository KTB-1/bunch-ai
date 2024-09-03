import pandas as pd
from sqlalchemy import create_engine, text
import logging
from config import MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE
from config import setup_logging
import json

setup_logging()

def create_connection_mariadb():
    # MariaDB 연결 정보 설정
    user = MYSQL_USER
    password = MYSQL_PASSWORD
    host = MYSQL_HOST
    port = MYSQL_PORT
    database_name = MYSQL_DATABASE

    connection = None

    # SQLAlchemy 연결 문자열 생성
    connection_string = f"mysql+pymysql://{user}:{password}@{host}:{port}/{database_name}"

    # SQLAlchemy 엔진 생성
    engine = create_engine(connection_string)

    logging.info("MariaDB 데이터베이스 연결 성공")

    return engine

def get_embedding_zero_rows():
    engine = create_connection_mariadb()
    
    try:
        # SQL 쿼리 실행
        query = "SELECT * FROM News WHERE embedding IS NULL"
        df = pd.read_sql(query, con=engine)
        return df
    except Exception as e:
        logging.error(f"embedding NULL인 데이터를 가져오는 중 오류 발생: {e}")
        return None
    finally:
        engine.dispose()

def test_get_1_rows():
    engine = create_connection_mariadb()
    
    try:
        # SQL 쿼리 실행
        query = "SELECT * FROM News WHERE embedding = 1"
        df = pd.read_sql(query, con=engine)
        return df
    except Exception as e:
        logging.error(f"embedding 1인 데이터를 가져오는 중 오류 발생: {e}")
        return None
    finally:
        engine.dispose()

def get_and_update_embedding_zero_rows():
    engine = create_connection_mariadb()
    
    try:
        # SQL 쿼리 실행하여 embedding 값이 0인 행을 가져옴
        query = "SELECT * FROM News WHERE embedding IS NULL"
        df = pd.read_sql(query, con=engine)
        
        # 가져온 데이터가 있으면 embedding 값을 1로 업데이트
        if not df.empty:
            update_query = "UPDATE News SET embedding = 1 WHERE embedding IS NULL"
            with engine.connect() as conn:
                conn.execute(text(update_query))
                conn.commit()
            logging.info("embeddings 값이 NULL인 행의 값을 1로 업데이트했습니다.")
        else:
            logging.info("업데이트할 데이터가 없습니다.")

        return df
    except Exception as e:
        logging.error(f"News 데이터를 가져오고 업데이트하는 중 오류 발생: {e}")
        return None
    finally:
        engine.dispose()

def get_decoded_summaries(news_ids):
    # 데이터베이스 연결 생성
    engine = create_connection_mariadb()
    
    # SQL 쿼리 작성
    query = """
        SELECT news_id, news_url, title, summary 
        FROM News 
        WHERE news_id IN :news_ids
        AND summary IS NOT NULL 
        AND summary != ''
    """

    # SQLAlchemy를 사용하여 쿼리 실행 및 결과 가져오기
    try:
        with engine.connect() as connection:
            result = connection.execute(text(query), {'news_ids': tuple(news_ids)})
            rows = result.fetchall()

            decoded_summaries = []
            
            for row in rows:
                news_id = row[0]
                news_url = row[1]
                news_title = row[2]
                summary_json = row[3]

                try:
                    # JSON 디코딩
                    decoded_summary = json.loads(summary_json)
                    decoded_summaries.append({
                        'news_id': news_id,
                        'news_url': news_url,
                        'title': news_title,
                        'summary': decoded_summary
                    })
                    
                except json.JSONDecodeError as e:
                    logging.error(f"JSON 디코딩 오류 (news_id: {row['news_id']}): {e}")
            
            # 결과 반환
            return decoded_summaries

    except Exception as e:
        logging.error(f"데이터 조회 오류: {e}")
        return []

def get_userID_from_usernewsviews(user_id, k):
    engine = create_connection_mariadb()

    try:
        # SQL 쿼리 실행
        query = f"""
            SELECT * FROM UserNewsViews 
            WHERE user_id = {user_id} 
            ORDER BY view_date DESC 
            LIMIT {k}
        """
        df = pd.read_sql(query, con=engine)
        return df
    except Exception as e:
        logging.error(f"user_id 데이터를 가져오는 중 오류 발생: {e}")
        return None
    finally:
        engine.dispose()

def get_user_news_views_data():
    engine = create_connection_mariadb()

    try:
        # SQL 쿼리 실행하여 UserNewsViews 테이블의 모든 데이터를 가져옴
        query = "SELECT * FROM UserNewsViews"
        df = pd.read_sql(query, con=engine)
        return df
    except Exception as e:
        logging.error(f"user_news_view 데이터를 가져오는 중 오류 발생: {e}")
        return None
    finally:
        engine.dispose()

def get_news_summaries_by_usernewsviews(df_usernewsviews):
    engine = create_connection_mariadb()
    
    news_data = []
    
    try:
        with engine.connect() as conn:
            for _, row in df_usernewsviews.iterrows():
                news_id = row['news_id']
                
                # SQL 쿼리 실행: news_id와 summary만 선택
                query = f"SELECT news_id, summary FROM News WHERE news_id = {news_id}"
                df_news = pd.read_sql(query, con=conn)
                
                if not df_news.empty:
                    news_row = df_news.iloc[0].to_dict()
                    
                    # summary 컬럼을 디코딩
                    if 'summary' in news_row:
                        try:
                            news_row['summary'] = json.loads(news_row['summary'])
                        except json.JSONDecodeError as e:
                            logging.error(f"JSON 디코딩 오류 (news_id: {news_id}): {e}")
                            news_row['summary'] = None
                    
                    news_data.append(news_row)
            
            # 리스트 형태로 반환
            return news_data
    except Exception as e:
        logging.error(f"News 데이터를 가져오는 중 오류 발생: {e}")
        return None
    finally:
        engine.dispose()

def insert_user_news_views_data(df):
    engine = create_connection_mariadb()
    
    try:
        with engine.connect() as conn:
            # DataFrame에서 각 행을 읽어와서 UserNewsViews 테이블에 삽입
            for _, row in df.iterrows():
                # 예시로 user_id를 1로 설정, news_id와 view_date는 DataFrame에서 가져옴
                user_id = 1
                news_id = row['news_id']
                view_date = pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')

                # 삽입 쿼리 실행
                query = text("""
                    INSERT INTO UserNewsViews (user_id, news_id, view_date)
                    VALUES (:user_id, :news_id, :view_date)
                """)
                conn.execute(query, {'user_id': user_id, 'news_id': news_id, 'view_date': view_date})
            
            conn.commit()
            print("UserNewsViews 테이블에 샘플 데이터가 성공적으로 추가되었습니다.")
    
    except Exception as e:
        logging.error(f"UserNewsViews 테이블에 데이터를 삽입하는 중 오류 발생: {e}")
    finally:
        engine.dispose()

# df = get_embeddings_zero_rows()
# df = get_and_update_embeddings_zero_rows()
# df = get_embeddings_zero_rows()
# df = get_user_news_views_data()

# if df is not None:
#     print(df.head())
# else:
#     print("데이터를 가져오지 못했습니다.")