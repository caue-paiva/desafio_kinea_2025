from DadosAlocacao import DadosAlocacao
import pandas as pd
from pathlib import Path
from datetime import datetime

class ParserNexxus:

    __DADOS= DadosAlocacao()
    __PATH_REGUAS = Path("/Volumes/desafio_kinea/boletagem_cp/files/ReguasOtimizadas/")
    __PATH_INPUT_NEXXUS = Path("/Volumes/desafio_kinea/boletagem_cp/files/InputNexxus/")
    __PATH_RESULTADO_NEXXUS = Path("/Volumes/desafio_kinea/boletagem_cp/files/ResultadoFinal/")

    def __init__(self):
        pass


    def __agrega_reguas(self)->pd.DataFrame:
        """
        Agrega todas as réguas no diretório ReguasOtimizadas em um DF único
        """
        path = Path("/Volumes/desafio_kinea/boletagem_cp/files/InputNexxus/input_nexxus.csv")
        return pd.read_csv(path)

    def regua_para_nexxus(self, nome_arquivo_finalizado:str = "input_nexxus_ali.csv")->None:
        """
        Agrega todos os arquivos de réguas otimizadas no diretório ReguasOtimizadas do volume em um único CSV no formato que o nexxus requer. Salva o arquivo de input para o nexxus no diretório
        InputNexxus do volume.

        Args:
            nome_arquivo_finalizado (str): Nome final em que o CSV de input pro nexxus irá ter, por padrão é "input_nexxus_teste.csv"
        Return:
            None
        """
        reguas_agregadas:pd.DataFrame = self.__agrega_reguas()
        data_atual = datetime.today().date()
        reguas_agregadas["trade_date"] = data_atual #coluna da data da trade

        reguas_agregadas = reguas_agregadas.rename({ #renomeia colunas
            "FUNDO":"trading_desk",
            "PU":"price",
            "QTDE": "amount",
            "ATIVO": "Product",
            "VALOR": "financial_price"
        },axis=1)

        df_classe_produtos = self.__DADOS.get_classe_produto() #df que mapeia cada ativo/produto com sua classe
        reguas_agregadas = pd.merge(reguas_agregadas, df_classe_produtos, on="Product") #inner join pelo produto, para trazer a classe
        reguas_agregadas = reguas_agregadas.rename({"ProductClass":"product_class","Product":"product"},axis=1)

        
        reguas_agregadas = reguas_agregadas.drop(columns=["Unnamed: 0"],axis=1)
        reguas_agregadas.to_csv(self.__PATH_INPUT_NEXXUS / nome_arquivo_finalizado, index=False) #salva no diretório de inputs para o Nexxus



    def nexxus_para_boletagem(self)->bool:
        """
        Parsing no resultado do nexxus (enquadrado) para o formato que o Ali usa na boletagem final. Salva o resulltado final no diretório ResultadoFinal do volume
        """


if __name__ == "__main__":
    parser = ParserNexxus()
    parser.regua_para_nexxus()