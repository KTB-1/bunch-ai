from lightfm import LightFM
from lightfm.data import Dataset
from lightfm.evaluation import auc_score
import numpy as np
from dbconnect import get_user_news_views_data

def make_matrix():
    df = get_user_news_views_data()

    # 사용자가 뉴스를 봤음을 나타내기 위해 view_date를 1로 설정
    df['view_date'] = 1

    # Pivot table 생성
    pivot_df = df.pivot_table(index='user_id', columns='news_id', values='view_date', fill_value=0)

    # 데이터 준비
    dataset = Dataset()
    dataset.fit(df['user_id'].unique(), df['news_id'].unique())

    (interactions, weights) = dataset.build_interactions([(x['user_id'], x['news_id'], x['view_date']) for index, x in df.iterrows()])

    # 모델 학습 (BPR)
    model = LightFM(loss='bpr')
    model.fit(interactions, epochs=30, num_threads=2)

    return model, interactions, dataset, pivot_df

# 추천 함수
def recommend_lightfm(model, userid, interactions, dataset, pivot_df, top_n=10):
    # 함수 내의 userid, newsid는 0-indexed
    # dataframe의 userid, newsid는 1-indexed
    n_users, n_items = interactions.shape

    # 모든 뉴스에 대한 점수를 예측
    scores = model.predict(userid - 1, np.arange(n_items))
    # print(scores)

    # 사용자가 이미 본 뉴스 아이디 가져오기
    user_interactions = pivot_df.loc[userid]
    seen_newsid = user_interactions[user_interactions > 0].index.tolist()
    seen_newsid = [x - 1 for x in seen_newsid]
    # print(seen_newsid)

    # 이미 본 뉴스 아이디는 제외하고 상위 추천 리스트 생성
    unseen_scores = [(i, score) for i, score in enumerate(scores) if i not in seen_newsid]
    unseen_scores.sort(key=lambda x: x[1], reverse=True)
    # print(unseen_scores)

    # 상위 N개 추천
    top_items = [item[0] for item in unseen_scores[:top_n]]

    # 뉴스 아이디 맵핑 복구
    newsid_map = dataset.mapping()[2]
    reverse_newsid_map = {v: k for k, v in newsid_map.items()}
    recommended_newsid = [reverse_newsid_map[item] for item in top_items]

    return recommended_newsid

def recc_matrix(userid, cnt):
    userID = userid
    topK = cnt

    (model, interactions, dataset, pivot_df) = make_matrix()
    recommended_newsid = recommend_lightfm(model, userID, interactions, dataset, pivot_df, top_n=topK)
    
    return recommended_newsid

recc_matrix(1, 3)

# userid 가 맵핑된 번호로 들어오면 오류 생길 수 있음 -> 고려해야함
#