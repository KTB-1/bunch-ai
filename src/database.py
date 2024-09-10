from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from config import MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE, setup_logging
import logging
import json

# 로그 설정
setup_logging()

# SQLAlchemy 기본 클래스 정의
Base = declarative_base()

# News 모델 정의
class News(Base):
    __tablename__ = 'News'
    
    news_id = Column(Integer, primary_key=True, autoincrement=True)
    category = Column(Text)
    news_url = Column(String(255), unique=True)
    title = Column(String(255))
    description = Column(Text)
    content = Column(Text)
    summary = Column(Text)
    publication_date = Column(String(255))
    embedding = Column(Integer)

# UserNewsViews 모델 정의
class UserNewsViews(Base):
    __tablename__ = 'UserNewsViews'
    
    view_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(255))
    news_id = Column(Integer, ForeignKey('News.news_id'))
    view_date = Column(String(255))

class DatabaseManager:
    def __init__(self):
        self.engine = None
        self.SessionLocal = None

    def init_db(self):
        connection_string = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"
        self.engine = create_engine(connection_string, pool_pre_ping=True)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def create_tables(self):
        Base.metadata.create_all(bind=self.engine)
        logging.info("테이블이 생성되었습니다 (이미 존재할 경우 무시됩니다).")

    def get_session(self):
        return self.SessionLocal()

    def close(self):
        if self.engine:
            self.engine.dispose()

db_manager = DatabaseManager()

def init_database():
    db_manager.init_db()
    db_manager.create_tables()

def save_news_to_database(news_data):
    try:
        with db_manager.get_session() as session:
            for news_item in news_data:
                existing_news = session.query(News).filter_by(news_url=news_item[1]).first()
                if not existing_news:
                    new_news = News(
                        category=news_item[0],
                        news_url=news_item[1],
                        title=news_item[2],
                        description=news_item[3],
                        publication_date=news_item[4]
                    )
                    session.add(new_news)
                    logging.info(f"새 뉴스 항목이 추가됨: {news_item[2]}")
                else:
                    logging.info(f"중복된 뉴스 항목 무시됨: {news_item[2]}")
            session.commit()
    except SQLAlchemyError as e:
        logging.error(f"데이터베이스 오류 발생: {e}")
        raise

def get_news_without_content():
    try:
        with db_manager.get_session() as session:
            return [news.news_url for news in session.query(News).filter((News.content == None) | (News.content == '')).all()]
    except SQLAlchemyError as e:
        logging.error(f"데이터베이스 조회 오류: {e}")
        raise

def update_news_content(news_url, content):
    try:
        with db_manager.get_session() as session:
            news = session.query(News).filter_by(news_url=news_url).first()
            if news:
                news.content = content
                session.commit()
                logging.info(f"뉴스 내용 DB에 업데이트 완료: {news_url}")
            else:
                logging.error(f"업데이트할 뉴스를 찾을 수 없음: {news_url}")
    except SQLAlchemyError as e:
        logging.error(f"데이터베이스 업데이트 오류: {e}")
        raise

def get_news_without_summary():
    try:
        with db_manager.get_session() as session:
            return session.query(News).filter(
                (News.summary == None) | (News.summary == ''),
                News.content != None
            ).all()
    except SQLAlchemyError as e:
        logging.error(f"데이터베이스 조회 오류: {e}")
        raise

def update_news_summary(news_id, summary):
    try:
        with db_manager.get_session() as session:
            news = session.query(News).filter_by(news_id=news_id).first()
            if news:
                news.summary = summary
                session.commit()
                logging.info(f"뉴스 요약 업데이트 완료: ID {news_id}")
            else:
                logging.error(f"업데이트할 뉴스를 찾을 수 없음: ID {news_id}")
    except SQLAlchemyError as e:
        logging.error(f"데이터베이스 업데이트 오류: {e}")
        raise

