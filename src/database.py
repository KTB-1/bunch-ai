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
    news_url = Column(String(255))
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
            news_items = session.query(News).filter(
                (News.summary == None) | (News.summary == ''),
                News.content != None
            ).all()
            if not news_items:
                logging.info(f"요약할 뉴스가 없습니다. news_items = {news_items}")
            return news_items
    except SQLAlchemyError as e:
        logging.error(f"데이터베이스 조회 오류: {e}")
        return []   # 오류 발생 시 빈 리스트 반환

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

def close_database():
    db_manager.close()

# 메인 실행 부분 (테스트용)
if __name__ == "__main__":
    init_database()
    # 여기에 필요한 테스트 코드를 추가할 수 있습니다.
    close_database()