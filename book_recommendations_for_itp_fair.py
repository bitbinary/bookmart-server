# -*- coding: utf-8 -*-
"""Book Recommendations for ITP - Fair.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1HiLab-dat1oIcl6HBIaRUEFQkFwnqTqW

Please mount the Google drive by running the block below and following the prompts.
"""

from utils.db import *
import pandas as pd 
import numpy as np
from nltk.corpus import stopwords
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfVectorizer
from surprise import Reader,Dataset
from surprise import SVD, NMF, model_selection, accuracy
from surprise.model_selection import GridSearchCV
from collections import defaultdict
from datetime import datetime

#Rating Data From Platform
users_from_platform=pg_queryToDataFrame("SELECT user_id,isbn,rating FROM review_rating where length(user_id)>20")
books=pg_queryToDataFrame("SELECT isbn,title from books")
#Rating Data from Kaggle
rating_data=pd.read_csv('./recommendation_engine/filtered_rating_data.csv')
rating_data.rename({'ISBN':'isbn'},axis=1,inplace=True)



rating_data.user_id=rating_data.user_id.astype('str')
#Combining Data From Platform and Kaggle for training
rating_data=pd.concat([rating_data,users_from_platform])
#Merging with book data to get book titles based on ISBN
books_filtered_data=pd.merge(left=rating_data,right=books[['isbn','title']],how='left')


#Approach: First, we will train on 80% of the data and use cross-validation to find hyper-parameters & then train on the whole data for making future predictions

# Establishing the rating scale
reader = Reader(rating_scale=(0.5, 5))
# Loading the dataset
data = Dataset.load_from_df(rating_data, reader)

# splitting the dataset into train (80%) and test (20%)
trainset, testset = model_selection.train_test_split(data, test_size=0.2)

### Fine-tune Surprise SVD model useing GridSearchCV
param_grid = {'n_factors': list(range(10,100)), 'lr_all': [0.001, 0.005, 0.01], 'reg_all': [0.01, 0.02, 0.04]}
# Optimize SVD algorithm for both root mean squared error ('rmse') and mean average error ('mae')
gs = GridSearchCV(SVD, param_grid, measures=['rmse', 'mae'], cv=5)

# Commented out IPython magic to ensure Python compatibility.
gs.fit(data)

#Getting the model with best combination of hyper-parameters optimized to lowest RMSE
model = gs.best_estimator['rmse']

print(gs.best_score['rmse'])
print(gs.best_params['rmse'])

model_selection.cross_validate(model, data, measures=['rmse', 'mae'], cv=5, verbose=True)

trainset = data.build_full_trainset()
model.fit(trainset) # re-fit on only the training data using the best hyperparameters
test_pred = model.test(testset)
print("SVD : Test Set")
accuracy.rmse(test_pred, verbose=True)

testset = trainset.build_anti_testset()

predictions = model.test(testset)

#Filtering out real users
actual_users=users_from_platform.user_id.unique()
#Getting their purchasedata
purchase_data=pg_queryToDataFrame('SELECT * FROM SALES WHERE userid in {}'.format(tuple(actual_users)))
#Boiler Plate for Getting Top N predictions obtained from Scikit-Surprise Website

def get_top_n(predictions, n=10):
  
    """Return the top-N recommendation for each user from a set of predictions.

    Args:
        predictions(list of Prediction objects): The list of predictions, as
            returned by the test method of an algorithm.
        n(int): The number of recommendation to output for each user. Default
            is 10.

    Returns:
    A dict where keys are user (raw) ids and values are lists of tuples:
        [(raw item id, rating estimation), ...] of size n.
    """

    # First map the predictions to each user.
    top_n = defaultdict(list)
    for uid, iid, true_r, est, _ in predictions:
        #Check if the user has purchased any books
        if uid in set(purchase_data.userid):
            #Excluding the purchased books from the recommendation list
          if iid in purchase_data.query('userid in @uid').isbn.unique():
            continue
          else:  
            top_n[uid].append((iid, est))
        else:
          top_n[uid].append((iid, est))

    # Then sort the predictions for each user and retrieve the k highest ones.
    for uid, user_ratings in top_n.items():
        user_ratings.sort(key=lambda x: x[1], reverse=True)
        top_n[uid] = user_ratings[:n]

    return top_n

top_n = get_top_n(predictions, n=10)

top_n = get_top_n(predictions, n=10)


#Preparing data for insertion
recommendations_to_insert=[]
for user in actual_users:
  rec_isbns=top_n[user]
  rec_isbns=[rec[0] for rec in rec_isbns]
  stringified_rec_isbns=','.join(rec_isbns)
  recommendations_to_insert.append((user,stringified_rec_isbns))

conn=pg_connect()
query="INSERT INTO RECOMMENDATIONS (USER_ID,RECOMMENDATIONS,created_at) VALUES " +",".join("(%s, %s, now())" for _ in recommendations_to_insert)
flattened_list=[item for sublist in recommendations_to_insert for item in sublist]                                                                                          
with conn.cursor() as c:
  if len(recommendations_to_insert)==0:
    print('Not expected')
  else:
    c.execute(query,flattened_list) 
    c.close()
    conn.commit()
    conn.close()
    
    
print('Hurray!!')