def get_decoded_summaries_modified_V1():
    try:
        with db_manager.get_session() as session:
            news_list = session.query(News).filter(
                News.summary != None,
                News.summary != '',
                (News.embedding == 0) | (News.embedding == None)
            ).all()

            if not news_list:
                return None

            decoded_summaries = []
            for news in news_list:
                try:
                    decoded_summary = json.loads(news.summary)
                    decoded_summaries.append({
                        'news_id': news.news_id,
                        'summary': decoded_summary
                    })
                    news.embedding = 1
                except json.JSONDecodeError as e:
                    logging.error(f"JSON 디코딩 오류 (news_id: {news.news_id}): {e}")
            
            session.commit()
            return decoded_summaries
    except SQLAlchemyError as e:
        logging.error(f"데이터베이스 조회/업데이트 오류: {e}")
        raise

def delete_news_entry(url):
    try:
        with db_manager.get_session() as session:
            news = session.query(News).filter_by(news_url=url).first()
            if news:
                session.delete(news)
                session.commit()
                logging.info(f"뉴스 항목이 삭제됨: {url}")
            else:
                logging.warning(f"삭제할 뉴스를 찾을 수 없음: {url}")
    except SQLAlchemyError as e:
        logging.error(f"데이터베이스에서 {url} 삭제 중 오류 발생: {str(e)}")
        raise

def close_database():
    db_manager.close()

def get_summary_lengths():
    try:
        with db_manager.get_session() as session:
            news_list = session.query(News).filter(
                News.summary.isnot(None),
                News.summary != ''
            ).all()

            summary_lengths = []
            for news in news_list:
                try:
                    summary = json.loads(news.summary)
                    lengths = {
                        'news_id': news.news_id,
                        'point_1_length': len(summary.get('point_1', '')),
                        'point_2_length': len(summary.get('point_2', '')),
                        'point_3_length': len(summary.get('point_3', '')),
                        'insight_length': len(summary.get('insight', ''))
                    }
                    summary_lengths.append(lengths)
                except json.JSONDecodeError as e:
                    logging.error(f"JSON 디코딩 오류 (news_id: {news.news_id}): {e}")

            return summary_lengths
    except SQLAlchemyError as e:
        logging.error(f"데이터베이스 조회 오류: {e}")
        raise

# 메인 실행 부분 (테스트용)
if __name__ == "__main__":
    init_database()
    # 테스트: summary 길이 가져오기
    summary_lengths = get_summary_lengths()
    
    for item in summary_lengths:
        print(f"News ID: {item['news_id']}")
        print(f"Point 1 length: {item['point_1_length']}")
        print(f"Point 2 length: {item['point_2_length']}")
        print(f"Point 3 length: {item['point_3_length']}")
        print(f"Insight length: {item['insight_length']}")
        print("---")

    # 각 포인트와 인사이트의 길이를 저장할 리스트 초기화
    point_1_lengths = []
    point_2_lengths = []
    point_3_lengths = []
    insight_lengths = []

    # 데이터에서 각 길이를 추출하여 리스트에 추가
    for item in summary_lengths:
        point_1_lengths.append(item['point_1_length'])
        point_2_lengths.append(item['point_2_length'])
        point_3_lengths.append(item['point_3_length'])
        insight_lengths.append(item['insight_length'])

    # 평균 계산 함수
    def calculate_average(lengths):
        return sum(lengths) / len(lengths)

    # 각 포인트와 인사이트의 평균 길이 계산
    avg_point_1 = calculate_average(point_1_lengths)
    avg_point_2 = calculate_average(point_2_lengths)
    avg_point_3 = calculate_average(point_3_lengths)
    avg_insight = calculate_average(insight_lengths)

    # 결과 출력
    print(f"point_1의 평균 길이: {avg_point_1:.2f}")
    print(f"point_2의 평균 길이: {avg_point_2:.2f}")
    print(f"point_3의 평균 길이: {avg_point_3:.2f}")
    print(f"insight의 평균 길이: {avg_insight:.2f}")
    
    # 최대 길이 계산
    max_point_1 = max(point_1_lengths)
    max_point_2 = max(point_2_lengths)
    max_point_3 = max(point_3_lengths)
    max_insight = max(insight_lengths)

    # 결과 출력
    print(f"point_1의 최대 길이: {max_point_1}")
    print(f"point_2의 최대 길이: {max_point_2}")
    print(f"point_3의 최대 길이: {max_point_3}")
    print(f"insight의 최대 길이: {max_insight}")
    close_database()