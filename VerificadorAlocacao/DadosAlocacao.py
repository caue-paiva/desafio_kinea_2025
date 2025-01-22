import os
from pathlib import Path
from pyspark.sql import DataFrame
from databricks.sdk.runtime import *
from dataclasses import dataclass
import pandas as pd
import math
from datetime import timedelta, datetime

class _Queries:
    
    ARQUIVOS_SQL = [
      "tabelascar_L_anos.sql",
      "tabelascar_pl_emissores.sql",
      "tabelascar_info_fundos.sql",
      "tabelascar_info_ativos.sql",
      "PL_total_fundo.sql",
      "PL_credito_privado_por_fundo.sql",
      #"PL_total_e_credito_privado_fundos.sql",
      "mapa_tabelacar.sql"
    ]
    RATINGS_ORDENADOS  = [
        "Aaa", "Aa2", "Aa3",
        "A1", "A2","A3", "A4",
        "Baa1","Baa2", "Baa3", "Baa4",
        "Ba1","Ba4","Ba5","Ba6",
        "B1", "B2", "B3","B4",
        "C1", "C2", "C3",
        "D1", "D2", "D3",
        "E1"
   ]
    
    #primeiro índice = melhor rating = está no menor nível (0 da tabelacar)
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

    def __get_ratings_iguais_ou_inferiores(self,rating:str)->list[str]:
        """
        Dado um rating da tabelacar retorna todos os ratings iguais ou inferiores
        """
        rating_parsed = rating.lower().strip()
        for i,nivel_ratings in enumerate(self.RATINGS_ORDENADOS):
            if nivel_ratings.lower() == rating_parsed: #achou rating
                return self.RATINGS_ORDENADOS[i:] #retorna a lista a partir desse rating
        return []

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
      
    def tabelascar_info_fundos(self, rating:str)->DataFrame:
        """
        Dado um nível da tabelacar, retorna o dataframe correspondente ao PL de crédito privado de cada fundo composto por ativos com rating piores ou igual ao especificado
        """
        lista_ratings:list[str] = self.__get_ratings_iguais_ou_inferiores(rating)
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

    def pl_total_fundos(self)->DataFrame:
        """
        Retorna um DF com o PL total de cada fundo
        """
        query = self.dict_queries["PL_total_fundo.sql"]
        return spark.sql(query)
    
    def pl_credito_privado_fundos(self)->DataFrame:
        """
        Retorna um DF com o PL de crédito privado de cada fundo
        """
        query = self.dict_queries["PL_credito_privado_por_fundo.sql"]
        return spark.sql(query)
    
    def mapa_tabelacar(self)->DataFrame:
        """
        Retorna um DF com o mapa da tabela car
        """
        query = self.dict_queries["mapa_tabelacar.sql"]
        return spark.sql(query)
    
