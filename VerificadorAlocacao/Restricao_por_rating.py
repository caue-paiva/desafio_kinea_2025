# Databricks notebook source
import pandas as pd
import re
from dataclasses import dataclass

def primeiro_numero_e_posicao(string:str)->tuple[int,int]:
    for i,char in enumerate(string):
        if char.isnumeric():
            return int(char), i
    
    return -1,-1

def construir_dict_ratings(lista_ratings:list[str],list_niveis:list[int])->dict:
    dict_ratings = {}
    for rating,nivel in zip(lista_ratings,list_niveis):
        valores_nivel = []
        if " a " in rating: #rating é um range
            if "Aaa" in rating:
                valores_nivel = ["Aaa","Aa2","Aa3"] #Por enquanto vai ficar hardcoded ppq eu n entendi essa parte
            else:
                primeiro_num, index1 = primeiro_numero_e_posicao(rating)
                segundo_num,  index2 = primeiro_numero_e_posicao(rating[index1+1:])

                str_base = rating[:index1]
                valores_nivel = [
                    f"{str_base}{str(x)}" for x in range(primeiro_num,segundo_num+1)
                ]
        else:
            valores_nivel = [rating]
        dict_ratings[nivel] = valores_nivel
    return dict_ratings

def get_ratings_igual_abaixo(rating:str, tabela_car_fundo:str)->list[str]:
    query_df_ratings = f"""SELECT * FROM {tabela_car_fundo} """

    df_ratings = spark.sql(query_df_ratings).sort("Nivel").collect()

    lista_ratings = []
    lista_nivels = []
    for row in df_ratings:
        #print(row["IntervaloRating"],row["Nivel"])
        lista_ratings.append(row["RatingKinea"]) # Trocar para IntervaloRating
        lista_nivels.append(row["Nivel"])
    
    ratings_dict = construir_dict_ratings(lista_ratings,lista_nivels)

    best_level = -1
    for key,val in  sorted(ratings_dict.items(),key= lambda x: x[0]):
        if rating in val: #se o rating esta na lista
            best_level  = key
            break
    if best_level == -1:
        raise RuntimeError("Não foi possível achar nível do rating")
    
    # print(best_level)
    return dict(
        filter(lambda x: x[0] >= best_level,ratings_dict.items()) #essa equação ou inequação é a principal coisa a se mudar caso precise modificar a lógica
    )


# COMMAND ----------

from typing import List
 
# O objetivo dessa query é ditar qual a porcentagem do PL de certo fundo é composto por ativos de crédito privado de até certo rating, de acordo com a lógica das tabelas CAR

