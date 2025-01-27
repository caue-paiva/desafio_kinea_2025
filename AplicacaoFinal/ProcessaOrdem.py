"""
Vamos ter uma task com trigger de um upload de um CSV no folder /volumes/ordems e a task irá executar esse código, que irá chamar a função de calcular regua para cada ativo da ordem
"""
import pandas as pd
from pathlib import Path
from CalculoReguaMacro import ReguaMacro
class ProcessaOrdem:
    def __init__(self):
        self.input_path = Path("/Volumes/desafio_kinea/boletagem_cp/files/Ordem/Ordem.csv")
        self.ordem = pd.read_csv(self.input_path)

    def processar_ordem(self):
        for index, row in self.ordem.iterrows():
            regua = ReguaMacro()
            regua.calcula_regua(row["ativo"],True)

if __name__ == "__main__":
    ordem = ProcessaOrdem()
    ordem.processar_ordem()
