import psycopg2
import psycopg2.extras
import pandas as pd
import configparser
from firebase_admin import firestore

def firestore_db():
    db = firestore.client()
    return db

def pg_connect():
    config = configparser.ConfigParser()

    config.read('./utils/config.ini')
    server = 'aws'
    conn = psycopg2.connect(
        user = config[server]['user'],
        password = config[server]['password'],
        host = config[server]['host'],
        port = config[server]['port'],
        database = config[server]['db']
        )
    return conn


def pg_queryToDataFrame(sql):
    conn = pg_connect()
    records = None
    
    try:
        with conn.cursor() as c:
            records = pd.read_sql(sql=sql, con=conn)
            
    except (Exception, psycopg2.Error) as error:
        print("Error while fetching data FROM PostgreSQL", error)
    
    finally:
        # closing database connection.
        if conn:
            c.close()
            conn.close()
            print("PostgreSQL connection is closed")
    return records

def rowToDict(row):
    return dict(zip(row.keys(), row))

class Stub():	
    def __init__(self, conn, cursor, type, q):	
        self.conn = conn
        self.cursor = cursor
        self.type = type
        self.q = q
        self.q_values = tuple()

    def values(self, **kargs):	
        keys = kargs.keys()	
        values = [kargs[k] for k in keys]	
        ph = ",".join(["?" for k in keys])	
        self.q += "({}) VALUES ({})".format(','.join(keys), ph)	
        self.q_values += tuple(values)	
        return self	

    def where(self, **kargs):	
        search_param = ["{} = ?".format(x) for x in kargs.keys()]	
        if (len(search_param) > 0):	
            self.q += " WHERE {}".format(" AND ".join(search_param))	
        self.q_values += tuple(kargs.values())	
        return self	

    def orwhere(self, **kargs):	
        search_param = ["{} = ?".format(x) for x in kargs.keys()]	
        if (len(search_param) > 0):	
            self.q += " WHERE {}".format(" OR ".join(search_param))	
        self.q_values += tuple(kargs.values())	
        return self	

    def set(self, **kargs):	
        set_param = ",".join(["{} = ?".format(x) for x in kargs])	
        self.q += " SET {}".format(set_param)	
        self.q_values += tuple(kargs.values())	
        return self	

    def execute(self):	
        c = self.cursor
        c.execute(self.q, self.q_values)
        
        if self.type == 'UPDATE' or self.type == 'DELETE':
            return c.rowcount
        elif self.type == 'INSERT':
            return c.lastrowid
        elif self.type == 'SELECT':
            rows = c.fetchall()
            if len(rows) == 0:
                return None
            return [rowToDict(row) for row in rows]
        elif self.type == 'SELECT_ONE':
            row = c.fetchone()
            if not row:
                return None
            return rowToDict(row)
        else:
            raise Exception("Unknown type for query {}".format(self.type))


class DB:	
    def __init__(self):	
        self.conn = pg_connect()
        self.cursor = self.conn.cursor(cursor_factory = psycopg2.extras.DictCursor)

    def raw(self, q, params=[]):	
        self.cursor().execute(q, tuple(params))	
        r = self.cursor().fetchall()	
        self.conn.commit()	
        self.conn.close()	
        return r	

    def insert(self, table):	
        s = Stub(self.conn,self.cursor, 'INSERT', 'INSERT INTO {}'.format(table))	
        return s	

    def select(self, table):	
        s = Stub(self.conn,self.cursor, 'SELECT', 'SELECT {} FROM {}'.format("*", table))	
        return s	

    def select_one(self, table):	
        s = Stub(self.conn,self.cursor, 'SELECT_ONE', 'SELECT {} FROM {}'.format("*", table))
        return s	
    def update(self, table):	
        s = Stub(self.conn,self.cursor, 'UPDATE', 'UPDATE {}'.format(table))	
        return s	

    def delete(self, table):	
        s = Stub(self.conn,self.cursor, 'DELETE', 'DELETE FROM {}'.format(table))	
        return s	

    def commit(self):	
        self.conn.commit()	
        self.conn.close()