class DadosAlocacao:
    
    __QUERIES = _Queries()
    __ARQUIVOS_SQL: list[str] = __QUERIES.ARQUIVOS_SQL
    __ARQUIVOS_DATAS = "datas_atualizacao.csv"
    __DATAS_PARA_ATUALIZAR:dict = {
        "tabelascar_pl_emissores": timedelta(days=1),
        "tabelascar_L_anos": timedelta(days=1),
        "tabelascar_info_fundos": timedelta(days=1),
        "tabelascar_info_ativos": timedelta(days=1),
        "PL_total_fundo": timedelta(days=1),
        "PL_credito_privado_por_fundo": timedelta(days=1),
        "mapa_tabelacar": timedelta(weeks=4),
    }
    __MAPA_TABELAS_METODOS:dict = {
        "tabelascar_pl_emissores": __QUERIES.tabelascar_pl_emissor,
        "tabelascar_L_anos":  __QUERIES.tabelascar_pl_anos_ativos,
        "tabelascar_info_fundos": __QUERIES.tabelascar_info_fundos,
        "tabelascar_info_ativos": __QUERIES.tabelascar_info_ativos,
        "PL_total_fundo": __QUERIES.pl_total_fundos,
        "PL_credito_privado_por_fundo": __QUERIES.pl_credito_privado_fundos,
        "mapa_tabelacar": __QUERIES.mapa_tabelacar
    }
    __METODOS_COM_ARGS = ["tabelascar_L_anos","tabelascar_info_fundos"]

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
            for i in self.__DATAS_PARA_ATUALIZAR:
                new_row = pd.DataFrame({"nome_tabela": [i], "data_atualizacao": [None]})
                datas_df = pd.concat([datas_df, new_row], ignore_index=True)
            datas_df.to_csv(path,index=False)

        datas_atualizacao = {}
        for row in datas_df.itertuples():  
            if isinstance(row.data_atualizacao, float) or row.data_atualizacao is None : #nan/null
                data  = None
            else:
                data = datetime.strptime(row.data_atualizacao, "%Y-%m-%d %H:%M:%S.%f")
            datas_atualizacao[row.nome_tabela] = data
        self.datas_atualizacao = datas_atualizacao

    def __escreve_arquivo_datas(self)->None:
        path = self.path_folder_dados / Path(self.__ARQUIVOS_DATAS)
        datas_df = pd.DataFrame(columns=["nome_tabela","data_atualizacao"])
        for i in self.__DATAS_PARA_ATUALIZAR:
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
        """
        Atualiza arquivos cujos métodos requerem argumentos, nesse caso são os para gerar as tabelas por ratings e por anos de expiracao dos ativos (L_anos)
        """
        if tabela == "tabelascar_L_anos":
            #print("atualiza tabela de L anos")
            self.__calcula_niveis_tabelascar_L_anos()
        elif tabela == "tabelascar_info_fundos":
            #print("atualiza info fundos")
            self.__calcula_ratings_info_fundos()
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
        
    def __calcula_ratings_info_fundos(self)->None:
        """
        Calcula Dataframes da tabela de info fundos (PL de crédito privado de cada fundo filtrado por rating) de acordo com cada rating da tabelacar, agregando ativos de rating igual ou pior para a liquidez . Salva todos os arquivos em formato csv. Os arquivos são nomeados dessa forma:  "tabelascar_info_fundos_rating_{rating}.csv"
        """
        for rating in self.__QUERIES.RATINGS_ORDENADOS:
            df = self.__QUERIES.tabelascar_info_fundos(rating).toPandas()
            path = str(self.path_folder_dados / Path(f"tabelascar_info_fundos_rating_{rating}.csv"))
            df.to_csv(path,index=False)
        self.datas_atualizacao["tabelascar_info_fundos"] = datetime.now()

    def __calcula_niveis_tabelascar_L_anos(self)->None:
        """
        Calcula os dataframes da tabela de crédito privado de um fundo, agregado por emissor mas contando apenas os ativos de cada emissor com data de expiração (em anos) igual or maior que certo número. Salva todos os arquivos em formato csv. Os arquivos são nomeados dessa forma:  "tabelascar_L_anos{ano}.csv"
        """
        for ano in self.__QUERIES.ANOS_FILTRAGEM_DURACAO_ATIVO:
            df = self.__QUERIES.tabelascar_pl_anos_ativos(ano).toPandas()
            path = str(self.path_folder_dados / Path(f"tabelascar_L_anos{ano}.csv"))
            df.to_csv(path,index=False)
            self.datas_atualizacao["tabelascar_L_anos"] = datetime.now()

    def __ler_csv(self,nome_tabela:str)->pd.DataFrame | None:
        try:
            path = self.path_folder_dados / Path(f"{nome_tabela}")
            df = pd.read_csv(path)
            return df
        except Exception as e:
            print(f"Falha ao ler o arquivo: {path}/{nome_tabela}. Erro: {e}")
            return None
        
    
    def _pl_emissor_vencimento_ano_aux(self,anos_vencimentos:int)->pd.DataFrame | None:
        """
        Objetivo: A query em SQL de pegar o PL de um emissor filtrado pelos anos de vencimento. de ativos tem o problema de excluir algumas combinações de emissores e fundos por eles terem 0 de pl (nenhum ativo) que satisfaz o filtro.
        Esse método faz a query sem filtro, acha as combinações única que estão faltando e dá append no dataframe delas com soma de PL 0
        """

        df_sem_filtro = self.get_pl_e_rating_por_emissor()
        if df_sem_filtro is None:
            return None
        df_sem_filtro = df_sem_filtro[ ["Emissor","TradingDesk","RatingGrupo","PL"] ] #pega apenas todas as colunas menos o PL filtrado de cada emissor
        df_filtrado = self.__ler_csv(f"tabelascar_L_anos{anos_vencimentos}.csv") #df filtrado
        df_join = df_sem_filtro.merge(df_filtrado,how="left",on=["Emissor","TradingDesk","RatingGrupo","PL"]) #left join, trazendo todas as combinações possíveis de Emissor e Trading desk
        df_join = df_join.fillna(0) #valores nulos viram 0

        return df_join

    def get_pl_e_rating_por_emissor(self)->pd.DataFrame | None:
        """
        Retorna uma tabela com o  PL de crédito privado de cada emissor em cada fundo, com os ratings de cada emissor.
        """
        self.__verifica_dados_atualizados() #verifica se dados estão atualizados
        return self.__ler_csv("tabelascar_pl_emissores.csv")

    def get_pl_fundo_por_rating(self,rating:str)->pd.DataFrame | None:
        """
        Retorna o PL de crédito privado de um fundo filtrando por ativos com rating igual ou pior que o especificado
        """
        self.__verifica_dados_atualizados()
        return self.__ler_csv(f"tabelascar_info_fundos_rating_{rating}.csv")

    def get_pl_por_emissor_e_vencimento_anos(self,anos_vencimentos:int)->pd.DataFrame | None:
        """
        Retorna uma tabela com o  PL de crédito privado de cada emissor em cada fundo, porém apenas contabilizando os ativos que tem data de vencimento igual ou maior que o especificado.
        """
        self.__verifica_dados_atualizados()
        return self._pl_emissor_vencimento_ano_aux(anos_vencimentos) #função auxiliar com lógica extra para lidar com valores que faltam com a filtragem

    def get_info_rating_ativos(self)->pd.DataFrame | None:
        """
        Retorna um DF com as informações de cada ativo, como seu rating, seu emissor e qual o rating do seu emissor
        """
        self.__verifica_dados_atualizados()
        return self.__ler_csv("tabelascar_info_ativos.csv")
    
    def get_pl_total_fundos(self) -> pd.DataFrame | None:
        """
        Retorna um DF com o PL total de cada fundo
        """
        self.__verifica_dados_atualizados()
        return self.__ler_csv("PL_total_fundo.csv")
    
    def get_pl_credito_privado_fundos(self) -> pd.DataFrame | None:
        """
        Retorna um DF com o PL de crédito privado de cada fundo
        """
        self.__verifica_dados_atualizados()
        return self.__ler_csv("PL_credito_privado_por_fundo.csv")
    

    def get_pl_total_e_credito_privado(self) -> pd.DataFrame | None:
        """
        Retorna um DF com o PL total e pl de crédito privado de cada fundo
        """
        self.__verifica_dados_atualizados()
        df1 = self.get_pl_credito_privado_fundos()
        df2 = self.get_pl_total_fundos()
        
    
    def get_mapa_tabelacar(self) -> pd.DataFrame | None:
        """
        Retorna um DF com o mapeamento de cada fundo para a sua tabelacar correspondente
        """
        self.__verifica_dados_atualizados()
        return self.__ler_csv("mapa_tabelacar.csv")


if __name__ == "__main__":
    dados = DadosAlocacao()
    df = dados.get_pl_por_emissor_e_vencimento_anos(6)
    display(df)
