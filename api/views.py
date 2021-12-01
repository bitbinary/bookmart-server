from flask import request, jsonify
from api.searchSortFilter import searchSortFilter
from api.books import getTopSellers, getBookById, getBookByUserId, removeFromPurchasedBook,getBookUrl
from api.user import recentlyViewed, getRecentlyViewed
from api.cart import addToCart, removeFromCart, getCartList, buyBook
from api.dashboard import getTransactionSummary, getGenreSummary, getTitleSummay, getAllPurchase,getAllUserRegistrations
from api.recommendations import getPersonalizedRecommendations
from api.ratings import *
from app import app, api
from flask_restx import Resource, abort, marshal, reqparse, fields, inputs
from models import *
from utils.db import *

import firebase_admin
import pyrebase
from firebase_admin import credentials, auth
import json
from flask import Flask, request
from functools import wraps
import werkzeug
import boto3
import configparser

books = api.namespace('books',
                      description='Books related operation')
user = api.namespace('users',
                     description='Users related operation')

rev = api.namespace('reviews', description='Reviews and Ratings')

cart = api.namespace('cart', description='Books in Cart')

sale = api.namespace('sales', description='Books Bought')

admin = api.namespace('admin', description='Admin Functionalities')

rec=api.namespace('recommendations',description='Get Personalized Recommendations')


# review_inputs_parser = reqparse.RequestParser()
# review_inputs_parser.add_argument('ISBN')
# review_inputs_parser.add_argument('review_text')
# review_inputs_parser.add_argument('rating',type=float,default=5.0)
# review_inputs_parser.add_argument('spoiler',type=inputs.boolean,default=False)

parser = reqparse.RequestParser()
parser.add_argument('orderBy', choices=['price', 'rating'])
parser.add_argument('ascending', type=inputs.boolean, default=True)
parser.add_argument('resultsPerPage', type=int, default=12)
parser.add_argument('pageNumber', type=int, default=1)
parser.add_argument('numberOfPages', type=int, default=1)
parser.add_argument('genres', action='append')
parser.add_argument('search')
parser.add_argument('price', type=float, action='append')
parser.add_argument('rating', type=float, action='append')


@books.route('/allbooks')
@books.doc(parser=parser)
class BooksList(Resource):
    @books.doc(description='get all the books by some order')
    @books.response(200, 'Success')
    @books.response(400, 'Failure', ErrorMsgModel)
    # @books.marshal_with(BookListModel, envelope='resource')
    def get(self):
        # args = GetBookList().load(request.args)
        args = parser.parse_args()
        result = searchSortFilter(args)
        data = {
            'books': result[0],
            'totalResults': result[1],
            'genres': result[2],
            'price': result[3],
            'rating': result[4]

        }
        return data, 200, {'statusText': 'Ok'}


@books.route('/topsellers')
class Topsellers(Resource):
    @books.doc(description='Get Top selling Books')
    @books.response(200, 'Success')
    @books.response(400, 'Failure', ErrorMsgModel)
    def get(self):
        result = getTopSellers()
        data = {
            'books': result,
        }
        return data, 200, {'statusText': 'Ok'}


cred = credentials.Certificate('utils/firebase_admin.json')
firebase = firebase_admin.initialize_app(cred)
pb = pyrebase.initialize_app(json.load(open('utils/firebase_config.json')))


getBookById_parser = reqparse.RequestParser()
getBookById_parser.add_argument('isbn')


@books.route('/getBookById')
class gettingBookById(Resource):
    @books.doc(description='get book by ISBN', parser=getBookById_parser)
    @books.response(200, 'Success')
    @books.response(400, 'Failure', ErrorMsgModel)
    def get(self):
        if not request.headers.get('Authorization'):
            user=None
        else:
            try:
                authorization = auth.verify_id_token(
                request.headers['Authorization'])
                user = authorization['uid']
            except:
                return {'message':'Invalid Token'},400
            

            #return {'message': 'No token provided.'}, 400
        #try:
            # authorization = auth.verify_id_token(
            #     request.headers['Authorization'])
            # user = authorization['uid']
        args = getBookById_parser.parse_args()
        result = getBookById(user, args['isbn'])
        if result['message'] == "Success":
            if user:
                result['recentlyViewedOperation'] = recentlyViewed(user, args)
            return result, 200, {'statusText': 'Ok'}
        else:
            return result, 400, {'statusText': 'Ok'}
        # except:
        #     return {'message': 'Invalid token.'}, 400


