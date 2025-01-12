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
