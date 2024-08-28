import pandas as pd
from sqlalchemy import create_engine, text
import logging
from config import MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE
from config import setup_logging

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

def get_and_update_embedding_zero_rows():
    engine = create_connection_mariadb()
    
    try:
        # SQL 쿼리 실행하여 embeddings 값이 0인 행을 가져옴
        query = "SELECT * FROM News WHERE embedding IS NULL"
        df = pd.read_sql(query, con=engine)
        
        # 가져온 데이터가 있으면 embeddings 값을 1로 업데이트
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

# df = get_embeddings_zero_rows()
# df = get_and_update_embeddings_zero_rows()
# df = get_embeddings_zero_rows()
df = get_user_news_views_data()

if df is not None:
    print(df.head())
else:
    print("데이터를 가져오지 못했습니다.")