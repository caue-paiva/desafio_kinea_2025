# Databricks notebook source
# MAGIC %md
# MAGIC ## [Link para documento overleaf](https://www.overleaf.com/project/677fe7fd4bf7cc5092992e57) 

# COMMAND ----------

# DBTITLE 1,Importando Bibliotecas
#Bibliotecas
import pandas as pd
from typing import List,Callable
import matplotlib.pyplot as plt
import seaborn as sns
import time


# COMMAND ----------

# DBTITLE 1,Funções Intermédiarias
#Funções Intermédiarias da Função Principal
def query(arquivo:str) -> pd.DataFrame:
    caminho_base = "/Workspace/Users/joaopedroalexandrino6@hotmail.com/desafio_kinea_2025/ScriptsSQL"
    caminho = caminho_base +'/' + arquivo + '.sql'
    with open(caminho, 'r') as f:
        query = f.read()
    df = spark.sql(query).toPandas()
    return df

def extrair_informacoes() -> List[pd.DataFrame]:
    '''
    Objetivo:
        Extrair informações necessárias para o Cálculo da Régua
    Inputs:
        None
    Output:
        0. inf_fundos: DataFrame com Patrimônio Líquido, Range Mínimo e Máximo de Crédito para cada fundo ['fundo','PL','l_min','l_max','v_min','v_max']
        1. peso_book_fundos: DataFrame com Percentual de Alocação de cada Book (Esse perccentual é referente a parte disponivel para crédito) para cada fundo ['fundo','book_macro','peso_book_macro']
        2. credito_aportado: DataFrame com valor de crédito alocado em cada book em cada fundo ['fundo','book','produto',alocado']
        3. restricoes_book_micro: DataFrame com as restrições book micro [book','fundo','flag']
        4. restricoes_fundo_restrito: Dataframe com restrições fundo restrito ['ativo',fundo','flag']
        5. ativos_books: DataFrame com ativos e seus books ['ativo','book_micro'] (Pode ser que não tenhamos todos cadastrados)
    '''
    #Tabela Base
    tabela_base = query("verificacao_range_e_book")
    tabela_base_aportado = query("credito_aportado")


    #Filtrando inf_fundos ['fundo','PL','l_min','l_max','v_min','v_max']
    inf_fundos = tabela_base[['fundo','PL','alocacao_min_porcen','alocacao_max_porcen','alocacao_min','alocacao_max']].drop_duplicates('fundo').rename(columns={'alocacao_min':'v_min','alocacao_max':'v_max','alocacao_min_porcen':'l_min','alocacao_max_porcen':'l_max'})
    
    #Filtrando peso_book_fundos ['fundo','book_macro','peso']
    peso_book_fundos = tabela_base[['fundo','peso_book','book_macro']].drop_duplicates(['fundo','book_macro']).rename(columns={'peso_book':'peso'})

    #Filtrando Crédito Aportado ['fundo','ativo',alocado']
    credito_aportado = tabela_base_aportado.rename(columns={'TradingDesk':'fundo','Product':'ativo','Position':'alocado'}).drop(columns=["PositionDate"])

    #Filtrando restricoes_book_micro ['fundo','book_micro','flag']
    restricoes_book_micro = tabela_base[['fundo','book_micro','flag']].drop_duplicates(['fundo','book_micro'])

    #Filtrando restricoes_fundo_restrito ['ativo','fundo_restrito']
    restricoes_fundo_restrito = tabela_base[['ativo','fundo_restrito']].drop_duplicates(['ativo']) #Procurar Entender por que nessa query tem 303 e direto na tabela 305

    #Filtrando ativos_books ['ativo',book_micro']
    ativos_books = tabela_base[['ativo','book_micro']].drop_duplicates(['ativo'])

    return [inf_fundos,peso_book_fundos,credito_aportado,restricoes_book_micro,restricoes_fundo_restrito,ativos_books]

