# Databricks notebook source
# MAGIC %sql
# MAGIC SELECT * FROM desafio_kinea.boletagem_cp.cotas
# MAGIC SORT BY Data DESC

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC SELECT t1.Codigo,t1.Data,t1.PL
# MAGIC FROM desafio_kinea.boletagem_cp.cotas as t1
# MAGIC JOIN (
# MAGIC     SELECT Codigo, MAX(Data) AS MaxData
# MAGIC     FROM desafio_kinea.boletagem_cp.cotas
# MAGIC     GROUP BY Codigo
# MAGIC ) t2 
# MAGIC ON t1.Codigo = t2.Codigo AND t1.Data = t2.MaxData
# MAGIC ORDER BY Data DESC;
# MAGIC
# MAGIC
# MAGIC

# COMMAND ----------


from pyspark.sql import DataFrame
from typing import Callable
"""
pegar património liquido de um fundo
"""


def df_pl_atualizado()->DataFrame:
        """
        Retorna um Dataframe com as colunas Código (do fundo), Data e PL do fundo mais atualizado.
        """
        return spark.sql("""
            SELECT t1.Codigo,t1.Data,t1.PL
            FROM desafio_kinea.boletagem_cp.cotas as t1
            JOIN (
                SELECT Codigo, MAX(Data) AS MaxData
                FROM desafio_kinea.boletagem_cp.cotas
                GROUP BY Codigo
            ) t2 
            ON t1.Codigo = t2.Codigo AND t1.Data = t2.MaxData
            ORDER BY Data DESC;
        """)

def get_pl_fundo(codigo_fundo:str,dataframe_pl:DataFrame)->float:
    return float(
        dataframe_pl.filter(dataframe_pl["Codigo"] == codigo_fundo).first()["PL"]
    )
    



df = df_pl_atualizado()
df.show()

get_pl_fundo("KP3", df)


# COMMAND ----------

from dataclasses import dataclass
"""
Modelar uma ordem de ativo como uma dataclass
"""

@dataclass
class OrdemAtivo:
    """
    Representa uma ordem de alocação de ativos para um fundo
    """
    nome_ativo:str
    amount:int
    venda:bool
    preco:float
    fundo:str

#dataset sintético para teste
ordens_ativos = [ 
    OrdemAtivo(nome_ativo="AAPL", amount=50, venda=False, preco=145.0, fundo="Fundo A"),
    OrdemAtivo(nome_ativo="TSLA", amount=20, venda=True, preco=120.5, fundo="Fundo B"),
    OrdemAtivo(nome_ativo="GOOGL", amount=15, venda=False, preco=2800.0, fundo="Fundo C"),
    OrdemAtivo(nome_ativo="AMZN", amount=10, venda=True, preco=3300.0, fundo="Fundo A"),
    OrdemAtivo(nome_ativo="META", amount=30, venda=False, preco=210.3, fundo="Fundo D"),
    OrdemAtivo(nome_ativo="NFLX", amount=25, venda=True, preco=600.0, fundo="Fundo B"),
    OrdemAtivo(nome_ativo="MSFT", amount=40, venda=False, preco=299.9, fundo="Fundo C"),
    OrdemAtivo(nome_ativo="NVDA", amount=35, venda=True, preco=700.4, fundo="Fundo D"),
    OrdemAtivo(nome_ativo="INTC", amount=45, venda=False, preco=56.7, fundo="Fundo A"),
    OrdemAtivo(nome_ativo="AMD", amount=60, venda=True, preco=120.2, fundo="Fundo B")
]


# COMMAND ----------

"""
Retorna o book que um ativo pertence
"""


df_books = spark.sql("""
                     SELECT * FROM desafio_kinea.boletagem_cp.book_ativos
                     """)
df_books.show()

def get_books_do_ativo(ativo:str,df_books:DataFrame)->list[str]:
   """
   Retorna uma lista de books do ativo
   """
   return [ row["book"] for row in
        df_books.filter(df_books["ativo"] == ativo).select("book").collect()
   ]

get_books_do_ativo("CESE22",df_books)

# COMMAND ----------

"""
Trabalhar com os ratings das tabelacar_
"""


def primeiro_numero_e_posicao(string:str)->tuple[int,int]:
    for i,char in enumerate(string):
        if char.isnumeric():
            return int(char), i
    
    return -1,-1

def construir_dict_ratings(lista_ratings:list[str],list_niveis:list[int])->dict:
    dict_ratings = {}
    for rating,nivel in zip(lista_ratings,list_niveis):
        valores_nivel = []
        if " a " in rating: #rating é um range
            if "Aaa" in rating:
                valores_nivel = ["Aaa","Aa2","Aa3"] #Por enquanto vai ficar hardcoded ppq eu n entendi essa parte
            else:
                primeiro_num, index1 = primeiro_numero_e_posicao(rating)
                segundo_num,  index2 = primeiro_numero_e_posicao(rating[index1+1:])

                str_base = rating[:index1]
                valores_nivel = [
                    f"{str_base}{str(x)}" for x in range(primeiro_num,segundo_num+1)
                ]
        else:
            valores_nivel = [rating]
        dict_ratings[nivel] = valores_nivel
    return dict_ratings

def get_ratings_igual_abaixo(rating:str)->list[str]:
    df_ratings = spark.sql("""SELECT * FROM desafio_kinea.boletagem_cp.tabelacar_baixorisco """
                           ).sort("Nivel").collect()
    #df_ratings.show()  # Shows the content of the DataFrame
    #print(df_ratings.count())  # Prints the number of rows in the DataFrame
    lista_ratings = []
    lista_nivels = []
    for row in df_ratings:
        #print(row["IntervaloRating"],row["Nivel"])
        lista_ratings.append(row["IntervaloRating"])
        lista_nivels.append(row["Nivel"])
    
    ratings_dict = construir_dict_ratings(lista_ratings,lista_nivels)

    best_level = -1
    for key,val in  sorted(ratings_dict.items(),key= lambda x: x[0]):
        if rating in val: #se o rating esta na lista
            best_level  = key
            break
    if best_level == -1:
        raise RuntimeError("Não foi possível achar nível do rating")
    
    print(best_level)
    return dict(
        filter(lambda x: x[0] >= best_level,ratings_dict.items()) #essa equação ou inequação é a principal coisa a se mudar caso precise modificar a lógica
    )

get_ratings_igual_abaixo("Aaa")
#rating_igual_ou_menor("A1","A1 a A4")

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT * FROM desafio_kinea.boletagem_cp.tabelacar_baixorisco
