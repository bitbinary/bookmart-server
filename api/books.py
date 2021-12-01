from app import app
from utils.db import *
try:
	import pandas as pd
	import json
	from datetime import datetime
except ImportError as exc:
    os.system('python -m pip install {}'.format(exc.name),)
    os.system('python ./run.py')

# This Api returns the 12 books that have been sold in the last week
def getTopSellers():
	date_column = 'createdAt'
	today = pd.to_datetime(datetime.today())
	# getting the last weeks sales data
	lastWeekData = pg_queryToDataFrame("SELECT * FROM sales WHERE date_part('year', createdat)=date_part('year',now()) AND date_part('week', createdat)=date_part('week',now())-1")
	if len(lastWeekData)>0:
		# identifying the ISBN of top 12 books in last week 
		topIsbns = tuple(lastWeekData.isbn.value_counts()[:12].index.values)
		# getting the deltais of the top 12 books
		topBooks = pg_queryToDataFrame("SELECT * FROM books WHERE isbn IN {};".format(topIsbns))
		# converting the the dataframe to json 
		jsonStr = topBooks.to_json(orient='records')
		ds = json.loads(jsonStr)
		return ds
	#When there is no sales in the previous week, all time best sellers are shown
	else: 
		allTimeSellers = pg_queryToDataFrame("select isbn,count(distinct userid) as cnt from sales group by 1 order by cnt desc limit 12;")
		topIsbns=tuple(allTimeSellers.isbn.values)
		topBooks = pg_queryToDataFrame("SELECT * FROM books WHERE isbn IN {};".format(topIsbns))
		jsonStr = topBooks.to_json(orient='records')
		ds = json.loads(jsonStr)
		return ds

# this function is used in the get emoticons for a book  
def getEmotings(isbn):
	# get all the emoticons received in for a book
	emotings = pg_queryToDataFrame("SELECT emotings FROM review_rating where isbn='{isbn}';".format(isbn=isbn))
	emotings['emotings'] = emotings['emotings'].apply(lambda x: x.split(',') if ',' in x else [x]) 
	emotings = emotings.explode('emotings')
	# calculate the perecntage of each emoticons to the total of all the emoticons
	emotings100 = emotings.value_counts(normalize=True).mul(100).round(1).astype(str) + '%'
	emotingsjson = eval(emotings100.to_json(orient='index'))
	# Modifying the keys in the right format 
	for key in list(emotingsjson.keys()):
		new_key = eval(key)[0]
		emotingsjson[new_key] = emotingsjson[key]
		del emotingsjson[key]
	return emotingsjson

#  this API gives book details for a requested ISBN
def getBookById(user_id,isbn):
	if isbn:
		flag = 'False'
		ispurchased = False
		iscarted = False
		# Here the code is checking whether the book was purchased or carted by a user
		if user_id:
			cart = pg_queryToDataFrame("SELECT * FROM cart WHERE isbn='{isbn}' and user_id='{user_id}';".format(isbn=isbn,user_id=user_id))
			if not cart.empty:
				flag = 'Cart'
				iscarted = True
			purchased = pg_queryToDataFrame("SELECT * FROM sales WHERE isbn='{isbn}' and userid='{user_id}';".format(isbn=isbn,user_id=user_id))
			if not purchased.empty:
				flag = 'Purchased'
				ispurchased = True
		# getting the book details from book table 
		books = pg_queryToDataFrame("SELECT * FROM books WHERE isbn='{isbn}';".format(isbn=isbn))
		#  Adding the flags and emoticons for the to book and returning it as JSON to fronend.
		if not books.empty:
			emotings = getEmotings(isbn)
			books['flag'] = flag
			books['ispurchased'] = ispurchased
			books['iscarted'] = iscarted
			bookJson = books.to_json(orient='records')
			ds = json.loads(bookJson)
			ds[0]['emotings'] = eval(json.dumps(emotings)) 
			return {'books':ds[0], 'message':'Success'}
		else:
			return {'message':'ISBN not Valid'}
	else:
		return {'message':'ISBN is empty'}

# this API provied the user with all the books that he has bought 
def getBookByUserId(user_id):
	if user_id:
		result  = pg_queryToDataFrame("SELECT A.createdat , B.isbn, B.title, B.author, B.publicationyear, B.bookimage, B.numpages, B.rating, B.genre, B.bookurl, B.language, B.synopsis, B.price FROM sales as A INNER JOIN books as B ON A.isbn = B.isbn where A.userid = '{user_id}';".format(user_id = user_id))
		if result.empty:
			return {'message':'Books not found'}
		else:
			return {'books': json.loads(result.to_json(orient='records')),'message':'Success'}					
	else:
		return {'message':'Failed'}

# This API can be used if the user want's to delete a purchased book.(Not in the user stories So haven't integrated with the frontend)
def removeFromPurchasedBook(user_id, isbn):
	#  checking whether the input parameter are given
	if user_id and isbn:
		# Checking Whether user has purchased the books
		Bookpurchased = pg_queryToDataFrame("SELECT * FROM sales WHERE isbn='{isbn}' and userid='{user_id}';".format(isbn=isbn,user_id=user_id))
		if not Bookpurchased.empty:
			conn=pg_connect()
			with conn.cursor() as c:
				# Since the user has purchased the book. we will now delete it from the sales table
			    c.execute("DELETE FROM sales WHERE isbn = '{isbn}' AND userid = '{user_id}';".format(
			    	isbn = isbn,
				    user_id = user_id,
			    ))
			    print('Book removed from My Purchase successfully!!')
			    conn.commit()
			    c.close()
			    conn.close()
			    return {'message':'Success'}
		else:
			return {'message':'Book not in Purchase'}
	else:
		return {'message':'ISBN or user is empty'}

# This Api is used to get the  URL of EPUB book which sotred in S3
def getBookUrl(user_id,isbn):
	if user_id:
		if isbn:
			Bookpurchased = pg_queryToDataFrame("SELECT * FROM sales WHERE isbn='{isbn}' and userid='{user_id}';".format(isbn=isbn,user_id=user_id))
			if not Bookpurchased.empty:

				book_url=pg_queryToDataFrame("select bookurl from books where isbn='{isbn}'".format(isbn=isbn))
				
				if (not book_url.empty) or (book_url):
					return {"success":True,
					'bookurl':book_url['bookurl'][0]},200
				else:
					return {"success":False,
					'message':'Book not found'},400
			else:
				return {'success':False,
				'message':'Book not purchased'},400
				