def calculo_regua_macro(inf_fundos: pd.DataFrame, peso_books_fundos:pd.DataFrame,credito_total:float) -> pd.DataFrame:
    '''
    Objetivo:
        Cálculo da Régua
    Inputs:
        inf_fundos: DataFrame com Patrimônio Líquido, Range Mínimo e Máximo de Crédito para cada fundo ['fundo','PL','l_min','l_max']
        peso_books_fundos: DataFrame com Percentual de Alocação de cada Book (Esse perccentual é referente a parte disponivel para crédito) para cada fundo ['fundo','book','peso']
    Output:
        regua: DataFrame com as informações da régua que contém as alocações ideais ['fundo','book','percentual_alocacao']
    '''

    #Funções Auxiliares
    def percentual_alocacao_range_total(credito_total:float,inf_fundos: pd.DataFrame) -> float:
        return (credito_total - inf_fundos['v_min'].sum())/ (inf_fundos['v_max'].sum() - inf_fundos['v_min'].sum())
    
    def percentual_credito_relativo_pl(percentual_alocacao_range_total:float,inf_fundo: pd.Series) -> dict:
        return inf_fundo['l_min'] + percentual_alocacao_range_total * (inf_fundo['l_max'] - inf_fundo['l_min'])
    
    def percentual_book_relativo_pl(percentual_credito_relativo_pl:float,peso_book_fundo: float) -> float:
        return percentual_credito_relativo_pl * peso_book_fundo
    
    def valor_book_relativo_pl(percentual_book_relativo_pl:float,pl:float) -> float:
        return pl *percentual_book_relativo_pl

    #Cálculo da Régua
    percentual_alocacao_range_total = percentual_alocacao_range_total(credito_total,inf_fundos)
   
    percentuais_credito_relativo_pl = {}
    for index,row in inf_fundos.iterrows():
        percentuais_credito_relativo_pl[row['fundo']] = percentual_credito_relativo_pl(percentual_alocacao_range_total,row)

    percentuais_books_relativo_pl = pd.DataFrame(columns=['fundo','book','percentual'])
    for fundo,percentual_credito_relativo_pl in percentuais_credito_relativo_pl.items():
        for index,row in peso_books_fundos[peso_books_fundos['fundo'] == fundo].iterrows():
            percentuais_books_relativo_pl.loc[len(percentuais_books_relativo_pl)] = [fundo,row['book_macro'],percentual_book_relativo_pl(percentual_credito_relativo_pl,row['peso'])]

    
    valores_books_relativos_pl = pd.DataFrame(columns=['fundo','book','valor'])
    for index,row in percentuais_books_relativo_pl.iterrows():
        valores_books_relativos_pl.loc[len(valores_books_relativos_pl)] = [row['fundo'],row['book'],valor_book_relativo_pl(row['percentual'],inf_fundos[inf_fundos['fundo'] == row['fundo']]['PL'].values[0])]
   
    regua = pd.DataFrame(columns=['fundo','book','percentual_alocacao'])
    books = valores_books_relativos_pl['book'].unique()
    fundos = valores_books_relativos_pl['fundo'].unique()
    somas_books = {}
    for book in books:
        somas_books[book] = valores_books_relativos_pl[valores_books_relativos_pl['book'] == book]['valor'].sum()
    for fundo in fundos:
        for index,row in valores_books_relativos_pl[valores_books_relativos_pl['fundo'] == fundo].iterrows():
            regua.loc[len(regua)] = [fundo,row['book'],row['valor']/somas_books[row['book']]]

    return regua

def encontrar_book_macro(book_micro:str) -> str:
    if book_micro.split('_')[0] == "HG":
        book_macro = 'HG'
    elif book_micro.split('_')[0] == "HY":
        book_macro = 'HY'
    elif book_micro.split('_')[0] == "MY":
        book_macro = 'MY'
    elif book_micro.split('_')[0] == "Debenture":
        if book_micro.split('_')[3] == "HG":
            book_macro = "Debenture_Fechada_HG"
        else:
             book_macro = "Debenture_Fechada_HY"
    elif book_micro.split('_')[0] == "Estruturado":
        if book_micro.split('_')[1] == "HG":
            book_macro = "Estruturado_HG"
        else:
             book_macro = "Estruturado_HY"
    else:
        book_macro = "OFFSHORE"
    return book_macro

def verificar_restricoes(ativo:str,book_ativo:str,regua_macro:pd.DataFrame,restricoes_book_micro:pd.DataFrame,restricoes_fundo_restrito:pd.DataFrame) -> dict:
    
    restricoes_book_micro = restricoes_book_micro[restricoes_book_micro['book_micro'] == book_ativo]
    restricoes_book_micro = restricoes_book_micro.merge(regua_macro,on='fundo')
    fundo_restrito = restricoes_fundo_restrito[restricoes_fundo_restrito['ativo'] == ativo]['fundo_restrito'].values[0]

    restricoes = regua_macro[regua_macro['fundo'] == fundo_restrito]
    restricoes = pd.concat([restricoes,restricoes_book_micro[restricoes_book_micro['flag'] == False]], axis=0).drop(columns=['book','book_micro','flag'])

    return restricoes
    
