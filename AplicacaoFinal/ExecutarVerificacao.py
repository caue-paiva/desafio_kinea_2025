"""
Script para executar Verificações
"""
from VerificadorTabelacar import  VerificadorTabelacar
from DadosAlocacao import DadosAlocacao
import pandas as pd

def ExecutarVerificacoes():
    for i in dbutils.fs.ls("/Volumes/desafio_kinea/boletagem_cp/files/Reguas/"):
        ativo = i.name.split("_")[1].removesuffix(".csv")
        alocacao = pd.read_csv(i.path.removeprefix("dbfs:")).drop(columns='book')
        alocacao_dic = {}
        alocacao_dic['fundo'] = alocacao['fundo'].tolist()
        alocacao_dic['valor'] = alocacao['percentual_alocacao'].tolist()
        verificador = VerificadorTabelacar()
        resultado_verificacao = verificador.verifica_alocacao(alocacao_dic,ativo)
    
if __name__ == '__main__':
    regua = ExecutarVerificacoes()