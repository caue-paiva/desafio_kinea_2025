import pandas as pd
from VerificadorTabelacar import VerificadorTabelacar
from Otimizacao import otimiza_regua

def conta_alocacoes_falhas(diferenca_verificador:pd.DataFrame)->int:
    cols_flag_verificacao = ["passou_max_emissor","passou_l_anos","passou_max_pl"]
    false_cnt = 0
    for col in cols_flag_verificacao:
        false_cnt += (diferenca_verificador[col] == False).sum() #soma as entradas que são falsas (Falsa == False => True e True = 1)
    
    return false_cnt

def loop_otimizacao(
    nome_ativo:str,
    regua_alocacao:pd.DataFrame,
    verificador:VerificadorTabelacar, 
    logging = False,
    tentativas_max = -1
)->pd.DataFrame:
    """
    Faz um loop de otimização de uma régua, por tentativas_max vezes (por padrão INF vezes), passando ela pela verificação das tabelascar e caso ela não passe, tenta otimizar a régua até que passe.

    Args:
        nome_ativo (str): Nome do ativo que será otimizado
        regua_alocacao (pd.DataFrame): Régua inicial do ativo
        verificador (VerificadorTabelacar): Instância da classe do Verificador das tabelascar
        logging (bool, optional): Se True, faz print do resultado das tentativas de otimização. Por padrão, é False.
        tentativas_max (int, optional): Número máximo de tentativas de otimização. Por padrão, é -1, que significa que a otimização é infinita. 

    Return:
        pd.DataFrame: 
        Se tentativas_max = -1 (loop INF): É a Régua que passou em todos os casos da verificação das tabelascar
        ou 
        Se tentativas_max != -1: É a melhor Régua obtida após as tentativas de otimizar (menor número de falhas/falses no df de verificação)
    """
    tentativa = 1
    min_num_falhas = float("inf")
    min_dif = None
    melhor_regua = regua_alocacao.copy()
    num_falhas_inicial = None
    
    while tentativas_max == -1 or tentativa <= tentativas_max: #loop até a regua ser valida ou até o max de iterações, caso em que a melhor régua é retornada
        diferencas: pd.DataFrame = verificador.verifica_alocacao(regua_alocacao,nome_ativo) #verifica diferença
        num_falhas = conta_alocacoes_falhas(diferencas)
        if num_falhas_inicial is None:
            num_falhas_inicial = num_falhas
        
        if num_falhas == 0:
            melhor_regua = regua_alocacao
            min_num_falhas = 0
            break
        elif num_falhas < min_num_falhas: #guarda regua com menor erro
            #print("menor num de falhas: ",num_falhas)
            min_num_falhas = num_falhas
            min_dif = diferencas
            melhor_regua["percentual_alocacao"] = regua_alocacao["percentual_alocacao"]

        resultado_otimizado: tuple = otimiza_regua(regua_alocacao,diferencas) #otimiza regua para contar com a diferença da verificacao
        df_otimizado = resultado_otimizado[0] #resultados da otimização
        erro:float = resultado_otimizado[1]
        
        regua_alocacao["percentual_alocacao"] = df_otimizado["alocacao_otimizada"]  #df agora é o df otimizado
        tentativa += 1
        if tentativas_max > 0 and tentativa > tentativas_max:
            print(f"Não foi possível completamente otimizar a regua da ordem {nome_ativo} após {tentativas_max} tentativas")
            break
    
    if logging:
        print(f"Régua inicial do ativo {nome_ativo}, com {melhor_regua.shape[0]} fundos,  tinha {num_falhas_inicial} falhas de alocação de acordo com a verificão da tabela car, agora tem {min_num_falhas} falhas depois de {tentativa} iterações")
    return melhor_regua

def ExecutarOtimizacaoCiclo(logging=False,max_iteracoes_por_ativo:int=-1):
    """
    Com as réguas iniciais dos ativos de uma dada ordem salvas no volume do desafio /Reguas/, faz a verificacao de acordo com as tabelascar e depois otimizar de acordo com a regua e restrições e
    salvar as reguas otimizadas no diretório X do volume. Essa função realiza a primeira otimização no ciclo de processa uma ordem.

    Args:
        logging (bool, optional): Se True, faz print do resultado das tentativas de otimização. Por padrão, é False.
        max_iteracoes_por_ativo (int, optional): Número máximo de tentativas de otimização por ativo. Por padrão, é -1, que significa que a otimização é infinita.

    Returns:
        (None): Salva os arquivos em /Volumes/desafio_kinea/boletagem_cp/files/ReguasOtimizadas/
    """
    verificador = VerificadorTabelacar()
    for i in dbutils.fs.ls("/Volumes/desafio_kinea/boletagem_cp/files/Reguas/"): #para cada regua de ativo nesse path
        ativo:str = i.name.split("_")[1].removesuffix(".csv")
        alocacao = pd.read_csv(i.path.removeprefix("dbfs:"))
        df_otimizado = loop_otimizacao(ativo,alocacao, verificador, logging, max_iteracoes_por_ativo) #otimiza a régua até passar em todas as verificações ou pega a melhor régua após max_iteracoes_por_ativo do processo de otimização

        if logging:
            print(f"Terminou o Loop de otimizar o ativo {ativo}")
        df_otimizado.to_csv(f"/Volumes/desafio_kinea/boletagem_cp/files/ReguasOtimizadas/REGUA_OTIMIZADA_{ativo}.csv",index=False)

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

if __name__ == "__main__":
    ExecutarOtimizacaoCiclo(True,10)