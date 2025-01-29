"""
Script para executar Verificações
"""
import sys
from VerificadorTabelacar import VerificadorTabelacar
from DadosAlocacao import DadosAlocacao
from Otimizacao import otimiza_regua #essa função recebe 2 df como arg
import pandas as pd

def ExecutarVerificacoes():
    """
    Com as réguas iniciais dos ativos de uma dada ordem salvas no volume do desafio /Reguas/, faz a verificação de acordo com as regras das tabelacars de cada régua e salva um DF de verificacao 
    no folder /VerificacaoTabelasCar/.
    """
    for i in dbutils.fs.ls("/Volumes/desafio_kinea/boletagem_cp/files/Reguas/"): #para cada régua de ativo nesse path, vamos passar a régua inicial pelo verificador e salvar o resultado em um CSV
        ativo:str = i.name.split("_")[1].removesuffix(".csv") #pega nome do ativo pelo
        alocacao = pd.read_csv(i.path.removeprefix("dbfs:"))
        #estava apresentando erro falando que a coluna book n existe entao eu vou por um verificador aqui 
        if 'book' in alocacao.columns:
            alocacao = alocacao.drop(columns='book')
        verificador = VerificadorTabelacar()
        resultado_verificacao = verificador.verifica_alocacao(alocacao,ativo)
        resultado_verificacao.to_csv(f"/Volumes/desafio_kinea/boletagem_cp/files/VerificacaoTabelasCar/VERIFICACAO_{ativo}.csv",index=False)


if __name__=='main_':
    ExecutarVerificacoes()