import pandas as pd
from VerificadorTabelacar import VerificadorTabelacar
from Otimizacao import otimiza_regua

def ExecutarOtimizacaoInicial():
    """
    Com as réguas iniciais dos ativos de uma dada ordem salvas no volume do desafio /Reguas/, faz a verificacao de acordo com as tabelascar e depois otimizar de acordo com a regua e restrições e
    salvar as reguas otimizadas no diretório X do volume. Essa função realiza a primeira otimização no ciclo de processa uma ordem
    """
    for i in dbutils.fs.ls("/Volumes/desafio_kinea/boletagem_cp/files/Reguas/"): #para cada regua de ativo nesse path
        ativo:str = i.name.split("_")[1].removesuffix(".csv")
        alocacao = pd.read_csv(i.path.removeprefix("dbfs:"))
        verificador = VerificadorTabelacar()
        diferencas = verificador.verifica_alocacao(alocacao,ativo)
        resultado_otimizado = otimiza_regua(alocacao,diferencas)
        df_otimizado =resultado_otimizado[0] 
        df_otimizado.to_csv(f"/Volumes/desafio_kinea/boletagem_cp/files/ReguasOtimizadas/REGUA_OTIMIZADA_{ativo}.csv",index=False)

def ExecutarOtimizacaoCiclo():
    """
    Com uma ou mais reguas otimizadas de uma ordem, realiza mais um processo de verificacao e otimizacao caso necessário. As reguas anteriores são lidas do path X (path de reguas otimizadas) do volumes e depois de atualizadas denovo, são salvas nesse mesmo path, substituindo as réguas otimizadas anteriores.
    """
    for i in dbutils.fs.ls("/Volumes/desafio_kinea/boletagem_cp/files/Reguas/"):
        ativo: str = i.name.split("_")[1].removesuffix(".csv")
        alocacao_otimizada = pd.read_csv(i.path.removeprefix("dbfs:")).drop(columns='book')

        verificador = VerificadorTabelacar()
        resultado_verificacao = verificador.verifica_alocacao(alocacao_otimizada,ativo)
        resultado_otimizado = otimiza_regua(alocacao_otimizada, resultado_verificacao)  
        #salva a regua otimizada novamente, substituindo a anterior
        df_otimizado = resultado_otimizado[0]
        df_otimizado.to_csv(f"/Volumes/desafio_kinea/boletagem_cp/files/Reguas/REGUA_OTIMIZADA_{ativo}.csv",index=False)
if __name__ == "__main__":
    ExecutarOtimizacaoInicial()