def query_fundo_sum_position(ratings:List[str])->pd.DataFrame:
  query_sum_positions_por_fundo = f"""
  WITH pl_total_fundo AS (
  SELECT t1.Codigo, t1.Data, t1.PL
  FROM desafio_kinea.boletagem_cp.cotas as t1
  JOIN (
      SELECT Codigo, MAX(Data) AS MaxData
      FROM desafio_kinea.boletagem_cp.cotas
      GROUP BY Codigo
  ) t2 
  ON t1.Codigo = t2.Codigo AND t1.Data = t2.MaxData
  ORDER BY Data DESC
),
tab_booksoverview AS (
 SELECT
   DISTINCT
   PositionDate,
   Book,
   Product,
   ProductClass,
   TradingDesk,
   Position
 FROM
   desafio_kinea.boletagem_cp.booksoverviewposicao_fechamento
 WHERE
   (LOWER(ProductClass) LIKE '%debenture%' OR
    LOWER(ProductClass) LIKE '%bonds%' OR
    LOWER(ProductClass) LIKE '%cra%' OR
    LOWER(ProductClass) LIKE '%cri%' OR
    LOWER(ProductClass) LIKE '%funds%' OR
    LOWER(ProductClass) LIKE '%letra%' OR
    LOWER(ProductClass) LIKE '%nota%')
   AND (LOWER(Book) LIKE '%ivan%')
   AND TradingDesk IN ('KCP','RFA','KOP', '846', '134', '678','FRA', 'CPI','PAL','ID2','PID','APO','APP','IRF','KAT','PEM','PDA',"KRF","652","389","348","BVP")
),
tab_pl AS (
 SELECT
   DISTINCT
   Data AS PositionDate,
   Codigo AS TradingDesk,
   PL
 FROM
   desafio_kinea.boletagem_cp.cotas
),
tab_fundos AS (
 SELECT
   DISTINCT
   tab_booksoverview.*,
   tab_pl.PL
 FROM
   tab_booksoverview
 LEFT JOIN
   tab_pl
 ON
   tab_pl.PositionDate = tab_booksoverview.PositionDate
   AND tab_pl.TradingDesk = tab_booksoverview.TradingDesk
) --retorna ativos de credito privado 


SELECT tabela_emissor.TradingDesk, PL as pl_total , pl_credito_privado FROM pl_total_fundo
JOIN
(
    SELECT  t1.TradingDesk, SUM(Position) as pl_credito_privado FROM tab_fundos as t1 --soma e acha o total de crédito privado de cada fundo
    JOIN --join na tabela de data mais recente, filtrando a tabela para as combinações de cada fundo - ativo mais recentes
    (
      -- acha a data mais recente para cada combinação fundo e ativo
      SELECT TradingDesk, Product, MAX(PositionDate) AS MaxData from tab_fundos
      GROUP BY TradingDesk, Product
    ) t2
    ON t1.TradingDesk = t2.TradingDesk AND t1.Product = t2.Product AND t1.PositionDate = t2.MaxData
    JOIN --subquery para o rating dos atiivos
    (
      SELECT DISTINCT 
        Emissor, 
        Ativo, 
        FLOOR(DATEDIFF(Vencimento,CURRENT_DATE) / 365) AS ExpiracaoAnos,
        RatingOp,
        RatingGrupo 
      FROM desafio_kinea.boletagem_cp.agendacp
      JOIN desafio_kinea.boletagem_cp.cadastroativo ON TickerOp = Ativo --join para ter a coluna de Vencimento
      JOIN desafio_kinea.boletagem_cp.ratingopatual ON ratingopatual.TickerOp = Ativo--join para ter coluna de rating
      JOIN desafio_kinea.boletagem_cp.ratinggrupoatual ON NomeGrupo = Emissor 
    )
    ON  t1.Product = Ativo
    WHERE RatingOp IN ({','.join(map(repr, ratings))}) --filtra pelo rating
    GROUP BY t1.TradingDesk
) AS tabela_emissor
ON pl_total_fundo.Codigo = tabela_emissor.TradingDesk"""

  return spark.sql(query_sum_positions_por_fundo)

# COMMAND ----------

from DadosAlocacao import DadosAlocacao

dados = DadosAlocacao()
df_pl_total = dados.get_pl_total_fundos()

def verificacao_l_anos(linha_tabela_car:pd.DataFrame,vencimento_em_anos:int)->float | None:
    """
    Dado um linha da tabelacar, verifica se ela tem info sobre porcentagens de ativos pelo ano, e se tiver, retorna o valor em porcentagem que o ano passado como arg. se encaixa.
    Caso a tabela não tenha verificações, retorna None
    """
    tem_col_anos:bool = False
    prev_col:str = ""
    for col in linha_tabela_car.columns:
        if "ano" in col.lower():
            tem_col_anos = True
            ano_coluna:int = int(re.findall(r'\d+', col)[0])
            if ano_coluna == vencimento_em_anos: #exemplo coluna L8_anos e vencimento de 8 anos
                return linha_tabela_car[col].values[0]
            elif ano_coluna > vencimento_em_anos: #exemplo colunas L6_anos, L8_anos e vencimento de 7 anos, retorna L6_anos 
                if prev_col:
                    return linha_tabela_car[prev_col].values[0]
                else: #não tem coluna anterior
                    return None
            prev_col = col
    
    return None #não tem coluna de ano 

def df_com_pl_total_e_por_rating(classe_dados:DadosAlocacao,rating:str)->pd.DataFrame:
    df_pl_total = dados.get_pl_total_fundos()
    df_pl_rating = dados.get_pl_fundo_por_rating(rating)
    df_pl_rating = df_pl_rating.rename({"total_credito":"pl_credito_privado_rating"},axis=1)
    return df_pl_total.merge(df_pl_rating,how="inner",left_on="TradingDesk",right_on="TradingDesk")

