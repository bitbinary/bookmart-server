from app import app
import pandas as pd
from utils.db import pg_connect, pg_queryToDataFrame
import json
from datetime import datetime
from faker import Faker

# This API adds the book to the cart
def addToCart(data):
    # get ISBN and User from the post data
    ISBN=data['ISBN']
    user_id=data['user_id']
    # get current timestamp
    added_at = pd.to_datetime(datetime.today())
    # check whether the user has already carted 
    BookInCart = pg_queryToDataFrame("SELECT * FROM cart WHERE isbn='{isbn}' and user_id='{user_id}';".format(isbn=ISBN,user_id=user_id))
    if BookInCart.empty:
        conn=pg_connect()
        with conn.cursor() as c:
            # Inserting the book ISBN with userid to the cart
            c.execute("INSERT INTO cart (isbn,user_id,added_at) values('{ISBN}','{user_id}','{added_at}');".format(
                ISBN = ISBN,
                user_id = user_id,
                added_at = added_at
            ))
            print('Book added in Cart successfully!!')
            conn.commit()
            c.close()
            conn.close()
            return {'message':'Success'}
    else:
        return {'message':'Failed'}

# This API removes the book from a cart for user
def removeFromCart(user_id, isbn):
    if user_id and isbn:
        # Check whether the user has already carted the  book
        BookInCart = pg_queryToDataFrame("SELECT * FROM cart WHERE isbn='{isbn}' and user_id='{user_id}';".format(isbn=isbn,user_id=user_id))
        if not BookInCart.empty:
            conn=pg_connect()
            with conn.cursor() as c:
                # Deleteing the Book User entry from Cart
                c.execute("DELETE FROM cart WHERE isbn = '{isbn}' AND user_id = '{user_id}';".format(
                    isbn = isbn,
                    user_id = user_id,
                ))
                print('Book removed from Cart successfully!!')
                conn.commit()
                c.close()
                conn.close()
                return {'message':'Book removed from Cart successfully!!'}
        else:
            return {'message':'Book not in Cart'}
    else:
        return {'message':'ISBN or user is empty'}

# get all the books that user has carted.
def getCartList(user_id):
    if user_id:
        cart = pg_queryToDataFrame("SELECT * FROM cart WHERE user_id='{user_id}';".format(user_id=user_id))
        if not cart.empty:
            result  = pg_queryToDataFrame("SELECT A.added_at , B.isbn, B.title, B.author, B.publicationyear, B.bookimage, B.numpages, B.rating, B.genre, B.bookurl, B.language, B.synopsis, B.price FROM cart as A INNER JOIN books as B ON A.isbn = B.isbn where A.user_id = '{user_id}';".format(user_id = user_id))
            if result.empty:
                return {"success":True,'message':'Books not found'}
            else:
                return {'data': json.loads(result.to_json(orient='records')),'message':'Cart Items Collected', "success":True}					
        else:
            return {'message':'Cart is Empty', "success":True,}
    else:
        return {'message':'Not Authorized', "success":False,}

# This create a new transactionID for an order
def getNewTransactionID():
    faker=Faker()
    transactionId=faker.iban()[:9]
    return transactionId
    
# This API is purchase a book, It also removes the book from the cart if the book was carted
def buyBook(data):
    ISBN = data['isbnList']
    user_id = data['user_id']
    createdat = pd.to_datetime(datetime.today())
    transactionIDList = pg_queryToDataFrame("SELECT transactionid FROM sales;")
    newTransactionID = getNewTransactionID() 
    while(newTransactionID in transactionIDList):
        newTransactionID = getNewTransactionID() 

    if len(ISBN)>1:
        purchasedBook = pg_queryToDataFrame("SELECT * FROM sales WHERE isbn in {isbn} and userid = '{user_id}';".format(isbn=tuple(ISBN),user_id=user_id))
    else:
        purchasedBook = pg_queryToDataFrame("SELECT * FROM sales WHERE isbn = '{isbn}' and userid = '{user_id}';".format(isbn=ISBN[0],user_id=user_id))
    if purchasedBook.empty:
        conn=pg_connect()
        with conn.cursor() as c:
            for i in range(len(ISBN)):
                price = pg_queryToDataFrame("SELECT price FROM books WHERE isbn = '{isbn}';".format(isbn=ISBN[i]))
                price = price['price'][0]
                c.execute("INSERT INTO sales (isbn, createdat, transactionid, price, userid) VALUES ('{isbn}', '{createdat}', '{transactionid}', '{price}', '{userid}');".format(isbn = ISBN[i], userid = user_id, createdat = createdat, price = price, transactionid = newTransactionID))
                removeFromCart(user_id,ISBN[i])
            conn.commit()
            c.close()
            conn.close()
            return {'message':'Purchased Book'}
    else:
        return {'message':'Some of the books Already bought'}
