from app import app
import pandas as pd
from utils.db import pg_queryToDataFrame
import json

def searchSortFilter(args):
    ascending = args['ascending']
    search_with = args['search']
    orderBy = args['orderBy']
    resultsPerPage = args['resultsPerPage']
    page = args['pageNumber']
    numberOfPages = args['numberOfPages']
    genre_filter=args.get('genres')
    price=args.get('price')
    rating=args.get('rating')
    
    
    df1 = pg_queryToDataFrame("SELECT * FROM books;")

    if search_with:
        df1=df1.query('title.str.contains(@search_with,case=False) or author.str.contains(@search_with,case=False)')

    if genre_filter:
        df1=df1.query('genre in @genre_filter')

    if price:
        df1=df1.query('price>=@price[0] and price<=@price[1]')

    if rating:
        df1=df1.query('rating>=@rating[0] and rating<=@rating[1]')


    
    totalRows = df1.shape[0]
    
    if orderBy:
        df1.sort_values(by=orderBy,inplace=True,ascending=ascending)
    
    genres=list(df1.genre.unique())

    price=[df1.price.min(),df1.price.max()]

    rating=[df1.rating.min(),df1.rating.max()]


    totalRowsToPass = resultsPerPage*numberOfPages
    print(totalRowsToPass)
    print(page)
    df1 = df1[totalRowsToPass*(page-1):totalRowsToPass*(page)]
    
    json_str=df1.to_json(orient='records')
    data=json.loads(json_str)
    
    return [data,totalRows,genres,price,rating]
