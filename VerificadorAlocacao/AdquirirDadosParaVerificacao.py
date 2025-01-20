# Databricks notebook source
"""
Script para poder pegar dados atualizados para conseguir a verificação da alocação

Dados que serão extraídos:

1) PL de cada fundo
2) PL de cŕedito privado de cada fundo
3) Book(s) de um ativo

"""

# COMMAND ----------

from pyspark.sql import DataFrame
from datetime import datetime

class DadosAlocacao:

    df_pl_fundos: DataFrame
    df_pl_credito_privado: DataFrame
    df_book_ativos: DataFrame
    data_extracao_dados: datetime

    def __init__(self):
        self.__atualizar_dados()

    def __atualizar_dados(self)->None:
        self.df_pl_fundos = self.__get_pl_fundos_aux()
        self.df_pl_credito_privado = self.__get_pl_credito_privado_aux()
        self.df_book_ativos = self.__get_book_ativos_aux()
        self.data_extracao_dados = datetime.now()

    def __get_pl_fundos_aux(self):
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

    def __get_pl_credito_privado_aux(self):
        pass

    def __get_book_ativos_aux(self):
        pass

    def __dados_estao_atualizados(self)->bool:
        diferen_tempo = datetime.now() - self.data_extracao_dados
        return diferen_tempo.total_seconds() < 86400 #24 horas ou menos de diferença entre a última data de extração e a data atual

    #métodos para retornar dataframes dos dados necessários

    def get_df_pl_fundos(self)->DataFrame:
        if not self.__dados_estao_atualizados(): #dados desatualizados
           self.__atualizar_dados() #atualiza dados 
        return self.df_pl_fundos

    def get_df_pl_credito_privado(self)->DataFrame:
        if not self.__dados_estao_atualizados(): #dados desatualizados
           self.__atualizar_dados() #atualiza dados 
        return self.df_pl_credito_privado

    def get_df_book_ativos(self)->DataFrame:
        if not self.__dados_estao_atualizados(): #dados desatualizados
           self.__atualizar_dados() #atualiza dados 
        return self.df_book_ativos

    #métodos para retornar valores específicos de um fundo ou book

    def get_pl_fundo(self,fundo:str)->float:
        if not self.__dados_estao_atualizados(): #dados desatualizados
           self.__atualizar_dados() #atualiza dados 

    def get_pl_credito_privado_fundo(self,fundo:str)->float:
        if not self.__dados_estao_atualizados(): #dados desatualizados
           self.__atualizar_dados() #atualiza dados 

    def get_book_ativo(self,ativo:str)->list[str]:
        if not self.__dados_estao_atualizados(): #dados desatualizados
           self.__atualizar_dados() #atualiza dados 

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT * FROM desafio_kinea.boletagem_cp.tabelacar_baixorisco

# COMMAND ----------

df=_sqldf.toPandas()
print(df.info())

# COMMAND ----------

import os
from pathlib import Path

class __Queries:


    ARQUIVOS_SQL = [
      "tabelascar_L_anos.sql",
      "tabelascar_pl_emissores.sql",
      "tabelascar_info_fundos.sql",
      "tabelascar_info_ativos.sql"
    ]

    dict_queries:dict[str,str] #mapea o nome de um arquivo/nome da query à string da propia query
    path_folder_queries:  Path
    query_tabelascar_pl_anos_ativos:str
    query_tabelascar_pl_emissor:str

    def __init__(self):
        dir_atual = Path(os.getcwd())
        path_final = dir_atual.absolute().parent / Path("ScriptsSQL") / Path("TemplatesPython")
        self.path_folder_queries = path_final
        self.read_query_files() #lé os arquivos das queries

    def read_query_files(self)->None:
        dict_queries = {}
        for nome_arqui in self.ARQUIVOS_SQL:
          with open(self.path_folder_queries / Path(nome_arqui), "r") as file:
            dict_queries[nome_arqui] = file.read()
        
        self.dict_queries = dict_queries

    def tabelascar_pl_anos_ativos(self,vencimento_maior_que:int)->DataFrame:
        query:str = self.dict_queries["tabelascar_L_anos.sql"]
        return spark.sql(query)
      
    def tabelascar_pl_emissor(self)->DataFrame:
        query:str = self.dict_queries["tabelascar_pl_emissores.sql"]
        return spark.sql(query)
      
    def tabelascar_info_fundos(self)->DataFrame:
        query:str = self.dict_queries["tabelascar_info_fundos.sql"]
        return spark.sql(query)

    def tabelascar_info_ativos(self)->DataFrame:
        query:str = self.dict_queries["tabelascar_info_ativos.sql"]
        return spark.sql(query)  

# COMMAND ----------


que = __Queries()

df = que.tabelascar_info_fundos()
print(df.show())