@books.route('/getbookbyuserid')
class UserBooks(Resource):
    @books.doc(description="Get Purchased Books")
    @books.response(400, 'Failure')
    @books.response(200, 'Success')
    @books.response(401, 'Auth Failure')
    def get(self):
        if not request.headers.get('Authorization'):
            return {'message': 'No token provided.'}, 400
        try:
            authorization = auth.verify_id_token(
                request.headers['Authorization'])
            user_id = authorization['uid']
            result = getBookByUserId(user_id)
            if result['message'] != 'Success':
                return result, 400
            return result, 200
        except Exception as e:
            print(e)
            return {'message': 'Invalid token.'}, 400


@books.route('/removefrompurchasedbook')
class RemoveFromPurchasedBook(Resource):
    @books.doc(description="remove From Purchased Book", parser=purchase_delete_parser)
    @books.response(400, 'Failure')
    @books.response(200, 'Success')
    @books.response(401, 'Auth Failure')
    def delete(self):
        if not request.headers.get('Authorization'):
            return {'message': 'No token provided.'}, 400
        try:
            authorization = auth.verify_id_token(
                request.headers['Authorization'])
            user_id = authorization['uid']
            args = purchase_delete_parser.parse_args()
            result = removeFromPurchasedBook(user_id, args['ISBN'])
            if result['message'] != 'Success':
                return result, 400
            else:
                return result, 200
        except Exception as e:
            print(e)
            return {'message': 'Invalid token.'}, 400


recentlyviewed_parser_get = reqparse.RequestParser()


@user.route('/get_recentlyviewed/')
@user.doc(parser=recentlyviewed_parser_get)
class Users(Resource):
    @user.doc(description='get recently viewed books')
    @user.response(200, 'Success')
    @user.response(400, 'Failure', ErrorMsgModel)
    def get(self):
        if not request.headers.get('Authorization'):
            return {'message': 'No token provided.'}, 400
        try:
            authorization = auth.verify_id_token(
                request.headers['Authorization'])
            #request.user = user
            # args=recentlyviewed_parser_get.parse_args()

            user = authorization['uid']
            result = getRecentlyViewed(user)
            if result and result != "Books Not Found":
                if result == "Books Not Found":
                    data = {
                        'books': "No books in recentlyviewed",
                    }
                    return data, 200, {'statusText': 'Ok'}
                else:
                    data = {
                        'books': result,
                    }
                    return data, 200, {'statusText': 'Ok'}
            else:
                return "Failed", 400, {'statusText': 'Failed'}

        except:
            return {'message': 'Invalid token.'}, 400


@books.route('/delete')
class DeleteBook(Resource):
    @books.doc(description="delete multiple book")
    @books.response(400, 'Failure')
    @books.response(200, 'Success')
    @books.response(401, 'Auth Failure')
    @books.expect(book_delete_model)
    def delete(self):
        if not request.headers.get('Authorization'):
            return {'message': 'No token provided.'}, 400
        try:
            authorization = auth.verify_id_token(
                request.headers['Authorization'])
            data = request.get_json()
            data = marshal(data, book_delete_model, skip_none=True)
            if not data or len(data['isbn']) == 0:
                return {'message': 'No data'}, 400

            conn = pg_connect()
            try:
                with conn.cursor() as c:
                    sql = """DELETE FROM Books WHERE isbn = %s"""
                    for isbn in data['isbn']:
                        c.execute(sql, (isbn,))
            except (Exception, psycopg2.Error) as error:
                print("Error while delete data", error)
                return abort(400, message="delete error")

            conn.commit()
            conn.close()
            return jsonify(message="Success")
        except:
            return {'message': 'Invalid token.'}, 400

