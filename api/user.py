from numpy.lib.function_base import select
from app import app
from utils.db import *
try:
	import pandas as pd
	import json
	from datetime import datetime
	import psycopg2
except ImportError as exc:
    os.system('python -m pip install {}'.format(exc.name),)
    os.system('python ./run.py')

def recentlyViewed(user, args):
	user_id = user
	isbn = args.get('isbn')
	
	viewed_at = pd.to_datetime(datetime.today())
	df = pg_queryToDataFrame("SELECT * FROM recently_viewed where user_id='{user_id}';".format(user_id=user_id))
	operation = ''
	# db = DB()
	try:
		conn = pg_connect()
		with conn.cursor() as c:
			if df.empty or df.shape[0]<10:
				if isbn in list(df['isbn']):
					# db.update('recently_viewed').set(viewed_at=viewed_at).where(isbn=isbn, user_id=user_id).execute()
					# db.commit()
					# db.close()
					operation = "updated a row"
					c.execute("UPDATE recently_viewed SET viewed_at='{viewed_at}' WHERE isbn='{isbn}' AND user_id='{user_id}';".format(user_id=user_id, isbn=isbn, viewed_at=viewed_at))
				else:
					c.execute("INSERT INTO recently_viewed(isbn, user_id, viewed_at) VALUES ('{isbn}', '{user_id}', '{viewed_at}') RETURNING *".format(user_id=user_id, isbn=isbn, viewed_at=viewed_at))
					operation = "Inserted a row"
			else:
				if isbn in list(df['isbn']):
					operation = "updated a row"
					c.execute("UPDATE recently_viewed SET viewed_at='{viewed_at}' WHERE isbn='{isbn}' AND user_id='{user_id}';".format(user_id=user_id, isbn=isbn, viewed_at=viewed_at))
				else:
					user_id_1 = df['user_id'][0]
					isbn_1 = df['isbn'][0]
					c.execute("UPDATE recently_viewed SET isbn='{isbn}', user_id='{user_id}', viewed_at='{viewed_at}' WHERE isbn='{isbn_1}' AND user_id='{user_id_1}';".format(user_id=user_id, isbn = isbn, user_id_1 = user_id_1, isbn_1 = isbn_1, viewed_at = viewed_at))
					operation = "Replaced a row"
			conn.commit()
	except (Exception, psycopg2.Error) as error:
		operation = "Failed"
		print("Error while fetching data FROM PostgreSQL", error)
	finally:
		if conn:
			c.close()
			conn.close()
			print("PostgreSQL connection is closed")
	return operation

def getRecentlyViewed(user):
	user_id = user
	books = pg_queryToDataFrame("SELECT b.* FROM books b,recently_viewed r WHERE b.isbn=r.isbn AND r.user_id='{user_id}' order by r.viewed_at desc".format(user_id=user_id))
	if not books.empty:
		books_json = books.to_json(orient="records")
		data=json.loads(books_json)
		return data
	else:
		return "Books Not Found"