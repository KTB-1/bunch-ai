from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import pymysql
import json
from config import MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE
from datetime import datetime
from recc_by_matrix import recc_matrix
from embed_news import recc_item, http_recc_item
from dbconnect import get_decoded_summaries, create_connection_mariadb, update_db_get_by_full
import numpy as np
import random

app = Flask(__name__)

# MariaDB 데이터베이스 설정
user = MYSQL_USER
password = MYSQL_PASSWORD
host = MYSQL_HOST
port = MYSQL_PORT
database_name = MYSQL_DATABASE

app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{user}:{password}@{host}:{port}/{database_name}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

pre_fill = datetime(2024, 9, 1)

# News 모델 정의
class News(db.Model):
    __tablename__ = 'News'
    news_id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.Text)
    news_url = db.Column(db.String(255))
    title = db.Column(db.String(255))
    description = db.Column(db.Text)
    content = db.Column(db.Text)
    summary = db.Column(db.Text)  # JSON 인코딩된 텍스트
    publication_date = db.Column(db.String(255))
    embedding = db.Column(db.Integer)

# API 엔드포인트 정의
@app.route('/get_recommendations', methods=['POST'])
def get_recommendations():
    global pre_fill

    data = request.get_json()
    userid = data.get('userid')
    cnt = data.get('cnt', 5)  # 기본값으로 5개 추천
    print(userid, cnt)
    if userid is None:
        return jsonify({"error": "userid is required"}), 400
    
    engine = create_connection_mariadb()
    pre_fill = update_db_get_by_full(engine, pre_fill)
    print(f"Updated pre_fill: {pre_fill}")
    
    # 추천 리스트 가져오기
    recommended_newsid1 = recc_matrix(userid, cnt)
    recommended_newsid2 = recc_item(userid, cnt)
    print(userid, recommended_newsid1, recommended_newsid2)
    # recommended_newsid2 = http_recc_item(userid, cnt)

    tmp_newsid = recommended_newsid1 + recommended_newsid2
    tmp_newsid = random.sample(tmp_newsid, cnt)
    recommended_newsid = list(set(tmp_newsid))

    summaries = get_decoded_summaries(recommended_newsid)
    
    # 결과 반환
    return jsonify({"recommendations": summaries})

# 앱 실행
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

# curl -X POST -H "Content-Type: application/json" -d '{"userid": 1, "cnt": 3}' http://localhost:5000/get_recommendations