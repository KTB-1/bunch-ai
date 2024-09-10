from lightfm import LightFM
from lightfm.data import Dataset
from lightfm.evaluation import auc_score
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from dbconnect import get_user_news_views_data

def make_matrix():
    df = get_user_news_views_data()

    if df is None or df.empty:
        return None, None, None, None

    # view_date를 datetime 형식으로 변환
    df['view_date'] = pd.to_datetime(df['view_date'], format='%Y-%m-%d %H:%M:%S')

    # 사용자가 뉴스를 봤음을 나타내기 위해 view_date를 1로 설정
    df['view_date'] = 1

    # user_id와 news_id를 각각 정수형 인덱스로 변환 (그리고 매핑 정보 저장)
    user_id_map = dict(enumerate(df['user_id'].astype('category').cat.categories))
    df['user_id'] = df['user_id'].astype('category').cat.codes
    news_id_map = dict(enumerate(df['news_id'].astype('category').cat.categories))
    df['news_id'] = df['news_id'].astype('category').cat.codes

    # Pivot table 생성
    pivot_df = df.pivot_table(index='user_id', columns='news_id', values='view_date', fill_value=0)

    # 데이터 준비
    dataset = Dataset()
    dataset.fit(df['user_id'].unique(), df['news_id'].unique())

    # 상호작용 데이터 생성
    interactions, weights = dataset.build_interactions([(x['user_id'], x['news_id'], x['view_date']) for index, x in df.iterrows()])

    # 모델 학습 (BPR)
    model = LightFM(loss='bpr')
    model.fit(interactions, epochs=30, num_threads=2)

    return model, interactions, dataset, pivot_df, user_id_map


# 추천 함수
def recommend_lightfm(model, userid, interactions, dataset, pivot_df, user_id_map, top_n=10):
    # userid가 문자열인 경우 매핑된 정수형 인덱스로 변환
    user_id_index = None
    for k, v in user_id_map.items():
        if v == userid:
            user_id_index = k
            break
    
    if user_id_index is None:
        raise ValueError(f"UserID '{userid}' not found in the dataset")

    # 모든 뉴스에 대한 점수를 예측
    n_users, n_items = interactions.shape
    scores = model.predict(user_id_index, np.arange(n_items))

    # 사용자가 이미 본 뉴스 아이디 가져오기
    user_interactions = pivot_df.loc[user_id_index]
    seen_newsid = user_interactions[user_interactions > 0].index.tolist()

    # 상위 N개 추천 (이미 본 뉴스 제외)
    unseen_scores = [(i, score) for i, score in enumerate(scores) if i not in seen_newsid]
    unseen_scores.sort(key=lambda x: x[1], reverse=True)

    top_items = [item[0] for item in unseen_scores[:top_n]]

    # 뉴스 아이디 맵핑 복구
    newsid_map = dataset.mapping()[2]
    reverse_newsid_map = {v: k for k, v in newsid_map.items()}
    recommended_newsid = [reverse_newsid_map[item] for item in top_items]

    return recommended_newsid


def recc_matrix(userid, cnt):
    (model, interactions, dataset, pivot_df, user_id_map) = make_matrix()

    if model is None:
        return list(range(0, cnt))

    recommended_newsid = recommend_lightfm(model, userid, interactions, dataset, pivot_df, user_id_map, top_n=cnt)

    return recommended_newsid


# recc_matrix(1, 3)

# userid 가 맵핑된 번호로 들어오면 오류 생길 수 있음 -> 고려해야함
#