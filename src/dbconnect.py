import pandas as pd
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, DateTime, BigInteger, Boolean, text
from sqlalchemy.orm import sessionmaker
import random
from datetime import datetime, timedelta
import logging
from config import MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE, FULLSTACK_DATABASE
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

    logging.info("aiDB 데이터베이스 연결 성공")

    return engine

def create_connection_fulldb():
    # MariaDB 연결 정보 설정
    user = MYSQL_USER
    password = MYSQL_PASSWORD
    host = MYSQL_HOST
    port = MYSQL_PORT
    database_name = FULLSTACK_DATABASE

    connection = None

    # SQLAlchemy 연결 문자열 생성
    connection_string = f"mysql+pymysql://{user}:{password}@{host}:{port}/{database_name}"

    # SQLAlchemy 엔진 생성
    engine = create_engine(connection_string)

    logging.info("fullstackDB 데이터베이스 연결 성공")

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

        cutoff_date = datetime.now() - timedelta(days=10)
        cutoff_date_str = cutoff_date.strftime('%Y-%m-%d %H:%M:%S')

        # SQL 쿼리 실행
        query = f"""
            SELECT * FROM UserNewsViews 
            WHERE user_id = '{user_id}' 
            AND view_date >= '{cutoff_date_str}'
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
        # 현재 시간으로부터 10일 전의 날짜 계산
        cutoff_date = datetime.now() - timedelta(days=10)
        cutoff_date_str = cutoff_date.strftime('%Y-%m-%d %H:%M:%S')

        # SQL 쿼리 실행하여 UserNewsViews 테이블의 모든 데이터를 가져옴
        query = f"""
            SELECT * FROM UserNewsViews
            WHERE view_date >= '{cutoff_date_str}'
        """
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

from faker import Faker

def create_fullstack_table(engine):
    metadata = MetaData()

    urls = Table(
        'urls', metadata,
        Column('url_id', BigInteger, primary_key=True, autoincrement=True),
        Column('created_at', DateTime, default=datetime.now),
        Column('updated_at', DateTime, default=datetime.now, onupdate=datetime.now),
        Column('is_deleted', Boolean, default=False),
        Column('url', String(255), nullable=False),
        Column('user_id', String(255), nullable=False),
    )

    # 테이블 생성
    metadata.create_all(engine)

def insert_fullstack_dummy(engine, num_records=20):
    # 세션 생성
    Session = sessionmaker(bind=engine)
    session = Session()

    # Faker 객체 생성
    faker = Faker()

    # url data
    urls = [
        "https://www.businessplus.kr/news/articleView.html?idxno=69475",
        "https://news.heraldcorp.com/view.php?ud=20240910050221",
        "https://www.etoday.co.kr/news/view/2399475",
        "https://news.heraldcorp.com/view.php?ud=20240910050220",
        "https://www.yna.co.kr/view/PYH20240910052700013?input=1196m",
        "https://www.dailian.co.kr/news/view/1405637/?sc=Naver",
        "https://www.sedaily.com/NewsView/2DE8LIM9EI",
        "https://biz.chosun.com/stock/stock_general/2024/09/10/67KRQLMY75FAXOXXOR22C2OXHY/?utm_source=naver&utm_medium=original&utm_campaign=biz",
        "http://www.ferrotimes.com/news/articleView.html?idxno=36690",
        "https://www.straightnews.co.kr/news/articleView.html?idxno=253359",
    ]

    # 더미 데이터 생성 및 삽입
    with engine.connect() as connection:
        trans = connection.begin()
        try:
            for it in range(num_records):
                is_deleted = random.choice([0, 1])  # is_deleted는 0 또는 1
                url = urls[it % 10]  # url 리스트에서 순서대로 가져옴
                user_id = faker.user_name()  # 랜덤 사용자 ID 생성

                # 데이터 삽입 쿼리
                insert_query = text(f"""
                INSERT INTO urls (created_at, updated_at, is_deleted, url, user_id)
                VALUES (:created_at, :updated_at, :is_deleted, :url, :user_id)
                """)

                # 실행 시 매개변수 바인딩
                connection.execute(insert_query, {
                    'created_at': datetime.now(),
                    'updated_at': datetime.now(),
                    'is_deleted': is_deleted,
                    'url': url,
                    'user_id': user_id
                })

                # print('end')
            trans.commit()
        except:
            trans.rollback()
            raise

    # 세션 커밋
    session.commit()
    session.close()

def update_db_get_by_full(engine_full, engine_ai, pre_fill):
    Session_full = sessionmaker(bind=engine_full)
    session_full = Session_full()
    Session_ai = sessionmaker(bind=engine_ai)
    session_ai = Session_ai()

    # 테이블 정의 (이미 테이블이 정의되어 있다고 가정)
    metadata = MetaData()
    urls = Table('urls', metadata, autoload_with=engine_full)
    news = Table('News', metadata, autoload_with=engine_ai)
    user_news_views = Table('UserNewsViews', metadata, autoload_with=engine_ai)

    # 1. URLs 테이블에서 is_deleted가 0이고, pre_fill 이후에 생성된 데이터를 조회
    recent_urls_query = session_full.query(urls).filter(
        urls.c.is_deleted == 0,
        urls.c.created_at > pre_fill
    )

    recent_urls = recent_urls_query.all()

    # 2. News 테이블과 URL을 비교하여 처리
    for url_data in recent_urls:
        # News 테이블에서 url과 일치하는 데이터 조회
        news_match = session_ai.query(news).filter(news.c.news_url == url_data.url).first()

        if news_match:
            # 일치하는 뉴스 데이터가 있는 경우 UserNewsViews 테이블에 삽입
            insert_query = user_news_views.insert().values(
                user_id=url_data.user_id,
                news_id=news_match.news_id,
                view_date=url_data.created_at  # created_at을 view_date로 사용
            )
            session_ai.execute(insert_query)

    # pre_fill 업데이트: 함수가 끝난 시점의 시간으로 업데이트
    pre_fill = datetime.now()

    # 변경사항 커밋
    session_full.commit()
    session_full.close()
    session_ai.commit()
    session_ai.close()

    # pre_fill 값을 반환하여 main 함수에서 사용
    return pre_fill

def main():
    # engine = create_connection_fulldb()
    # create_fullstack_table(engine)  # 테이블이 없는 경우에만 실행
    # insert_fullstack_dummy(engine, num_records=20)  # 100개의 더미 데이터 생성
    # print('test')
    pre_fill = datetime(2024, 9, 1)  # 초기 pre_fill 값 설정
    engine_full = create_connection_fulldb()
    engine_ai = create_connection_mariadb()
    pre_fill = update_db_get_by_full(engine_full, engine_ai, pre_fill)
    print(f"Updated pre_fill: {pre_fill}")


if __name__ == "__main__":
    
    main()

# df = get_embeddings_zero_rows()
# df = get_and_update_embeddings_zero_rows()
# df = get_embeddings_zero_rows()
# df = get_user_news_views_data()

# if df is not None:
#     print(df.head())
# else:
#     print("데이터를 가져오지 못했습니다.")