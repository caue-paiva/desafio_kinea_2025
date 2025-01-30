import numpy as np
import scipy
import pandas as pd
from VerificadorTabelacar import VerificadorTabelacar


def otimiza_regua(regua_ideal:pd.DataFrame, diferencas:pd.DataFrame)->tuple[pd.DataFrame,float]:
    """
    Dado uma DF régua ideal de alocação de um ativo em vários fundos e um DF diferenças que dita qual a diferença entre a alocação ideal vs as restrições  das tabelasCar (negativo que dizer acima do possível), 
    otimiza a regua ideia de acordo com as diferenças, de forma a ter a melhor alocação possível dentro das regras.
    Args:
        regua_ideal (pd.DataFrame): DF com as alocações ideais de cada fundo
        diferencas (pd.DataFrame): DF com as diferenças entre a alocação ideal e a alocação real, com uma diferença negativa (real ou porcentagem) ditando que a alocação passou do limite de certa verificação da tabelacar
    Return:
        (tuple[pd.DataFrame,float]): tupla com o DF da régua otimizada e o erro da otimização
    """
    #Inicia uma Régua com os valores distribuidos uniformemente entre os fundos
    x0 = np.array([1/len(regua_ideal)] * len(regua_ideal))

    #Calculando Limite Máximo de Cada Fundo
    #limites_maximos =regua_ideal['percentual_alocacao'] + diferencas[['diferenca_porcentagem_ano','diferenca_porcentagem_emissor','diferenca_porcentagem_pl_privado']].min(axis=1)
    limites_maximos =regua_ideal['percentual_alocacao'] + regua_ideal['percentual_alocacao'] * diferencas[['diferenca_porcentagem_ano','diferenca_porcentagem_emissor','diferenca_porcentagem_pl_privado']].min(axis=1)

    #Adicionando Bounds
    bounds = []
    for limite in limites_maximos:
        bounds.append((0,limite))

    #Função Objetivo -> Soma dos Módulos das diferenças entre a Régua Ideal e a Régua Possível
    def objetivo(x, regua_ideal):
        y = np.abs(x -regua_ideal['percentual_alocacao']).sum()
        return y
    
    #Restrição para Limite Máximo
    def limite_maximo(x, i, limite):
        #print(f"Verificando restrição para i={i}: limite={l}, valor atual={x[i]}")
        return limite - x[i]
    
    #Restrição Soma das Alocações Igual a 1
    def soma_1(x):
        print(sum(x))
        return sum(x) - 1

    #Restrição para cada alocação ser maior ou igual a 0
    def alocacao_maiorque_0(x,i): 
        return x[i]
    
    #Lista com Restrições
    constraints = []
    #constraints.append({'type': 'eq', 'fun': lambda x: soma_1(x)})
    for i in range(len(x0)):
        limite = limites_maximos[i]
        #constraints.append({'type': 'ineq', 'fun': lambda x,i=i: alocacao_maiorque_0(x,i)})
        constraints.append({'type':'ineq','fun':lambda x,i=i:limite_maximo(x,i,limites_maximos[i])})

    #Resolver o problema de minimização
    minimizador = scipy.optimize.minimize(
        fun=objetivo,
        x0=x0,
        args=(regua_ideal),
        constraints=constraints,
        bounds= bounds,
        method='SLSQP',
        options={'maxiter': 100000,'disp':True}
    )    

    print(minimizador.success)
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