def verificacao_emissor_e_l_anos(
    emissor_nome:str,
    fundo:str,
    pl_total_fundo:float,
    ratings_igual_ou_abaixo_emissor:dict,
    vencimento_em_anos:int,
    tabela_car_fundo:pd.DataFrame,
    debug = False
):
    df_pl_por_emissor = dados.get_pl_e_rating_por_emissor() #df do pl de cada emissor num fundo
    df_pl_emissor_l_anos = dados.get_pl_por_emissor_e_vencimento_anos(vencimento_em_anos)

    linha_tabela_car:pd.DataFrame = tabela_car_fundo[tabela_car_fundo["Nivel"] == int(min(ratings_igual_ou_abaixo_emissor.keys()))] #filtra tabelacar pelos ratings do emissor
    
    porcentagem_max_pelo_ano:float | None = verificacao_l_anos(linha_tabela_car,vencimento_em_anos) #porcentagem maximo do PL de um fundo por emissor
    porcentagem_max_pelo_emissor:float = linha_tabela_car["MaxEmissor"].values[0] #porcentagem maximo do pl de um fundo composta por ativos desse emissor com vencimento igual ou maior a L anos
    if porcentagem_max_pelo_ano is None: #a tabela não restringe por ano dos ativos, então a porcentagem que vamos olha é a do emissor (que é equivalente ao de L0 anos, representando nenhuma restrição quanto a data de vencimento)
        porcentagem_max_pelo_ano = porcentagem_max_pelo_emissor


    pl_emissor_no_fundo:float = df_pl_por_emissor[(df_pl_por_emissor["Emissor"] ==  emissor_nome) & (df_pl_por_emissor["TradingDesk"] == fundo)]["pl_emissor"].values[0] #valor liquido que o emissor tem naquele fundo para todos os ativos
    pl_emissor_l_anos_fundo:float = df_pl_emissor_l_anos[ (df_pl_emissor_l_anos["Emissor"] ==  emissor_nome) & (df_pl_emissor_l_anos["TradingDesk"] == fundo)]["pl_emissor"].iloc[0] #valor liquido que o emissor tem no fundo, apenas contando ativos que vencem em L ou mais anos
   
    if debug:
        print(f"Pl total do emissor no fundo: {pl_emissor_no_fundo}, pl do emissor contando apenas ativos com vencimento de {vencimento_em_anos} anos ou mais: {pl_emissor_l_anos_fundo}")
        print(f"porcentagens maximas pelo emissor: {porcentagem_max_pelo_emissor} e pelo ano: {porcentagem_max_pelo_ano}")

    porcentagem_real_pelo_ano:float =  pl_emissor_l_anos_fundo / pl_total_fundo #porcentagem real
    porcentagem_real_pemissor:float =  pl_emissor_no_fundo / pl_total_fundo

    return {
        "diferenca_porcentagem_ano": porcentagem_max_pelo_ano - porcentagem_real_pelo_ano ,
        "diferenca_total_ano": (porcentagem_max_pelo_ano - porcentagem_real_pelo_ano) * pl_total_fundo,
        "diferenca_porcentagem_emissor":  porcentagem_max_pelo_emissor - porcentagem_real_pemissor,
        "diferenca_total_emissor": (porcentagem_max_pelo_emissor - porcentagem_real_pemissor) * pl_total_fundo,
    }


# COMMAND ----------

mapeamento_fundos_tabela_car = {
          'CAR Baixo Risco':            'desafio_kinea.boletagem_cp.tabelacar_baixorisco',
          'CAR Médio Risco':            'desafio_kinea.boletagem_cp.tabelacar_mediorisco', 
          'CAR Fundos Hibridos':        'desafio_kinea.boletagem_cp.tabelacar_hibridos',
          'Dedicado Alto Risco':        'desafio_kinea.boletagem_cp.tabelacar_dedicadoaltorisco',
          'CAR Fundos HY':              'desafio_kinea.boletagem_cp.tabelacar_hy',
          'CAR Fundos Mistos':          'desafio_kinea.boletagem_cp.tabelacar_criinfra',
          'Dedicado CapitalSolutions':  'desafio_kinea.boletagem_cp.tabelacar_capitalsolutions'
}

