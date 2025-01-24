import numpy as np
import scipy
import pandas as pd

#Pegar inputs
regua_ideal = ''
diferencas = ''

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