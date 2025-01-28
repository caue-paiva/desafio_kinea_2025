"""
Script para executar Verificações
"""
from VerificadorTabelacar import  VerificadorTabelacar
from DadosAlocacao import DadosAlocacao
import pandas as pd

def ExecutarVerificacoes():
    verificador = VerificadorTabelacar()
    for i in dbutils.fs.ls("/Volumes/desafio_kinea/boletagem_cp/files/Reguas/"): #para cada régua de ativo nesse path, vamos passar a régua inicial pelo verificador e salvar o resultado em um CSV
        ativo:str = i.name.split("_")[1].removesuffix(".csv") #pega nome do ativo pelo 
        alocacao = pd.read_csv(i.path.removeprefix("dbfs:")).drop(columns='book')
        resultado_verificacao = verificador.verifica_alocacao(alocacao,ativo)
        resultado_verificacao.to_csv(f"/Volumes/desafio_kinea/boletagem_cp/files/VerificacaoTabelasCar/VERIFICACAO_{ativo}.csv",index=False)
if __name__ == '__main__':
    regua = ExecutarVerificacoes()