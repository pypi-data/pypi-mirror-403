from .imports import *
from .tableManager import *
def get_safe_password(password):
    safe_password = quote_plus(password)
    return safe_password
# Existing utility functions remain the same
def get_dbType(dbType=None):
    return dbType or 'database'

def get_dbName(dbName=None):
    return dbName or 'abstract'

def get_dbUser(dbUser=None):
    return dbUser

def verify_env_path(env_path=None):
    return env_path or get_env_path()
def get_db_vars_from_kwargs(**kwargs):
    """
    Normalize DB-related kwargs into canonical connection variables.

    Accepted aliases (case-insensitive):
        port        -> port
        password    -> password, pass
        dbType      -> type, dbtype
        host        -> host, url, address
        dbUser      -> user, dbuser
        dbName      -> dbname, database, name
    """
    resolved = {}

    key_aliases = {
        "port": ["port"],
        "password": ["password", "pass"],
        "dbType": ["type", "dbtype"],
        "host": ["host", "url", "address"],
        "user": ["user", "dbuser"],
        "dbname": ["dbname", "database", "name"],
        "env_path":["path","env_path"]
    }

    # Normalize incoming kwargs once
    lowered_kwargs = {k.lower(): v for k, v in kwargs.items()}

    for canonical_key, aliases in key_aliases.items():
        for alias in aliases:
            if alias in lowered_kwargs:
                resolved[canonical_key] = lowered_kwargs[alias]
                break  # stop searching aliases, not keys

    return resolved
def get_kwargs_dict(**kwargs):
    return kwargs
def get_db_env_value(dbname,user,env_path=None,**kwargs):
    env_path = verify_env_path(env_path)
    dbname_part_key=""
    user_part_key=""
    if dbname:
        dbname_part_key=f"{dbname}_"
    if user:
        user_part_key=f"{dbname_part_key}{user}_"
    for key,value in kwargs.items():
        value = get_env_value(value) or value
        if not value:
            for part_key in [dbname_part_key,user_part_key]:
                temp_key = f"{part_key}{key}"
                value = get_env_value(temp_key.upper(),path=env_path)
                if value:
                    break
        kwargs[key]=value
    return get_kwargs_dict(dbname=dbname,user=user,**kwargs)
def get_db_env_key(dbname=None,user=None,port=None,password=None,host=None,env_path=None,dbType=None):
    return get_db_env_value(dbname=dbname,user=user,port=port,password=password,host=host,env_path=env_path)
def derive_db_vars(**kwargs):
    db_vars = get_db_vars_from_kwargs(**kwargs)
    return get_db_env_key(**db_vars)
def get_db_vars(**kwargs):
    dbVars = derive_db_vars(**kwargs)
    protocol = 'postgresql'
    if 'rabbit' in str(dbVars.get('dbname',"")).lower():
        protocol = 'amqp'
    dbVars['dburl'] = f"{protocol}://{dbVars['user']}:{dbVars['password']}@{dbVars['host']}:{dbVars['port']}/{dbVars['dbname']}"
    return dbVars
class connectionManager(metaclass=SingletonMeta):
        
    def __init__(self, tables=[], tables_path=None,**kwargs):
        if not hasattr(self, 'initialized'):
            self.initialized=True
            dbVars = derive_db_vars(**kwargs)
            self.env_path = dbVars.get('env_path')
            self.dbName = dbVars.get('dbname')
            self.dbType = dbVars.get('dbtype')
            self.dbUser = dbVars.get('user')
            self.dbVars = self.get_db_vars(**dbVars)
            self.user = self.dbUser = self.dbVars['user']
            self.password = self.dbVars['password']
            self.host = self.dbVars['host']
            self.port = self.dbVars['port']
            self.dbname = self.dbVars['dbname']
            self.dburl = self.dbVars['dburl']  # URL-based connection string
            self.table_mgr = TableManager()
            self.tables = tables or safe_load_from_json(file_path=tables_path) or []
            self.table_mgr.env_path = self.env_path
            self.add_insert_list=None
            
            self.check_conn()
        
    def check_conn(self):
        if self.add_insert_list == None:
##          try:
                self.table_mgr.add_insert_list(self.connect_db(), self.tables, self.dbName)
                self.table_mgr.add_insert_list(self.connect_db(), self.tables, self.dbName)
                self.add_insert_list=True