# this function for admin to add the book info
# need login required later


@user.route('/addBook')
class AddBook(Resource):
    @user.doc(description="add new book")
    @user.response(400, 'Failure')
    @user.response(200, 'Success')
    @user.response(401, 'Auth Failure')
    @user.expect(book_model)
    def put(self):
        if not request.headers.get('Authorization'):
            return {'message': 'No token provided.'}, 400
        try:
            authorization = auth.verify_id_token(
                request.headers['Authorization'])
            data = request.get_json()

            data = marshal(data, book_model, skip_none=True)
            if not data:
                return abort(400, message="nothing to update")
            conn = pg_connect()
            try:
                with conn.cursor() as c:
                    sql = """ INSERT INTO Books(ISBN, title, author, publicationYear,
                                                numpages, rating, genre, 
                                                language, synopsis, price) VALUES 
                                                (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) """
                    c.execute(sql, list(data.values()))
            except (Exception, psycopg2.Error) as error:
                print("Error while insert data", error)
                return abort(400, message="insert error")

            conn.commit()
            conn.close()
            return jsonify(message="Success")
        except:
            return {'message': 'Invalid token.'}, 400


# for aws s3 bucket
bucketname = 'itp-bookmart'

addBook_parser = reqparse.RequestParser()
addBook_parser.add_argument('bookImage', type=werkzeug.datastructures.FileStorage, location='files', required=True)
addBook_parser.add_argument('book', type=werkzeug.datastructures.FileStorage, location='files', required=True)
@books.route('/uploadFile/<isbn>')
class UploadFile(Resource):
    @books.doc(description="upload files of a book", parser=addBook_parser)
    @books.response(400, 'Failure')
    @books.response(200, 'Success')
    @books.response(401, 'Auth Failure')
    def post(self, isbn):

        if not request.headers.get('Authorization'):

            return {'message': 'No token provided.'}, 400
        try:
            auth.verify_id_token(request.headers['Authorization'])
            args = addBook_parser.parse_args()

            bookImage = args['bookImage']
            bookImage.save(bookImage.filename)

            book = args['book']
            book.save(book.filename)

            config = configparser.ConfigParser()
            config.read('./utils/config.ini')
            key = 'key'
            s3 = boto3.client("s3",
                              aws_access_key_id=config[key]['ACCESS_KEY_ID'],
                              aws_secret_access_key=config[key]['SECRET_ACCESS_KEY'])
            try:
                conn = pg_connect()

                s3.upload_file(book.filename, bucketname,
                               'book/{}_{}'.format(isbn, book.filename),ExtraArgs={'ACL':'public-read'})
                
                bookUrl = "https://itp-bookmart.s3.ap-southeast-2.amazonaws.com/book/{}_{}".format(isbn,book.filename)
                print('bookUrl',bookUrl)

                conn.cursor().execute(("UPDATE Books SET bookUrl='{bookUrl}' WHERE isbn='{isbn}';").format(
                    bookUrl=bookUrl, isbn=isbn))

                s3.upload_file(bookImage.filename, bucketname,
                               "bookImage/{}_{}".format(isbn, bookImage.filename),ExtraArgs={'ACL':'public-read'})

                imageUrl = "https://itp-bookmart.s3.ap-southeast-2.amazonaws.com/bookImage/{}_{}".format(isbn,
                    bookImage.filename)
                conn.cursor().execute(("UPDATE Books SET bookimage='{bookimage}' WHERE isbn='{isbn}';").format(
                    bookimage=imageUrl, isbn=isbn))
                conn.commit()
                conn.close()
            except:
                return {'message': 'aws error'}, 400
            return jsonify(message="Success")
        except:
            return {'message': 'Invalid token.'}, 400


