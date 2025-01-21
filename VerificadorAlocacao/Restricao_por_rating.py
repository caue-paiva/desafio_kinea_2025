# Databricks notebook source
import pandas as pd

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

mapeamento_fundos_tabela_car = {
          'CAR Baixo Risco':            'desafio_kinea.boletagem_cp.tabelacar_baixorisco',
          'CAR Médio Risco':            'desafio_kinea.boletagem_cp.tabelacar_mediorisco', 
          'CAR Fundos Hibridos':        'desafio_kinea.boletagem_cp.tabelacar_hibridos',
          'Dedicado Alto Risco':        'desafio_kinea.boletagem_cp.tabelacar_dedicadoaltorisco',
          'CAR Fundos HY':              'desafio_kinea.boletagem_cp.tabelacar_hy',
          'CAR Fundos Mistos':          'desafio_kinea.boletagem_cp.tabelacar_criinfra',
          'Dedicado CapitalSolutions':  'desafio_kinea.boletagem_cp.tabelacar_capitalsolutions'
}

# TODO: Generalizar para pegar da tabela desafio_kinea.boletagem_cp.fundostipocar
# quando recebermos a régua com todos os fundos | alocacao
# Por enquanto, somente utilizando uma lista de fundos para teste

# FUNDO 389 não tem na tabela dos fundos que apareceram em desafio_kinea.boletagem_cp.fundostipocar
# lista_fundos = ["KAT", "ID2", "FRA", "APP", "PAL", "652", "PDA", "APO", "PID", "678", "KRF", "KCP", "BVP", "RFA", "KOP", "134", "CPI", "846", "IRF"]



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

#Pegar a régua que foi dada pelo João

# df de [Fundo | alocacao], código do fundo
# ["KAT", "ID2", "FRA", "APP", "PAL", "652", "PDA", "APO", "PID", "678", "KRF", "KCP", "BVP", "RFA", "KOP", "134", "CPI", "846", "IRF"]

# TODO Comentar e melhorar código

# TODO Integrar com as tabelas CSV implementadas

# TODO Integrar com o que o João fez 
ativo = 'ENMTA4'

fundo_dist_regua = {
    'fundo': ['RFA', 'APO', 'ID2'],
    'valor': [sum([0.4753, 0.2623, 0.3275]),
              sum([0.1017, 0.3478, 0.1845]),
              sum([0.4230, 0.3899, 0.4879])]
}
df_regua_fundo_valor = pd.DataFrame(fundo_dist_regua)

#Buscar qual é o rating do fundo | RatingOp

caminho_base = "../ScriptsSQL"
caminho = caminho_base +'/' + 'tabelascar_info_ativos' + '.sql'
with open(caminho, 'r') as f:
    query = f.read()
df_ativos = spark.sql(query).toPandas()

rating_ativo = df_ativos[df_ativos["Ativo"] == ativo]["RatingOp"].values[0]
rating_emissor = df_ativos[df_ativos["Ativo"] == ativo]["Emissor"].values[0]


dict_fundos_tipoCAR = {}
for fundo in fundo_dist_regua["fundo"]:
    dict_fundos_tipoCAR[fundo] = spark.sql(f"SELECT DISTINCT TipoCAR FROM desafio_kinea.boletagem_cp.fundostipocar WHERE Fundo = '{fundo}'").collect()[0][0]

for fundo in df_regua_fundo_valor["fundo"]:
    tabela_car_fundo = spark.sql(f"select * from {mapeamento_fundos_tabela_car[dict_fundos_tipoCAR[fundo]]}").toPandas()
    
    ratings_igual_abaixo = get_ratings_igual_abaixo(df_ativos[df_ativos["Ativo"] == ativo]["RatingOp"].values[0],
                                                    mapeamento_fundos_tabela_car[dict_fundos_tipoCAR[fundo]])
    
    print(ratings_igual_abaixo)
    
    ratings = []
    for key,val in ratings_igual_abaixo.items():
        for rating in val:
            ratings.append(rating)
            
    # Linha referente ao rating do ativo específico e a tabela car referente ao fundo
    linha_tabela_car = tabela_car_fundo[tabela_car_fundo["Nivel"] == int(min(ratings_igual_abaixo.keys()))]

    display(linha_tabela_car)

    fundo_sum_position_pl_total = query_fundo_sum_position(ratings).toPandas()

    display(fundo_sum_position_pl_total)

    fundo_sum_position_pl_total["porcentagem_pl"] = fundo_sum_position_pl_total["pl_credito_privado"] / fundo_sum_position_pl_total["pl_total"]

    fundo_porcentagem_pl = fundo_sum_position_pl_total[fundo_sum_position_pl_total["TradingDesk"] == fundo]["porcentagem_pl"].values[0]


    # Verificação como stub
    # if fundo_porcentagem_pl > tabela_car_max_pl:
    #     # TODO se entrar, deve fazer a construção do DF de realocação.
    #     print("entrou aqui")
    # else:
    #     # Printando a porcetagem à titulo de curiosidade
    #     print(fundo, fundo_porcentagem_pl)
    #     print(fundo, tabela_car_max_pl)
    #     print("eh isto aí")


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
