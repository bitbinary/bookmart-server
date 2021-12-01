from typing import DefaultDict

from flask_restx import reqparse, fields, inputs
from app import api

ErrorMsgModel = api.model('Error', {
    'msg': fields.String(example="Invaild request")
})

book_model = api.model('Book',{
'ISBN':fields.String(required=True),
'title':fields.String(required=True),
'author':fields.String(required=True),
'publicationYear':fields.String(required=True),
# 'bookImage':fields.String(required=True),
'numpages':fields.Integer(required=True),
'rating':fields.Float(required=True),
'genre':fields.String(required=True),
# 'bookURL':fields.String(required=True),
'language':fields.String(required=True),
'synopsis':fields.List(fields.String, required=True),
'price':fields.Float(required=True)
})

book_update_model = api.model('BookUpdate',{
'title':fields.String(),
'author':fields.String(),
'publicationYear':fields.String(),
# 'bookImage':fields.String(),
'numpages':fields.Integer(),
'rating':fields.Float(),
'genre':fields.String(),
# 'bookURL':fields.String(),
'language':fields.String(),
'synopsis':fields.List(fields.String),
'price':fields.Float()
})

book_delete_model = api.model('BookDelete', {
    'isbn': fields.List(fields.String, required=True)
})

# EditBookModel = api.model('Edit', {
# 'title':fields.String,
# 'author':fields.List(fields.String),
# 'publicationyear':fields.String,
# 'bookimage':fields.Url,
# 'numberOfPages':fields.Integer,
# 'rating':fields.Float,
# 'genre':fields.String,
# 'bookUrl':fields.Url,
# 'language':fields.String,
# 'synopsis':fields.List(fields.String),
# 'price':fields.Float
# })

#Reviews & Ratings
# review_inputs_parser = reqparse.RequestParser()
# #review_inputs_parser.add_argument('ISBN')
# review_inputs_parser.add_argument('review_text')
# review_inputs_parser.add_argument('rating',type=float,default=5.0)
# review_inputs_parser.add_argument('is_spoiler',type=inputs.boolean,default=False)
# review_inputs_parser.add_argument('emotings',action='append')


review_rating_model=api.model('WriteReview',{
    'rating':fields.Float(),
    'review_text':fields.String(),
    'is_spoiler':fields.Boolean(),
    'emotings':fields.List(fields.String)
})

reviews_query_parser=reqparse.RequestParser()
reviews_query_parser.add_argument('sentiment')
reviews_query_parser.add_argument('pageNumber',type=int,default=1)
reviews_query_parser.add_argument('reviewsPerPage',type=int,default=5)

cart_model=api.model('AddToCart',{
    'ISBN':fields.String(required=True),
})

cart_delete_parser = reqparse.RequestParser()
cart_delete_parser.add_argument('ISBN')

buy_books_model=api.model('AddToCart',{
    'isbnList':fields.List(fields.String, required=True),
})

purchase_delete_parser = reqparse.RequestParser()
purchase_delete_parser.add_argument('ISBN')