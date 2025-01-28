"""
Script para executar Verificações
"""
from VerificadorTabelacar import  VerificadorTabelacar
from DadosAlocacao import DadosAlocacao
from Otimizacao import otimiza_regua #essa função recebe 2 df como arg
import pandas as pd

def ExecutarVerificacoes():
    """
    Com as réguas iniciais dos ativos de uma dada ordem salvas no volume do desafio /Reguas/, faz a verificação de acordo com as regras das tabelacars de cada régua e salva um DF de verificacao 
    no folder /VerificacaoTabelasCar/.
    """
    verificador = VerificadorTabelacar()
    for i in dbutils.fs.ls("/Volumes/desafio_kinea/boletagem_cp/files/Reguas/"): #para cada régua de ativo nesse path, vamos passar a régua inicial pelo verificador e salvar o resultado em um CSV
        ativo:str = i.name.split("_")[1].removesuffix(".csv") #pega nome do ativo pelo 
        alocacao = pd.read_csv(i.path.removeprefix("dbfs:")).drop(columns='book')
        resultado_verificacao = verificador.verifica_alocacao(alocacao,ativo)
        resultado_verificacao.to_csv(f"/Volumes/desafio_kinea/boletagem_cp/files/VerificacaoTabelasCar/VERIFICACAO_{ativo}.csv",index=False)

def ExecutarOtimizacaoInicial():
    """
    Com as réguas iniciais dos ativos de uma dada ordem salvas no volume do desafio /Reguas/, faz a verificacao de acordo com as tabelascar e depois otimizar de acordo com a regua e restrições e
    salvar as reguas otimizadas no diretório X do volume. Essa função realiza a primeira otimização no ciclo de processa uma ordem
    """

def ExecutarOtimizacaoCiclo():
    """
    Com uma ou mais reguas otimizadas de uma ordem, realiza mais um processo de verificacao e otimizacao caso necessário. As reguas anteriores são lidas do path X (path de reguas otimizadas) do volumes e depois de atualizadas denovo, são salvas nesse mesmo path, substituindo as réguas otimizadas anteriores.
    """


    
if __name__ == '__main__':
    regua = ExecutarVerificacoes()