import numpy as np
import scipy
import pandas as pd
from VerificadorTabelacar import VerificadorTabelacar
def otimiza_regua(regua_ideal:pd.DataFrame, livres:pd.DataFrame)->tuple[pd.DataFrame,float]:
    """
    Dado uma DF régua ideal de alocação de um ativo em vários fundos e um DF diferenças que dita qual a diferença entre a alocação ideal vs as restrições  das tabelasCar (negativo que dizer acima do possível), 
    otimiza a regua ideia de acordo com as diferenças, de forma a ter a melhor alocação possível dentro das regras.
    Args:
        regua_ideal (pd.DataFrame): DF com as alocações ideais de cada fundo
        livres (pd.DataFrame): DF com o máximo possível que uma alocação poderia ter em relação a ordem
    Return:
        (tuple[pd.DataFrame,float]): tupla com o DF da régua otimizada e o erro da otimização
    """
    #Inicia uma Régua com os valores distribuidos uniformemente entre os fundos
    x0 = np.array([1/len(regua_ideal)] * len(regua_ideal))

    #Seleciona o Máximo que a alocação pode alcançar sem quebrar nenhuma regra
    limites_maximos = livres[['livre_max_pl','livre_emissor','livre_anos']].min(axis=1) 
    #Selecionamos o minimo pois cada coluna contém quantos % da ordem poderia ser alocado sem quebrar uma restrição

    #Adicionando Bounds
    bounds = []
    for limite in limites_maximos:
        bounds.append((0,limite))

    #Função Objetivo -> Soma dos Módulos das diferenças entre a Régua Ideal e a Régua Possível
    def objetivo(x, regua_ideal):
        y = np.abs(x -regua_ideal['percentual_alocacao']).sum()
        return y
    
    #Restrição Soma das Alocações Igual a 1
    def soma_1(x):
        return sum(x) - 1
    
    #Lista com Restrições
    constraints = []
    constraints.append({'type': 'eq', 'fun': lambda x: soma_1(x)})

    #Resolver o problema de minimização
    minimizador = scipy.optimize.minimize(
        fun=objetivo,
        x0=x0,
        args=(regua_ideal),
        constraints=constraints,
        bounds= bounds,
        method='SLSQP',
        options={'maxiter': 100000,'disp':False}
    )    

    erro = minimizador.fun
    regua_otimizada = minimizador.x

    #Salvar Regua Otimizada e Erro
    regua_ideal["alocacao_otimizada"] = regua_otimizada

    return regua_ideal,erro

def otimiza_ativo(verificador:VerificadorTabelacar, ativo:str)->tuple[pd.DataFrame,float]:
    """
    Dado um ativo com sua regua já calculada e salva (em .csv) no volume de armazenamento do desafio, no Path /Reguas/ e uma classe de verificacao, otimiza a regua de acordo com as diferenças entre 
    a alocação ideal e as restrições impostas pelo verificador (as das tabelascar).

    Args:
        verificador (VerificadorTabelacar): Classe de verificação
        ativo (str): Nome do ativo
    Returns:
        (pd.DataFrame,float): tupla com o DF da régua otimizada (com novos valores na coluna "alocacao_otimizada") e o erro da otimização
    """
    df_regua = pd.read_csv(f"/Volumes/desafio_kinea/boletagem_cp/files/Reguas/Regua_{ativo}.csv")
    df_diferencas = verificador.verifica_alocacao(df_regua,ativo)
    regua_ideal, erro = otimiza_regua(df_regua,df_diferencas)
    return regua_ideal,erro


if __name__ == "__main__":
    ativo = 'CPGT18'
    verificador = VerificadorTabelacar()
    df_otimizado,erro = otimiza_ativo(verificador,ativo)
    print(erro)
    display(df_otimizado)