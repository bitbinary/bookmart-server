from app import app
from utils.db import pg_queryToDataFrame
import json

def getPersonalizedRecommendations(user_id):
    list_of_isbns=pg_queryToDataFrame("SELECT recommendations from recommendations where user_id='{user_id}' order by created_at desc limit 1;".format(user_id=user_id))
    if list_of_isbns.empty:
        top_rated_books=pg_queryToDataFrame('SELECT * FROM books order by rating>=4.8')
        recommended_books=top_rated_books.sample(10)
        rec_books_json_str = recommended_books.to_json(orient='records')
        recommendations=json.loads(rec_books_json_str)
        return recommendations
    else:
        list_of_isbns=list(list_of_isbns.recommendations.values)
        list_of_isbns=list_of_isbns[0].split(',')
        recommended_books=pg_queryToDataFrame('SELECT * FROM BOOKS where isbn in {}'.format(tuple(list_of_isbns)))
        rec_books_json_str = recommended_books.to_json(orient='records')
        recommendations=json.loads(rec_books_json_str)
        return recommendations


