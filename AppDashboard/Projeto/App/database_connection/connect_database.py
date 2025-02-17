import pandas as pd
import databricks,os
from databricks import sql
 
class Database:
    def __init__(self):
        self.conn = sql.connect(
            server_hostname =  os.getenv("HOST_NAME"),
            http_path = os.getenv("SQL_HTTP_PATH") ,
            access_token = os.getenv("ACESS_TOKEN")
        )
    
    def insert_dataframe(self, df, table_name):
        connection = self.conn 
        print(df, table_name)
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


def main():
    database = Database()

    query = """select * from desafio_kinea.boletagem_cp.book_ativos"""

    df = database.select_to_dataframe(query)

    print(df)
    



if __name__ == '__main__':
    main()