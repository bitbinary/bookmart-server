from app import app
from utils.db import *
try:
    import pandas as pd
    import json
    from datetime import datetime
except ImportError as exc:
    os.system('python -m pip install {}'.format(exc.name),)
    os.system('python ./run.py')


def getTransactionSummary():
    conn = pg_connect()
    with conn.cursor() as c:
        result = pg_queryToDataFrame(
            "SELECT min(createdat) AS timestamp, COUNT(transactionid) AS count, sum(price) AS totalRevenue FROM sales GROUP BY transactionid")
        conn.commit()
        c.close()
        conn.close()
        if result.empty:
            return {'message': 'No Sales'}
        else:
            return {'sales': json.loads(result.to_json(orient='records')), 'message': 'Success'}


def getGenreSummary():
    conn = pg_connect()
    with conn.cursor() as c:
        result = pg_queryToDataFrame(
            "SELECT count(A.transactionid), B.genre FROM sales as A INNER JOIN books as B ON A.isbn = B.isbn group by B.genre;")
        conn.commit()
        c.close()
        conn.close()
        if result.empty:
            return {'message': 'No Sales'}
        else:
            return {'genres': json.loads(result.to_json(orient='records')), 'message': 'Success'}


def getTitleSummay():
    conn = pg_connect()
    with conn.cursor() as c:
        result = pg_queryToDataFrame(
            "SELECT A.createdat,B.title, count(*) FROM sales as A INNER JOIN books as B ON A.isbn = B.isbn GROUP BY A.createdat, B.title;")
        conn.commit()
        c.close()
        conn.close()
        if result.empty:
            return {'message': 'No Sales'}
        else:
            return {'topselling': json.loads(result.to_json(orient='records')), 'message': 'Success'}


def getAllPurchase():
    conn = pg_connect()
    with conn.cursor() as c:
        result = pg_queryToDataFrame("SELECT * FROM sales;")
        conn.commit()
        c.close()
        conn.close()
        if result.empty:
            return {'message': 'No Sales'}
        else:
            return {'purchase': json.loads(result.to_json(orient='records')), 'message': 'Success'}


def getAllUserRegistrations():
    db = firestore_db()
    limit = 1500  # Reduce this if it uses too much of your RAM

    def stream_collection_loop(collection, count, cursor=None):
        while True:
            # Very important. This frees the memory incurred in the recursion algorithm.
            docs = []
            result = []
            if cursor:
                docs = [snapshot for snapshot in
                        collection.limit(limit).order_by('__name__').start_after(cursor).stream()]
            else:
                docs = [snapshot for snapshot in collection.limit(
                    limit).order_by('__name__').stream()]

            for doc in docs:
                if doc.to_dict()['createdAt'] != 'null':
                    result.append(doc.to_dict()['createdAt'])
                # The `doc` here is already a `DocumentSnapshot` so you can already call `to_dict` on it to get the whole document.
                # process_data_and_log_errors_if_any(doc)
                count = count + 1

            if len(docs) == limit:
                cursor = docs[limit-1]
                continue

            return result
    result = stream_collection_loop(db.collection('Users'), 0)
    return {'timestamps': result, 'message': 'success'}