@books.route('/<string:isbn>')
@books.doc(params={'isbn': 'isbn'})
class BookDetail(Resource):
    @books.doc(description="delete book")
    @books.response(400, 'Failure')
    @books.response(200, 'Success')
    @books.response(401, 'Auth Failure')
    def delete(self, isbn):
        conn = pg_connect()
        try:
            with conn.cursor() as c:
                sql = """DELETE FROM Books WHERE isbn = %s"""
                c.execute(sql, (isbn,))
        except (Exception, psycopg2.Error) as error:
            print("Error while delete data", error)
            return abort(400, message="delete error")

        conn.commit()
        conn.close()
        return jsonify(message="Success")

    @books.doc(description="update book detail")
    @books.response(400, 'Failure')
    @books.response(200, 'Success')
    @books.response(401, 'Auth Failure')
    @books.expect(book_update_model)
    def post(self, isbn):
        if not request.headers.get('Authorization'):
            return {'message': 'No token provided.'}, 400
        try:
            authorization = auth.verify_id_token(
                request.headers['Authorization'])
            data = request.get_json()
            data = marshal(data, book_update_model, skip_none=True)
            if not data:
                return abort(400, message="nothing to update")
            conn = pg_connect()
            if data['title']:
                conn.cursor().execute(("UPDATE Books SET title='{title}' WHERE isbn='{isbn}';").format(
                    title=data['title'], isbn=isbn))
            if data['author']:
                conn.cursor().execute(("UPDATE Books SET author='{author}' WHERE isbn='{isbn}';").format(
                    author=data['author'], isbn=isbn))
            if data['publicationYear']:
                conn.cursor().execute(("UPDATE Books SET publicationyear='{publicationyear}' WHERE isbn='{isbn}';").format(
                    publicationyear=data['publicationYear'], isbn=isbn))
            # if data['bookImage']:
            #     conn.cursor().execute(("UPDATE Books SET bookimage='{bookimage}' WHERE isbn='{isbn}';").format(bookimage=data['bookImage'], isbn=isbn))
            if data['rating']:
                conn.cursor().execute(("UPDATE Books SET rating='{rating}' WHERE isbn='{isbn}';").format(
                    rating=data['rating'], isbn=isbn))
            if data['genre']:
                conn.cursor().execute(("UPDATE Books SET genre='{genre}' WHERE isbn='{isbn}';").format(
                    genre=data['genre'], isbn=isbn))
            if data['language']:
                conn.cursor().execute(("UPDATE Books SET language='{language}' WHERE isbn='{isbn}';").format(
                    language=data['language'], isbn=isbn))
            if data['synopsis']:
                sql = """ UPDATE Books
                    SET synopsis = %s
                    WHERE isbn = %s"""
                conn.cursor().execute(sql, (data['synopsis'], isbn))
            if data['price']:
                conn.cursor().execute(("UPDATE Books SET price='{price}' WHERE isbn='{isbn}';").format(
                    price=data['price'], isbn=isbn))
            # if data['bookURL']:
            #     conn.cursor().execute(("UPDATE Books SET bookUrl='{bookUrl}' WHERE isbn='{isbn}';").format(bookUrl=data['bookURL'], isbn=isbn))
            if data['numpages']:
                conn.cursor().execute(("UPDATE Books SET numpages='{numberOfPages}' WHERE isbn='{isbn}';").format(
                    numberOfPages=data['numpages'], isbn=isbn))
            conn.commit()
            conn.close()
            return jsonify(message="Success")
        except:
            return {'message': 'Invalid token.'}, 400


@rev.route('/<string:isbn>')
class Reviews(Resource):
    @rev.doc(description="Write a review")
    @rev.response(400, 'Failure')
    @rev.response(200, 'Success')
    @rev.response(401, 'Auth Failure')
    @rev.expect(review_rating_model)
    def post(self, isbn):
        if not request.headers.get('Authorization'):
            return {'message': 'No token provided.'}, 400
        try:
            authorization = auth.verify_id_token(
                request.headers['Authorization'])
            user_id = authorization['uid']
            user_name = authorization['name']
            data = request.get_json()
            data = marshal(data, review_rating_model)
            data['user_id'] = user_id
            data['user_name'] = user_name
            result = writeReview(data, isbn)
            return result
        except:
            return {'message': 'Invalid token.'}, 400

    @rev.doc(params={'isbn': 'isbn'}, parser=reviews_query_parser)
    def get(self, isbn):
        if not request.headers.get('Authorization'):
            user_id = None
        if request.headers.get('Authorization'):
            authorization = auth.verify_id_token(
                request.headers['Authorization'])
            user_id = authorization['uid']
        args = reviews_query_parser.parse_args()
        result = fetch_reviews(args, isbn, user_id)
        return result


