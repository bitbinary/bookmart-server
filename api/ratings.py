from app import app
import pandas as pd
import numpy as np
from utils.db import pg_connect, pg_queryToDataFrame
import json
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

def sentiment_analyzer(text):
    vader_analyzer=SentimentIntensityAnalyzer()
    polarity=vader_analyzer.polarity_scores(text)
    sentiment_score=polarity['compound']
    if sentiment_score>=0.05:
        sentiment_label='Positive'
    elif sentiment_score<=-0.05:
        sentiment_label='Negative'
    else:
        sentiment_label='Neutral'
    return [sentiment_score,sentiment_label]

def review_existence(user_id,isbn):
    existing_reviews = pg_queryToDataFrame("SELECT * FROM review_rating WHERE isbn='{isbn}' and user_id='{user_id}';".format(isbn=isbn,user_id=user_id))
    if not existing_reviews.empty:
        return True
    else:
        return False

def writeReview(data,isbn):
    ISBN=isbn
    review_text=data['review_text']
    rating=data['rating']
    is_spoiler=data['is_spoiler']
    emotings=data['emotings']
    sentiment_score=999
    sentiment_label=""
    user_id=data['user_id']
    user_name=data['user_name']
    
    if not rating:
        rating=999
   
    if len(emotings)>0:
        emotings=','.join(emotings)
        print(emotings)

    if len(emotings)==0:
        emotings=""

    if len(review_text)>0:
        sentiment_bundle=sentiment_analyzer(review_text)
        sentiment_score=sentiment_bundle[0]
        sentiment_label=sentiment_bundle[1]

    #Validates if a review already exists
    if review_existence(user_id=user_id,isbn=ISBN):
        print('Thanks,but you alread reviewed this book!!')
        return {'message':'Thanks,but you already reviewed this book!!'}
    conn=pg_connect()
    with conn.cursor() as c:
        c.execute("INSERT INTO review_rating(ISBN,user_id,review_text,rating,is_spoiler,sentiment_score,sentiment_label,emotings,user_name) values('{ISBN}','{user_id}','{review_text}','{rating}','{is_spoiler}','{sentiment_score}','{sentiment_label}','{emotings}','{user_name}');".format(ISBN=ISBN,
        user_id=user_id,
        review_text=review_text,
        rating=rating,
        is_spoiler=is_spoiler,
        sentiment_score=sentiment_score,
        sentiment_label=sentiment_label,
        emotings=emotings,
        user_name=user_name))
        print('Review added successfully!!')
        conn.commit()
        c.close()
        conn.close()
        return {'message':'Success'}


def fetch_reviews(args,isbn,user_id):
    #Getting the Sentiment Filter Query from Request
    sentiment=args.get('sentiment')
    #PageNumber & ReviewsPerPage From request
    page = args.get('pageNumber')
    reviews_per_page=args.get('reviewsPerPage')
    #Initializing totalReviews and totalPages
    total_reviews=0
    total_pages=1
    #Fetching reviews for the particular book
    reviews_df=pg_queryToDataFrame("SELECT * FROM review_rating where isbn='{isbn}';".format(isbn=isbn))
    #When we have some reviews for the book
    if not reviews_df.empty:
        #Getting Total Reviews
        total_reviews=reviews_df.shape[0]
        #Computing the number of pages based on the total reviews and reviews per page
        total_pages=np.ceil(total_reviews/reviews_per_page)
        #Formatting String-Emotings into List
        reviews_df.emotings=reviews_df.emotings.apply(lambda x: x.split(',') if ',' in x else [x] if len(x)!=0 else [])
        #If a value was supplied for the sentiment parameter
        if sentiment:
            #Filter reviews based on sentiment
            reviews_df=reviews_df.query('sentiment_label==@sentiment')
        #Show select reviews based on page value
        reviews_to_show=reviews_df[reviews_per_page*(page-1):reviews_per_page*(page)]

        #convert df records to json
        reviews_json=reviews_to_show.to_json(orient='records')
        reviews_json=json.loads(reviews_json)
        already_reviewed=False
        if user_id:
            if review_existence(user_id=user_id,isbn=isbn):
                already_reviewed=True


        data={'reviews':reviews_json,
                'totalReviews':total_reviews,
                'totalPages':total_pages,
                'currentPage':page,
                'alreadyReviewed':already_reviewed}
        return data
    else:
        print('No body has reviewed this book yet!!')
        data={'reviews':[],
                'totalReviews':0,
                'totalPages':0,
                'currentPage':0,
                'alreadyReviewed':False}
        return data
