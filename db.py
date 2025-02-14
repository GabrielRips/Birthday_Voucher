import mysql.connector
import os
from config import MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE, MYSQL_SSL_CA, MYSQL_PORT

def get_db_connection():    
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