# COMMAND ----------

"""
O output do código de verifição da tabelacar vai ser essa classe com o dataframe com esse schema
"""

df_resultado_regua = pd.DataFrame(
    columns=[
        "fundo","valor_alocacao_inicial","diferenca_porcentagem_ano","diferenca_total_ano","diferenca_porcentagem_emissor",
        "diferenca_total_emissor","diferenca_porcentagem_pl_privado","diferenca_total_pl_privado", "passou_em_tudo", "passou_max_pl",
        "passou_max_emissor","passou_l_anos"
    ]
)


# COMMAND ----------


# TODO Integrar com o que o João fez 

ativo = 'ENMTA4'

fundo_dist_regua = {
    'fundo': ['RFA', 'APO', 'ID2'],
    'valor': [sum([0.4753, 0.2623, 0.3275]),
              sum([0.1017, 0.3478, 0.1845]),
              sum([0.4230, 0.3899, 0.4879])]
}
df_regua_fundo_valor = pd.DataFrame(fundo_dist_regua)

# dict_fundos_tipoCAR contém um dicionário da forma "codigo_fundo": "Tipo Tabela Car"; 
# Ex: {'RFA': 'CAR Fundos Hibridos', 'APO': 'CAR Fundos Hibridos', 'ID2': 'CAR Fundos Hibridos'}
df_mapa_tabelacar =  dados.get_mapa_tabelacar()

dict_fundos_tipoCAR: dict[str,str] = {} #mapeamento nome fundo para o tipo de tabela car
dict_fundo_tabelaCAR: dict[str,pd.DataFrame] = {} #mapeamento nome fundo para o dataframe da tabelacar correspondente

for fundo in set(fundo_dist_regua["fundo"]): #conjunto de fundos da regua
    tipo_car:str = df_mapa_tabelacar[ df_mapa_tabelacar["Fundo"] == fundo].values[0][1]
    tabela_car:str = mapeamento_fundos_tabela_car[tipo_car]
    dict_fundo_tabelaCAR[fundo] = spark.sql(f"select * from {tabela_car}").toPandas()
    dict_fundos_tipoCAR[fundo] = tipo_car


df_ativos = dados.get_info_rating_ativos() #df com informações sobre cada ativo,ratings e emissores
#Pegar dados sobre o ativo,seus rating, o seu emissor e rating do emissor
df_ativo_filtrado = df_ativos[df_ativos["Ativo"] == ativo]
rating_ativo:str = df_ativo_filtrado["RatingOp"].values[0] 
rating_emissor:str = df_ativo_filtrado["RatingGrupo"].values[0]
emissor_nome:str = df_ativo_filtrado["Emissor"].values[0]
vencimento_anos_ativo:int = int(df_ativo_filtrado["ExpiracaoAnos"].values[0])

