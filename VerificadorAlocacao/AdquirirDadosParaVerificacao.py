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

    RATINGS_POR_NIVEL_TABELACAR  = {
            0: ["Aaa", "Aaa1", "Aaa2", "Aaa3"],
            1: ["A1", "A2", "A3", "A4"],
            2: ["Baa1"],
            3: ["Baa3", "Baa4"],
            4: ["Ba1"],
            5: ["Pior"]
    }
    ANOS_FILTRAGEM_DURACAO_ATIVO = [0,2,4,6,8,10]

    dict_queries:dict[str,str] #mapea o nome de um arquivo/nome da query à string da propia query
    path_folder_queries:  Path
    query_tabelascar_pl_anos_ativos:str
    query_tabelascar_pl_emissor:str

    def __init__(self):
        dir_atual = Path(os.getcwd())
        path_final = dir_atual.absolute().parent / Path("ScriptsSQL") / Path("TemplatesPython")
        self.path_folder_queries = path_final
        self.__ler_arquivos_queries() #lé os arquivos das queries

    def __get_ratings_por_nivel(self,nivel_tabela_car:int)->list[str]:
        """
        Dado um nível da tabelacar retorna todos os ratings que correspondem ao nível, sendo iguais ou inferiores
        """
        lista_ratings = []
        for nivel_ratings in self.RATINGS_POR_NIVEL_TABELACAR:
            if nivel_ratings >= nivel_tabela_car: #nível 0 é o com melhor rating, ele inclui todos abaixo
                lista_ratings.extend(self.RATINGS_POR_NIVEL_TABELACAR[nivel_ratings]) #add esses ratings na lista
        
        return lista_ratings


    def __ler_arquivos_queries(self)->None:
        """
        Le arquivos .sql das queries e guarda eles num dict para uso pelas outras funções
        """
        dict_queries = {}
        for nome_arqui in self.ARQUIVOS_SQL:
          with open(self.path_folder_queries / Path(nome_arqui), "r") as file:
            dict_queries[nome_arqui] = file.read()
        
        self.dict_queries = dict_queries

    def tabelascar_pl_anos_ativos(self, vencimento_maior_que:int)->DataFrame:
        """
        Retorna um Dataframe correspondente ao PL de crédito privado de cada fundo alocado por cada emissor, com os ativos que correspondem à esse valor por emissor tendo seu vencimento em anos maior que o argumento
        """
        query:str = self.dict_queries["tabelascar_L_anos.sql"]
        query = query.format(anos_filtro=vencimento_maior_que)
        return spark.sql(query)
      
    def tabelascar_pl_emissor(self)->DataFrame:
        """
        Retorna um Dataframe correspondente ao PL de crédito privado de cada fundo alocado por cada emissor, com o rating do emissor incluido
        """
        query:str = self.dict_queries["tabelascar_pl_emissores.sql"]
        return spark.sql(query)
      
    def tabelascar_info_fundos(self, nivel_tabela_car:int)->DataFrame:
        """
        Dado um nível da tabelacar, retorna o dataframe correspondente ao PL de crédito privado de cada fundo composto por ativos cujo rating corresponde (igual ou maior) ao nível da tabela_car
        """
        lista_ratings:list[str] = self.__get_ratings_por_nivel(nivel_tabela_car)
        query:str = self.dict_queries["tabelascar_info_fundos.sql"]
        lista_ratings = "(" + ",".join(f"'{value}'" for value in lista_ratings) + ")"
        query  = query.format(lista_ratings=lista_ratings)
        return spark.sql(query)

    def tabelascar_info_ativos(self)->DataFrame:
        """
        Retorna informações sobre ativos de crédito privado, como seu rating, seu emissor, o rating do seu emissor e o tempo até ele vencer
        """
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
            print("atualiza tabela de L anos")
            self.__calcula_niveis_tabelascar_L_anos()
        elif tabela == "tabelascar_info_fundos.sql":
            print("atualiza info fundos")
            self.__calcula_niveis_info_fundos()
        else:
            raise Exception("Tabela com argumento passada para essa função não teve sua lógica implementada")

    def __atualizar_dados(self,tabela:str)->None:
        if tabela in self.__METODOS_COM_ARGS:
            print("atualiza especial")
            self.__atualizar_tabelas_arg(tabela)
        else:        
            df = self.__MAPA_TABELAS_METODOS[tabela]().toPandas()
            path = str(self.path_folder_dados / Path(f"{tabela}.csv"))
            df.to_csv(path,index=False)
            #df.write.csv(path, mode="overwrite")
        self.datas_atualizacao[tabela] = datetime.now()
        
    def __calcula_niveis_info_fundos(self)->None:
        """
        Calcula Dataframes da tabela de info fundos (PL de crédito privado de cada fundo filtrado por rating) de acordo com cada nível da tabelacar, do nível 0 (com melhores ratings) até abaixo. Salva todos os arquivos em formato csv. Os arquivos são nomeados dessa forma:  "tabelascar_info_fundos_nivel{num_nivel}.csv"
        """
        for nivel in self.__QUERIES.RATINGS_POR_NIVEL_TABELACAR:
            df = self.__QUERIES.tabelascar_info_fundos(nivel).toPandas()
            path = str(self.path_folder_dados / Path(f"tabelascar_info_fundos.sql{nivel}.csv"))
            df.to_csv(path,index=False)
        self.datas_atualizacao["tabelascar_info_fundos.sql"] = datetime.now()

    def __calcula_niveis_tabelascar_L_anos(self)->None:
        """
        Calcula os dataframes da tabela de crédito privado de um fundo, agregado por emissor mas contando apenas os ativos de cada emissor com data de expiração (em anos) igual or maior que certo número. Salva todos os arquivos em formato csv. Os arquivos são nomeados dessa forma:  "tabelascar_L_anos{ano}.csv"
        """
        for ano in self.__QUERIES.ANOS_FILTRAGEM_DURACAO_ATIVO:
            df = self.__QUERIES.tabelascar_pl_anos_ativos(ano).toPandas()
            path = str(self.path_folder_dados / Path(f"tabelascar_L_anos{ano}.csv"))
            df.to_csv(path,index=False)
            self.datas_atualizacao["tabelascar_L_anos.sql"] = datetime.now()


# COMMAND ----------

dados = DadosAlocacao()
