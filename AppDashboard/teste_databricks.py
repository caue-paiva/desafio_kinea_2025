import pandas as pd
from databricks import sql
import databricks
 
class Database:
    def __init__(self):
        self.conn = sql.connect(
            server_hostname = 'adb-2481770933719198.18.azuredatabricks.net',
            http_path = '/sql/1.0/warehouses/b8393f0553c09bb7',
            access_token = 'seu-token'
        )
 
    def insert_dataframe(self, df, table_name):
        connection = self.conn 
        df.to_sql(table_name, con=connection, if_exists='append', index=False)
        connection.close()
 
 
    def select_to_dataframe(self, query):
        with self.conn.cursor() as cursor:
 
            cursor.execute(query)
            colunas = [column[0] for column in cursor.description]
            dados = cursor.fetchall()
        return pd.DataFrame(dados, columns = colunas)
 
    def executa_query(self, query):
        with self.conn.cursor() as cursor:
            cursor.execute(query)