for fundo in df_regua_fundo_valor["fundo"]:
    tabela_car_fundo = dict_fundo_tabelaCAR[fundo]
    
    ratings_igual_abaixo:dict = get_ratings_igual_abaixo(df_ativos[df_ativos["Ativo"] == ativo]["RatingOp"].values[0],
                                                    mapeamento_fundos_tabela_car[dict_fundos_tipoCAR[fundo]])
    
    ratings_igual_abaixo_emissor:dict = get_ratings_igual_abaixo(df_ativos[df_ativos["Ativo"] == ativo]["RatingGrupo"].values[0],
                                                    mapeamento_fundos_tabela_car[dict_fundos_tipoCAR[fundo]])
  
    # Linha referente ao rating do ativo específico e a tabela car referente ao fundo
    linha_tabela_car:pd.DataFrame = tabela_car_fundo[tabela_car_fundo["Nivel"] == int(min(ratings_igual_abaixo.keys()))] #df de uma linha
    
    #porcentagem_pelo_ano:float = verificacao_l_anos(linha_tabela_car,vencimento_anos_ativo) #porcentagem maximo do PL de um fundo por emissor
    #display(linha_tabela_car)
    
    # Pega o maior rating da linha da tabela car relacionada ao ativo. Ex: rating_ativo = Baa3, linha = "Baa1 a Baa4" ->
    # Retornará Baa1. Será utilizado para pegar dos CSV's já salvos com a soma do position de todos os ativos abaixo de Baa1.
    # Caso seja apenas Baa3 no campo de rating da linha da tabela car, será pego o CSV relacionado à esse rating + os ativos abaixo 

    # TODO TODO TODO TODO !!!!!Pedir para o Rapha mudar nome da coluna p/ IntervaloRating para Tabela Car "Fundos Hibridos"!!!!!!
    maior_rating_linha_tabela_car = linha_tabela_car["RatingKinea"].values[0].split(" ")[0] 
    fundo_pl_cred_priv_pl_total = df_com_pl_total_e_por_rating(dados,maior_rating_linha_tabela_car) #pega PL de credito privado de um fundo  de um fundo filtrado por esse  rating
    pl_total_fundo:float = fundo_pl_cred_priv_pl_total[fundo_pl_cred_priv_pl_total["TradingDesk"] == fundo]["PL"].values[0]
    
    # Aparentemente a query foi atualizada, mas não rodou o script de atualizar os CSVs. Provavelmente vai funcionar pegar a coluna de pl_credito_privado da variável fundo_pl_cred_priv_pl_total se atualizar. 

    fundo_pl_cred_priv_pl_total["porcentagem_pl"] = (fundo_pl_cred_priv_pl_total["pl_credito_privado_rating"] /
                                                     fundo_pl_cred_priv_pl_total["PL"])
    
    fundo_porcentagem_pl_cred_priv:float = (fundo_pl_cred_priv_pl_total[fundo_pl_cred_priv_pl_total["TradingDesk"] == fundo] 
                            ["porcentagem_pl"].values[0])

    resultado_emissor_e_ano = verificacao_emissor_e_l_anos(
        emissor_nome,fundo,pl_total_fundo,ratings_igual_abaixo_emissor,vencimento_anos_ativo,tabela_car_fundo
    )
    print(resultado_emissor_e_ano)
    
    # pl_emissor_no_fundo:float = df_pl_por_emissor[(df_pl_por_emissor["Emissor"] ==  emissor_nome) & (df_pl_por_emissor["TradingDesk"] == fundo)]["pl_emissor"].values[0] #valor liquido que o emissor tem naquele fundo para todos os ativos

    # Variável fundo_porcentagem_pl_cred_priv poderá fazer a validação relacionada ao maxPL da tabela car da variável tabela_car_fundo
    # Variável pl_emissor_no_fundo poderá fazer a validação relacionada ao maxEmissor na da tabela car da variável tabela_car_fundo
    # TODO: Fazer validação se há as colunas de anos, e fazer a validação deles, caso seja válido. (Não lembro se era para substituir a validação de maxPL ou maxEmissor por essa de anos, ou se é uma validação à parte).
    # TODO: Gerar o output da forma que Sarah e João querem (fundo | excedente) (será em porcentagem? será que não deveriamos estar fazendo por quantidade de cotas excedentes? ou pela quantidade de PL excedente?) 


# COMMAND ----------

!pip install openai==0.28

dbutils.library.restartPython()

import openai

openai.api_type = "azure"
openai.api_base = "https://oai-dk.openai.azure.com/"
openai.api_version = "2023-12-01-preview"
openai.api_key = dbutils.secrets.get('akvdesafiokinea','azure-oai-dk')
prompt = "Prompt de teste"
message_text = [{"role":"system",
                "content":"Você é um sistema de GenAI que será utilizado ajudar usuários a melhorarem códigos de programação."},
               {"role":"user",
                "content":prompt}]
completion = openai.ChatCompletion.create(
engine="gpt35turbo16k",
messages = message_text,
temperature=0,
max_tokens=1200,
top_p=0.95,
frequency_penalty=0,
presence_penalty=0,
stop=None
)
completion.to_dict()['choices'][0]['message']['content']