def redistribuir(regua_macro:pd.DataFrame,restritos:pd.DataFrame) -> pd.DataFrame:
    fundos_nao_restritos = regua_macro[regua_macro['fundo'].isin(restritos['fundo'].unique()) == False]
    excedente_distribuido = (fundos_nao_restritos['percentual_alocacao']/fundos_nao_restritos['percentual_alocacao'].sum()) *restritos['percentual_alocacao'].sum()
    regua_macro['percentual_alocacao'] = fundos_nao_restritos['percentual_alocacao'] + excedente_distribuido
    return regua_macro



# COMMAND ----------

#Extraindo Informações Necessárias
dataframes = extrair_informacoes()

# COMMAND ----------

# DBTITLE 1,Função Principal
#Cálculo Régua Macro
def solucao(ativo:str,checagens: List[Callable],ordens: pd.DataFrame,informacoes: List[pd.DataFrame]) -> pd.DataFrame:
    '''
    Função principal que recebe como input:
    1. checagens: Lista de funções geradas pelo ChatGPT
    2. ordens: DataFrame ['Ticker','Amount','Price'] representando uma grupo de ordens a serem boletadas
    e retorna:
    1. ordens_final: DatFrame ['Ticker','Amount','Price','Fundo'] representando quanto irá para cada fundo
    '''
    #Essas  etapas são para 1 ordem -> 1 linha do dataframe ordens

    #Extrair dataframes necessários
    inf_fundos = dataframes[0]
    peso_books = dataframes[1]
    credito_aportado = dataframes[2]
    restricoes = dataframes[3:5]
    book_ativos = dataframes[5]   
   
    #Qual o book referente ao ativo da ordem
    book_ativo = book_ativos[book_ativos['ativo'] == ativo]['book_micro'].values[0]
    book_macro = encontrar_book_macro(book_ativo)

    #Calcular a Régua Book Macro 
    regua_macro = calculo_regua_macro(dataframes[0],dataframes[1],credito_aportado['alocado'].sum())
   
    #Filtrar Régua pelo Book do Ativo
    regua_macro = regua_macro[regua_macro['book'] == book_macro]
    
    #Aplicar Restrição de book micro e fundo restrito
    alocacoes_restritos= verificar_restricoes(ativo,book_ativo,regua_macro,restricoes[0],restricoes[1])
   
    #Redistribuir 
    regua = redistribuir(regua_macro,alocacoes_restritos)
    regua = regua[regua['percentual_alocacao'] != 0].dropna()

    #Retornar Regua
    return regua
   
teste = solucao('INDIGO FIAGRO DCA EMISSAO 1 SERIE 1 SENIOR',[],pd.DataFrame(),dataframes)
print(teste)

# COMMAND ----------

# DBTITLE 1,Testes Cálculo Régua
#Teste Cálculo Régua - Exemplo feito pelo Ali na Reunião do dia 09/01/2025 (https://drive.google.com/file/d/1O-bVrF1At0xZNQIGmIOQ1Oi7YiSkGD0u/view?usp=sharing)
#Apenas um teste não precisa rodas
''''credito_total = 40
teste_inf_fundos = pd.DataFrame({
        'fundo':['RFA','APO','ID2'],
        'PL':[100,50,70],
        'l_min':[0.1,0.1,0.1],
        'l_max':[0.2,0.2,0.4]
})
teste_books_fundos  = pd.DataFrame({
        'fundo':['RFA','RFA','RFA','APO','APO','APO','ID2','ID2','ID2'],
        'book':['HG','MY','HY','HG','MY','HY','HG','MY','HY'],
        'peso_book':[0.53778,0.1634,0.29882,0.23006,0.433212,0.336729,0.41028,0.20813,0.38159]
})
resposta_nossa = calculo_regua(teste_inf_fundos,teste_books_fundos,credito_total)
resposta_ali = pd.DataFrame({
        'fundo':['RFA','RFA','RFA','APO','APO','APO','ID2','ID2','ID2'],
        'book':['HG','MY','HY','HG','MY','HY','HG','MY','HY'],
        'dist_regua':[0.4753,0.2623,0.3275,0.1017,0.3478,0.1845,0.4230,0.3899,0.4879]
        
})
print(resposta_nossa['percentual_alocacao'])
print(resposta_ali['dist_regua'])''''