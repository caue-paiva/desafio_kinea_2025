"""
Vamos ter uma task com trigger de um upload de um CSV no folder /volumes/ordems e a task irá executar esse código, que irá chamar a função de calcular regua para cada ativo da ordem
"""
import pandas as pd
from pathlib import Path
from CalculoReguaMacro import ReguaMacro
class ProcessaOrdem: 
    """
    Classe que ao ser instanciada processa a ordem mais atual no volume de arquivos do desafio no path /Ordem/, salvando ela como um df.
    Essa classe tem o método processar_ordem que irá processar a ordem  e chamar a função de calcular régua para cada ativo da ordem, salvando as réguas no volume do desafio
    """
    def __init__(self): 
        self.input_path = Path("/Volumes/desafio_kinea/boletagem_cp/files/Ordem/Ordem.csv")
        self.ordem = pd.read_csv(self.input_path,sep="\t")
        self.ordem['qtde'] = self.ordem['qtde'].str.replace(",","").astype(float)
    def __get_alocacao_total_por_ativo(self)->pd.DataFrame:
        df = self.ordem
        df["alocacao_total"] = df["qtde"] * df["preco"]
        df_agrupado = df.groupby("ticker").sum().reset_index()
        display(df_agrupado)
        return df_agrupado
        

    def processar_ordem(self): 
        path_alocacao_trade = Path("/Volumes/desafio_kinea/boletagem_cp/files/Ordem") / Path(f"Alocacao_total_ordem.csv") #path para guardar o CSV do volume de alocação da ordem
        alocacao_por_ativo:pd.DataFrame = self.__get_alocacao_total_por_ativo() #calcula a alocação total da ordem por ativo
        alocacao_por_ativo.to_csv(path_alocacao_trade, index=False) #salva esse df num arquivo

        #calculaa régua para cada arquivo da ordem
        for index, row in self.ordem.iterrows():
            regua = ReguaMacro()
            regua.calcula_regua(row["ticker"],row['book'],True) #calcula régua e salva no volume

if __name__ == "__main__":
    ordem = ProcessaOrdem()
    ordem.processar_ordem()
