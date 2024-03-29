import os
import logging
import textwrap
import pyodbc
import pandas as pd
from urllib.parse import quote_plus
import sqlalchemy

SECRET_VARIABLES = ["SERVER_NAME", "DATABASE_NAME", "DB_LOGIN", "DB_PASSWORD"]
DRIVER = "{ODBC Driver 17 for SQL Server}"


def fetch_azure_connection_string():
    secrets = {}
    for secret in SECRET_VARIABLES:
        secrets[secret] = os.getenv(secret, False)
        if not secrets[secret]:
            raise NameError(f"{secret} is not set as an environment variable!")
    logging.info("Loaded all secrets into memory")
    server = f"{secrets['SERVER_NAME']}.database.windows.net,1433"

    con_str = textwrap.dedent(
        f"""
        Driver={DRIVER};
        Server={server};
        Database={secrets["DATABASE_NAME"]};
        Uid={secrets["DB_LOGIN"]};
        Pwd={secrets["DB_PASSWORD"]};
        Encrypt=yes;
        TrustServerCertificate=no;
        Connection Timeout=30;
    """
    )
    return con_str


class DB_Connection:
    def __init__(self):
        connection_string = self.secrets = fetch_azure_connection_string()
        self.cnxn: pyodbc.Connection = pyodbc.connect(connection_string)
        self.crsr: pyodbc.Cursor = self.cnxn.cursor()
        logging.info("Established connection with the DB")

    def get_data(self, sql_file):
        with open(sql_file) as f:
            sql_code = f.read()
        return pd.read_sql(sql_code, self.cnxn)

    def run_query(self, sql_str=None, sql_file=None):
        if (sql_str is None) & (sql_file is None):
            raise Exception("A query or file need to be provided to run this method")
        elif sql_file is not None:
            with open(sql_file, "r") as sql:
                sql_str = sql.read()
        self.crsr.execute(sql_str)
        self.cnxn.commit()
        logging.info("Executed query successfully")
        return True

    def load_data(self, df, table, schema):
        con_str = quote_plus(self.secrets)
        con_str = "mssql+pyodbc:///?odbc_connect={}".format(con_str)
        sql_engine = sqlalchemy.create_engine(con_str)
        con = sql_engine.connect()
        df.to_sql(con=con, name=table, if_exists="append", index=False, schema=schema, method="multi", chunksize=100)
        logging.info("Loaded data into SQL Server successfully")
        return True

    def close(self):
        self.cnxn.close()
        logging.info("Closed conection successfully")
        return True
