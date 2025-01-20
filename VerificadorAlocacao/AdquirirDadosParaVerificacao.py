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

class _Queries:
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

    def tabelascar_pl_anos_ativos(self, vencimento_maior_que:int)->DataFrame:
        query:str = self.dict_queries["tabelascar_L_anos.sql"]
        query = query.format(anos_filtro=vencimento_maior_que)
        print(query)
        return spark.sql(query)
      
    def tabelascar_pl_emissor(self)->DataFrame:
        query:str = self.dict_queries["tabelascar_pl_emissores.sql"]
        return spark.sql(query)
      
    def tabelascar_info_fundos(self, list_ratings:list[str] )->DataFrame:
        query:str = self.dict_queries["tabelascar_info_fundos.sql"]
        lista_ratings = "(" + ",".join(f"'{value}'" for value in list_ratings) + ")"
        query  = query.format(lista_ratings=lista_ratings)
        return spark.sql(query)

    def tabelascar_info_ativos(self)->DataFrame:
        query:str = self.dict_queries["tabelascar_info_ativos.sql"]
        return spark.sql(query)  

# COMMAND ----------


que = _Queries()

df = que.tabelascar_pl_emissor() 
print(df.show())


# COMMAND ----------

from dataclasses import dataclass
import pandas as pd
import math
from datetime import timedelta, datetime

class DadosAlocacao:
    
    __QUERIES = _Queries()
    __ARQUIVOS_SQL: list[str] = __QUERIES.ARQUIVOS_SQL
    __ARQUIVOS_DATAS = "datas_atualizacao.csv"
    __DATAS_PARA_ATUALIZAR:dict = {
        "tabelascar_pl_emissores.sql": timedelta(weeks=1),
        "tabelascar_L_anos.sql": timedelta(weeks=1),
        "tabelascar_info_fundos.sql": timedelta(weeks=1),
        "tabelascar_info_ativos.sql": timedelta(weeks=1)
    }
    __MAPA_TABELAS_METODOS:dict = {
        "tabelascar_pl_emissores.sql": __QUERIES.tabelascar_pl_emissor,
        "tabelascar_L_anos.sql":  __QUERIES.tabelascar_pl_anos_ativos,
        "tabelascar_info_fundos.sql": __QUERIES.tabelascar_info_fundos,
        "tabelascar_info_ativos.sql": __QUERIES.tabelascar_info_ativos
    }
    __METODOS_COM_ARGS = ["tabelascar_L_anos.sql","tabelascar_info_fundos.sql"]

    datas_atualizacao:dict[str, datetime | None] #dado o nome de uma query/tabela diz qual foi a última vez que ela foi atualizada
    path_folder_dados:Path

    def __init__(self):
        dir_atual = Path(os.getcwd())
        path_final = dir_atual.absolute() / Path("DadosVerificacao")
        self.path_folder_dados = path_final
        self.__ler_arquivo_datas()
        self.__verifica_dados_atualizados()
       
    def __ler_arquivo_datas(self)->None:
        if not Path(self.__ARQUIVOS_DATAS).exists():
            pass
        
        path = self.path_folder_dados / Path(self.__ARQUIVOS_DATAS)     
        try:
            datas_df = pd.read_csv(path)
        except Exception as e:
            print("Falha ao ler arquivo de datas atualizacao, criando novo arquivo")
            datas_df = pd.DataFrame(columns=["nome_tabela","data_atualizacao"])
            for i in self.__ARQUIVOS_SQL:
                new_row = pd.DataFrame({"nome_tabela": [i], "data_atualizacao": [None]})
                datas_df = pd.concat([datas_df, new_row], ignore_index=True)
            datas_df.to_csv(path,index=False)

        datas_atualizacao = {}
        for row in datas_df.itertuples():
            print(row.data_atualizacao)
            if isinstance(row.data_atualizacao, float): #nan/null
                data  = None
            else:
                data = datetime.strptime(row.data_atualizacao, "%Y-%m-%d %H:%M:%S.%f")
            datas_atualizacao[row.nome_tabela] = data
        print(datas_df)
        self.datas_atualizacao = datas_atualizacao

    def __escreve_arquivo_datas(self)->None:
        print("atualizando datas")
        path = self.path_folder_dados / Path(self.__ARQUIVOS_DATAS)
        datas_df = pd.DataFrame(columns=["nome_tabela","data_atualizacao"])
        for i in self.__ARQUIVOS_SQL:
            new_row = pd.DataFrame({"nome_tabela": [i], "data_atualizacao": [self.datas_atualizacao[i]]})
            datas_df = pd.concat([datas_df, new_row], ignore_index=True)
        datas_df.to_csv(path,index=False)

    def __verifica_dados_atualizados(self)->None:
        atualizou_tabela = False
        for tabela,data_atualizacao in self.datas_atualizacao.items():
            tempo_max_atualizar = self.__DATAS_PARA_ATUALIZAR[tabela]
            if data_atualizacao is None: #atualiza dados
                atualizou_tabela = True
                self.__atualizar_dados(tabela) 
                continue
            
            tempo_passado = datetime.now() - data_atualizacao
            if tempo_passado > tempo_max_atualizar: #atualiza dados
                atualizou_tabela = True
                self.__atualizar_dados(tabela) 
        
        if atualizou_tabela:
            self.__escreve_arquivo_datas()

    def __atualizar_tabelas_arg(self,tabela:str):
        if tabela == "tabelascar_L_anos.sql":
            pass
        elif tabela == "tabelascar_info_fundos.sql":
            pass
        else:
            raise Exception("Tabela com argumento passada para essa função não teve sua lógica implementada")

    def __atualizar_dados(self,tabela:str)->None:
        if tabela in self.__METODOS_COM_ARGS:
            pass #logica especial
        else:        
            df = self.__MAPA_TABELAS_METODOS[tabela]().toPandas()
            path = str(self.path_folder_dados / Path(f"{tabela}.csv"))
            df.to_csv(path,index=False)
            #df.write.csv(path, mode="overwrite")
            self.datas_atualizacao[tabela] = datetime.now()
        
            


# COMMAND ----------

dados = DadosAlocacao()
