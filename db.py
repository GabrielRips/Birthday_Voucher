import mysql.connector
import os
from config import MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE, MYSQL_SSL_CA, MYSQL_PORT

def get_db_connection():
    # Debug prints:
    print("MYSQL_HOST:", repr(MYSQL_HOST), type(MYSQL_HOST))
    print("MYSQL_USER:", repr(MYSQL_USER), type(MYSQL_USER))
    print("MYSQL_PASSWORD:", repr(MYSQL_PASSWORD), type(MYSQL_PASSWORD))
    print("MYSQL_DATABASE:", repr(MYSQL_DATABASE), type(MYSQL_DATABASE))
    print("MYSQL_SSL_CA:", repr(MYSQL_SSL_CA), type(MYSQL_SSL_CA))
    print("MYSQL_PORT:", repr(MYSQL_PORT), type(MYSQL_PORT))
    
    connection_params = {
        "host": MYSQL_HOST,
        "user": MYSQL_USER,
        "password": MYSQL_PASSWORD,
        "database": MYSQL_DATABASE,
        "ssl_ca": MYSQL_SSL_CA
    }
    if MYSQL_PORT:
        # Ensure port is an integer
        connection_params["port"] = int(MYSQL_PORT)
    
    return mysql.connector.connect(**connection_params)