@cart.route('/addtocart')
class AddToCart(Resource):
    @cart.doc(description="Add to Cart")
    @cart.response(400, 'Failure')
    @cart.response(200, 'Success')
    @cart.response(401, 'Auth Failure')
    @cart.expect(cart_model)
    def post(self):
        if not request.headers.get('Authorization'):
            return {'message': 'No token provided.'}, 400
        try:
            authorization = auth.verify_id_token(
                request.headers['Authorization'])
            user_id = authorization['uid']
            data = request.get_json()
            data = marshal(data, cart_model)
            data['user_id'] = user_id
            result = addToCart(data)
            if result['message'] == 'Failed':
                return {'message': 'Book Already in Cart'}, 400

            return result, 200
        except Exception as e:
            print(e)
            return {'message': 'Invalid token.'}, 400


@cart.route('/removefromcart')
class RemoveFromCart(Resource):
    @cart.doc(description="remove from Cart", parser=cart_delete_parser)
    @cart.response(400, 'Failure')
    @cart.response(200, 'Success')
    @cart.response(401, 'Auth Failure')
    @cart.expect(book_delete_model)

    def delete(self):
        if not request.headers.get('Authorization'):
            return {'message': 'No token provided.'}, 400
        try:
            authorization = auth.verify_id_token(
                request.headers['Authorization'])
            user_id = authorization['uid']
            data = request.get_json()
            data = marshal(data, book_delete_model, skip_none=True)
            
            if not data or len(data['isbn']) == 0:
                 return {"success":False, "message": "ISBN  not Provided"}, 400
            result = removeFromCart(user_id, data['isbn'][0])
            if result['message'] == 'Book Not Found':
                return result, 400

            return result, 200
        except Exception as e:
            print(e)
            return {'message': 'Invalid token.'}, 400


@cart.route('/getcart')
class GetCart(Resource):
    @cart.doc(description="Get Books in Cart")
    @cart.response(400, 'Failure')
    @cart.response(200, 'Success')
    @cart.response(401, 'Auth Failure')
    def get(self):
        if not request.headers.get('Authorization'):
            return {'message': 'No token provided.'}, 400
        try:
            authorization = auth.verify_id_token(
                request.headers['Authorization'])
            user_id = authorization['uid']
            result = getCartList(user_id)
            if result['success'] != True:
                return result, 400
            return result, 200
        except Exception as e:
            print(e)
            return {'message': 'Invalid token.'}, 400


@sale.route('/purchase')
class Purchase(Resource):
    @sale.doc(description="Purchase Books")
    @sale.response(400, 'Failure')
    @sale.response(200, 'Success')
    @sale.response(401, 'Auth Failure')
    @sale.expect(buy_books_model)
    def post(self):
        if not request.headers.get('Authorization'):
            return {'message': 'No token provided.'}, 400
        try:
            authorization = auth.verify_id_token(
                request.headers['Authorization'])
            user_id = authorization['uid']
            data = request.get_json()
            data = marshal(data, buy_books_model)
            data['user_id'] = user_id
            result = buyBook(data)
            if result['message'] != 'Purchased Book':
                return result, 400
            else:
                return result, 200
        except Exception as e:
            print(e)
            return {'message': 'Invalid token.'}, 400


@books.route('/bookurl/<string:isbn>')
class bookUrl(Resource):
    @books.doc(description="Get the url of eBook")
    @books.response(400, 'Failure')
    @books.response(200, 'Success')
    @books.response(401, 'Auth Failure')
    def get(self,isbn):
        if not request.headers.get('Authorization'):
            return {'message': 'No token provided.'}, 400
        try:
            authorization = auth.verify_id_token(request.headers['Authorization'])
            user_id = authorization['uid']
            print(user_id)
            result= getBookUrl(user_id,isbn)
            return result

        except:
            return {'success':False,
                    'message':'Authorization failure'},401