##          except:
##            pass
        return self.add_insert_list
    def get_dbName(self, dbName=None):
        return get_dbName(dbName=dbName or self.dbName)
    def get_dbType(self, dbType=None):
        return get_dbType(dbType=dbType or self.dbType)
    def get_dbUser(self, dbUser=None):
        return get_dbUser(dbUser=dbUser or self.dbUser)
    def get_env_path(self, env_path=None):
        return verify_env_path(env_path=env_path)

    def get_db_vars(self,**kwargs):
        return get_db_vars(**kwargs)

    def change_db_vars(self, tables=[], tables_path=None,**kwargs):
        dbVars = derive_db_vars(**kwargs)
        self.env_path = dbVars.get('env_path')
        self.dbName = dbVars.get('dbname')
        self.dbType = dbVars.get('dbtype')
        self.dbUser = dbVars.get('user')
        self.dbVars = self.get_db_vars(**dbVars)
        self.user = self.dbUser = self.dbVars['user']
        self.password = self.dbVars['password']
        self.host = self.dbVars['host']
        self.port = self.dbVars['port']
        self.dbname = self.dbVars['dbname']
        self.dburl = self.dbVars['dburl']  # URL-based connection string
        self.simple_connect = self.simple_connect_db()
        self.get_db_connection(self.connect_db())
        self.tables = tables or self.tables
        self.table_mgr.add_insert_list(self.connect_db(), self.tables, self.dbName)
        return self.dbVars

    def connect_db(self):
            
            """ Establish a connection to the database, either by connection parameters or via URL """
            if self.dburl:
                
                return psycopg2.connect(self.dburl)
            else:
                return psycopg2.connect(user=self.user,
                                        password=self.password,
                                        host=self.host,
                                        port=self.port,
                                        dbname=self.dbname)

    def simple_connect_db(self):
        """ Create a connection pool using the database URL """
        if self.dburl:
            return psycopg2.pool.SimpleConnectionPool(1, 10, self.dburl)
        else:
            return psycopg2.pool.SimpleConnectionPool(1, 10, user=self.user,
                                                      password=self.password,
                                                      host=self.host,
                                                      port=self.port,
                                                      database=self.dbname)

    def put_db_connection(self, conn):
        conn = conn or self.connect_db()
        self.putconn(conn)

    def get_db_connection(self):
        return self.connect_db()

    def get_insert(self, tableName):
        return self.table_mgr.get_insert(tableName)

    def fetchFromDb(self, tableName, searchValue):
        return self.table_mgr.fetchFromDb(tableName, searchValue, self.connect_db())

    def insertIntoDb(self, tableName, searchValue, insertValue):
        return self.table_mgr.insert_intoDb(tableName, searchValue, insertValue, self.connect_db())

    def search_multiple_fields(self, query, **kwargs):
        return self.table_mgr.search_multiple_fields(query=query, conn=self.connect_db())

    def get_first_row_as_dict(self, tableName=None, rowNum=1):
        return self.table_mgr.get_first_row_as_dict(tableName=tableName, rowNum=rowNum, conn=self.connect_db())
def create_connection(**kwargs):
    return connectionManager(**kwargs)

def get_db_connection(**kwargs):

    return connectionManager(**kwargs).get_db_connection()

def put_db_connection(conn):
    connectionManager().put_db_connection(conn)

def connect_db(**kwargs):
    return connectionManager(**kwargs).connect_db()

def get_insert(tableName,**kwargs):
    return connectionManager(**kwargs).get_insert(tableName)

def fetchFromDb(tableName, searchValue,**kwargs):
    return connectionManager(**kwargs).fetchFromDb(tableName, searchValue)

def insertIntoDb(tableName, searchValue, insertValue,**kwargs):
    return connectionManager(**kwargs).insertIntoDb(tableName, searchValue, insertValue)

def search_multiple_fields(query, **kwargs):
    return connectionManager().search_multiple_fields(query, **kwargs)

def get_first_row_as_dict(tableName=None, rowNum=1):
    return connectionManager().get_first_row_as_dict(tableName, rowNum)
def get_cur_conn(use_dict_cursor=True):
    """
    Get a database connection and a RealDictCursor.
    Returns:
        tuple: (cursor, connection)
    """
    conn = connectionManager().get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor) if use_dict_cursor else conn.cursor()
    return cur, conn
