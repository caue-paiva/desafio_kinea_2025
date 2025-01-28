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
    #Pegar inputs
    # regua_ideal = ''
    #diferencas = ''

    #Inicia uma Régua com os valores distribuidos uniformemente entre os fundos
    x0 = np.array([1/len(regua_ideal)] * len(regua_ideal))

    #Função Objetivo -> Soma dos Módulos das diferenças entre a Régua Ideal e a Régua Possível
    def objetivo(x, regua_ideal):
        return np.power(x - regua_ideal['percentual_alocacao'], 2).sum()

    #Contraints Iniciais
    constraints=[
    {'type': 'eq', 'fun': lambda x: sum(x) - 1} #A soma dos valores da régua tem que ser igual a um
    ]
    for i in range(len(x0)):
        constraints.append({'type': 'ineq', 'fun': lambda x: x[i]}) #Todos os valores de x tem que ser maiores que 0

    #Tratar Dataframe de Diferenças

    #Transformar Diferenças em Constraints
    limites = {}
    diferencas = diferencas.reset_index(drop=True)
    colunas_valores = diferencas.columns.contains('diferenca')


    for index,row in diferencas.iterrows():
        limite_fundo = []
        for col in ['diferenca_total_ano', 'diferenca_total_emissor', 'diferenca_total_pl_privado']:     
            limite = row['valor_alocacao_inicial']+ row[col]
            constraints.append({'type': 'ineq', 'fun': lambda x,i = index,l = limite: l-x[i]})
            limite_fundo.append(limite)
        limites[row['fundo']] = limite_fundo

    #Resolver o problema de minimização
    minimizador = scipy.optimize.minimize(
        fun=objetivo,
        x0=x0,
        args=(regua_ideal),
        constraints=constraints,
        method='SLSQP',
        options={'disp':False}
    )    
    erro = minimizador.fun
    regua_otimizada = minimizador.x

    #Salvar Regua Otimizada e Erro

    return regua_otimizada,erro


if __name__ == "__main__":
    ativo = 'CPGT18'
    verificador = VerificadorTabelacar()
    df_regua = pd.read_csv(f"/Volumes/desafio_kinea/boletagem_cp/files/Reguas/Regua_{ativo}.csv")
    display(df_regua)
    df_diferencas = verificador.verifica_alocacao(df_regua,ativo)
    display(df_diferencas)
  
    #regua_otimizada,erro = otimiza_regua(df_regua,df_diferencas)
    #print(erro)
    #display(regua_otimizada)
 