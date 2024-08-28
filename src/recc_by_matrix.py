import pymysql
import pandas as pd
from sqlalchemy import create_engine
import chromadb
from langchain_ollama import OllamaEmbeddings
from sklearn.metrics.pairwise import cosine_similarity

# need to modify to match DB
# need some changes for "cold start" problem and "new item income" problem and ..
df = pd.read_csv('/Users/yangtaegyu/test/TeamProject1/ratings_small.csv')

df = df[df['movieId'] <= 10000]

print(len(df))

pivot_df = df.pivot_table(index='userId', columns='movieId', values='rating', fill_value=0)

# 결과 확인
print(pivot_df.head)

# 사용자 간 유사도 계산 (cosine similarity)
user_similarity = cosine_similarity(pivot_df)

# 유사도 결과를 DataFrame으로 변환
user_similarity_df = pd.DataFrame(user_similarity, index=pivot_df.index, columns=pivot_df.index)

# 결과 확인
print(user_similarity_df)

# user1과 다른 사용자들의 유사도 확인
user1_similarities = user_similarity_df.loc[1]

# user1과 유사한 상위 5명 추출 (자기 자신은 제외)
top_5_similar_users = user1_similarities.drop(1).nlargest(5)

# 결과 출력
print(top_5_similar_users)