@admin.route('/transactionsummary')
class TransactionSummary(Resource):
    @admin.doc(description="Get Transaction Summary Number of Order and Revnue generated")
    @admin.response(400, 'Failure')
    @admin.response(200, 'Success')
    @admin.response(401, 'Auth Failure')
    def get(self):
        if not request.headers.get('Authorization'):
            return {'message': 'No token provided.'}, 400
        try:
            authorization = auth.verify_id_token(request.headers['Authorization'])
            result = getTransactionSummary()
            return result
        except:
            return {'success':False,
                    'message':'Authorization failure'},401

@admin.route('/genresummary')
class GenreSummary(Resource):
    @admin.doc(description="Get Summary by Genres")
    @admin.response(400, 'Failure')
    @admin.response(200, 'Success')
    @admin.response(401, 'Auth Failure')
    def get(self):
        if not request.headers.get('Authorization'):
            return {'message': 'No token provided.'}, 400
        try:
            authorization = auth.verify_id_token(request.headers['Authorization'])
            result = getGenreSummary()
            return result
        except:
            return {'success':False,
                    'message':'Authorization failure'},401

@admin.route('/gettitlesummary')
class TitleSummay(Resource):
    @admin.doc(description="Get Summary by Book Title")
    @admin.response(400, 'Failure')
    @admin.response(200, 'Success')
    @admin.response(401, 'Auth Failure')
    def get(self):
        if not request.headers.get('Authorization'):
            return {'message': 'No token provided.'}, 400
        try:
            authorization = auth.verify_id_token(request.headers['Authorization'])
            result = getTitleSummay()
            return result
        except:
            return {'success':False,
                    'message':'Authorization failure'},401


@admin.route('/getallpurchase')
class AllPurchase(Resource):
    @admin.doc(description="Get All Purchased Book")
    @admin.response(400, 'Failure')
    @admin.response(200, 'Success')
    @admin.response(401, 'Auth Failure')
    def get(self):
        if not request.headers.get('Authorization'):
            return {'message': 'No token provided.'}, 400
        try:
            authorization = auth.verify_id_token(request.headers['Authorization'])
            result = getAllPurchase()
            return result
        except:
            return {'success':False,
                    'message':'Authorization failure'},401


@rec.route('')
class personalizedRecommendations(Resource):
    @rec.doc(description="Get Personalized Recommendations")
    @rec.response(400, 'Failure')
    @rec.response(200, 'Success')
    @rec.response(401, 'Auth Failure')
    def get(self):
        if not request.headers.get('Authorization'):
            user_id=None
            return {'message':'No token provided.'},400
        try:
            authorization=auth.verify_id_token(request.headers['Authorization'])
            user_id = authorization['uid']
            result=getPersonalizedRecommendations(user_id)
            data = {'books': result}
            return data, 200, {'statusText': 'Ok'}
        except:
            return {'message': 'Invalid token.'}, 400
@admin.route('/getuserregistrations')
class AllTimeStamp(Resource):
    @admin.doc(description="Get All user registration timestamps")
    @admin.response(400, 'Failure')
    @admin.response(200, 'Success')
    @admin.response(401, 'Auth Failure')
    def get(self):
        # if not request.headers.get('Authorization'):
        #     return {'message': 'No token provided.'}, 400
        # try:
        #     authorization = auth.verify_id_token(request.headers['Authorization'])
        # doc_ref = db.collection(u'Users').stream()

        # docs = db.collection(u'Users').get()
        # my_dict = {el.id: el.to_dict() for el in docs}
        # # docs = doc_ref.get()
        # print(my_dict)
        if not request.headers.get('Authorization'):
            return {'message': 'No token provided.'}, 400
        try:
            authorization = auth.verify_id_token(request.headers['Authorization'])
            result = getAllUserRegistrations()
            return result
        except:
            return {'success':False,
                    'message':'Authorization failure'},401
        
