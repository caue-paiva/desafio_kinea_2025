# Databricks notebook source
# MAGIC %sql
# MAGIC SELECT * FROM desafio_kinea.boletagem_cp.cotas
# MAGIC SORT BY Data DESC

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC SELECT t1.Codigo,t1.Data,t1.PL
# MAGIC FROM desafio_kinea.boletagem_cp.cotas as t1
# MAGIC JOIN (
# MAGIC     SELECT Codigo, MAX(Data) AS MaxData
# MAGIC     FROM desafio_kinea.boletagem_cp.cotas
# MAGIC     GROUP BY Codigo
# MAGIC ) t2 
# MAGIC ON t1.Codigo = t2.Codigo AND t1.Data = t2.MaxData
# MAGIC ORDER BY Data DESC;
# MAGIC
# MAGIC
# MAGIC

# COMMAND ----------


from pyspark.sql import DataFrame
from typing import Callable
"""
pegar património liquido de um fundo
"""


def df_pl_atualizado()->DataFrame:
        """
        Retorna um Dataframe com as colunas Código (do fundo), Data e PL do fundo mais atualizado.
        """
        return spark.sql("""
            SELECT t1.Codigo,t1.Data,t1.PL
            FROM desafio_kinea.boletagem_cp.cotas as t1
            JOIN (
                SELECT Codigo, MAX(Data) AS MaxData
                FROM desafio_kinea.boletagem_cp.cotas
                GROUP BY Codigo
            ) t2 
            ON t1.Codigo = t2.Codigo AND t1.Data = t2.MaxData
            ORDER BY Data DESC;
        """)

def get_pl_fundo(codigo_fundo:str,dataframe_pl:DataFrame)->float:
    return float(
        dataframe_pl.filter(dataframe_pl["Codigo"] == codigo_fundo).first()["PL"]
    )
    



df = df_pl_atualizado()
df.show()

get_pl_fundo("KP3", df)


# COMMAND ----------

from dataclasses import dataclass
"""
Modelar uma ordem de ativo como uma dataclass
"""

@dataclass
class OrdemAtivo:
    """
    Representa uma ordem de alocação de ativos para um fundo
    """
    nome_ativo:str
    amount:int
    venda:bool
    preco:float
    fundo:str

#dataset sintético para teste
ordens_ativos = [ 
    OrdemAtivo(nome_ativo="AAPL", amount=50, venda=False, preco=145.0, fundo="Fundo A"),
    OrdemAtivo(nome_ativo="TSLA", amount=20, venda=True, preco=120.5, fundo="Fundo B"),
    OrdemAtivo(nome_ativo="GOOGL", amount=15, venda=False, preco=2800.0, fundo="Fundo C"),
    OrdemAtivo(nome_ativo="AMZN", amount=10, venda=True, preco=3300.0, fundo="Fundo A"),
    OrdemAtivo(nome_ativo="META", amount=30, venda=False, preco=210.3, fundo="Fundo D"),
    OrdemAtivo(nome_ativo="NFLX", amount=25, venda=True, preco=600.0, fundo="Fundo B"),
    OrdemAtivo(nome_ativo="MSFT", amount=40, venda=False, preco=299.9, fundo="Fundo C"),
    OrdemAtivo(nome_ativo="NVDA", amount=35, venda=True, preco=700.4, fundo="Fundo D"),
    OrdemAtivo(nome_ativo="INTC", amount=45, venda=False, preco=56.7, fundo="Fundo A"),
    OrdemAtivo(nome_ativo="AMD", amount=60, venda=True, preco=120.2, fundo="Fundo B")
]


# COMMAND ----------

"""
Retorna o book que um ativo pertence
"""


df_books = spark.sql("""
                     SELECT * FROM desafio_kinea.boletagem_cp.book_ativos
                     """)
#df_books.show()

def get_books_do_ativo(ativo:str,df_books:DataFrame)->list[str]:
   """
   Retorna uma lista de books do ativo
   """
   return [ row["book"] for row in
        df_books.filter(df_books["ativo"] == ativo).select("book").collect()
   ]

get_books_do_ativo("CESE22",df_books)

# COMMAND ----------

"""
Trabalhar com os ratings das tabelacar_
"""


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

def get_ratings_igual_abaixo(rating:str)->list[str]:
    df_ratings = spark.sql("""SELECT * FROM desafio_kinea.boletagem_cp.tabelacar_baixorisco """
                           ).sort("Nivel").collect()
    lista_ratings = []
    lista_nivels = []
    for row in df_ratings:
        #print(row["IntervaloRating"],row["Nivel"])
        lista_ratings.append(row["IntervaloRating"])
        lista_nivels.append(row["Nivel"])
    
    ratings_dict = construir_dict_ratings(lista_ratings,lista_nivels)

    best_level = -1
    for key,val in  sorted(ratings_dict.items(),key= lambda x: x[0]):
        if rating in val: #se o rating esta na lista
            best_level  = key
            break
    if best_level == -1:
        raise RuntimeError("Não foi possível achar nível do rating")
    
    print(best_level)
    return dict(
        filter(lambda x: x[0] >= best_level,ratings_dict.items()) #essa equação ou inequação é a principal coisa a se mudar caso precise modificar a lógica
    )

get_ratings_igual_abaixo("Aaa")
#rating_igual_ou_menor("A1","A1 a A4")

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT * FROM desafio_kinea.boletagem_cp.tabelacar_baixorisco

# COMMAND ----------

# Célula para pegar  dados de PL de crédito privado num fundo

df_pl_credito_privado = spark.sql("""
    WITH 
tab_booksoverview AS (

 SELECT
 distinct
   PositionDate
   ,Book          --Book: Classificacao organizacional dos ativos dos fundos
   ,Product       --Product: Produto, é o prório ativo
   ,ProductClass  --ProductClass: Tipo de Produto (Debenture,Fidc, Cri/Cra, etc)
   ,TradingDesk   --Fundo
   ,Position      --Posicao em valor financeiro total do ativo

 FROM
 desafio_kinea.boletagem_cp.booksoverviewposicao_fechamento  --Tabela com as posicoes dos fundos


 where (  LOWER(ProductClass) like '%debenture%'  --Apenas Ativos de Crédito Privado
     or LOWER(ProductClass) like '%bonds%' 
     or LOWER(ProductClass) like '%cra%' 
     or LOWER(ProductClass) like '%cri%' 
     or LOWER(ProductClass) like '%funds%' 
     or LOWER(ProductClass) like '%letra%' 
     or LOWER(ProductClass) like '%nota%'
     )

  and (  LOWER(Book) like '%ivan%') --Filtra Books Ivan (gestor do fundo) - Apenas Crédito Privado

and TradingDesk in ('KCP','RFA','KOP', '846', '134', '678','FRA', 'CPI','PAL','ID2','PID','APO','APP','IRF','KAT','PEM','PDA',"KRF","652","389","348","BVP") --Apenas fundos finais

)

, tab_pl as (

 SELECT
   distinct
   Data as PositionDate
   ,Codigo as TradingDesk
   ,PL
  from desafio_kinea.boletagem_cp.cotas cotas --Tabela com o PL dos fundos
)

,tab_fundos as (
 SELECT
 DISTINCT
 tab_booksoverview.*
 ,tab_pl.PL
 FROM
 tab_booksoverview
 LEFT JOIN
 tab_pl
 ON tab_pl.PositionDate = tab_booksoverview.PositionDate and tab_pl.TradingDesk = tab_booksoverview.TradingDesk
 
) 

select PositionDate,Book,TradingDesk AS Fundo,Position from tab_fundos
""")
#print(df_pl_credito_privado.count())
df_pl_credito_privado.groupBy("Fundo")

# COMMAND ----------

# MAGIC %sql
# MAGIC     WITH 
# MAGIC tab_booksoverview AS (
# MAGIC
# MAGIC  SELECT
# MAGIC  distinct
# MAGIC    PositionDate
# MAGIC    ,Book          --Book: Classificacao organizacional dos ativos dos fundos
# MAGIC    ,Product       --Product: Produto, é o prório ativo
# MAGIC    ,ProductClass  --ProductClass: Tipo de Produto (Debenture,Fidc, Cri/Cra, etc)
# MAGIC    ,TradingDesk   --Fundo
# MAGIC    ,Position      --Posicao em valor financeiro total do ativo
# MAGIC
# MAGIC  FROM
# MAGIC  desafio_kinea.boletagem_cp.booksoverviewposicao_fechamento  --Tabela com as posicoes dos fundos
# MAGIC
# MAGIC
# MAGIC  where (  LOWER(ProductClass) like '%debenture%'  --Apenas Ativos de Crédito Privado
# MAGIC      or LOWER(ProductClass) like '%bonds%' 
# MAGIC      or LOWER(ProductClass) like '%cra%' 
# MAGIC      or LOWER(ProductClass) like '%cri%' 
# MAGIC      or LOWER(ProductClass) like '%funds%' 
# MAGIC      or LOWER(ProductClass) like '%letra%' 
# MAGIC      or LOWER(ProductClass) like '%nota%'
# MAGIC      )
# MAGIC
# MAGIC   and (  LOWER(Book) like '%ivan%') --Filtra Books Ivan (gestor do fundo) - Apenas Crédito Privado
# MAGIC
# MAGIC and TradingDesk in ('KCP','RFA','KOP', '846', '134', '678','FRA', 'CPI','PAL','ID2','PID','APO','APP','IRF','KAT','PEM','PDA',"KRF","652","389","348","BVP") --Apenas fundos finais
# MAGIC
# MAGIC )
# MAGIC
# MAGIC , tab_pl as (
# MAGIC
# MAGIC  SELECT
# MAGIC    distinct
# MAGIC    Data as PositionDate
# MAGIC    ,Codigo as TradingDesk
# MAGIC    ,PL
# MAGIC   from desafio_kinea.boletagem_cp.cotas cotas --Tabela com o PL dos fundos
# MAGIC )
# MAGIC
# MAGIC ,tab_fundos as (
# MAGIC  SELECT
# MAGIC  DISTINCT
# MAGIC  tab_booksoverview.*
# MAGIC  ,tab_pl.PL
# MAGIC  FROM
# MAGIC  tab_booksoverview
# MAGIC  LEFT JOIN
# MAGIC  tab_pl
# MAGIC  ON tab_pl.PositionDate = tab_booksoverview.PositionDate and tab_pl.TradingDesk = tab_booksoverview.TradingDesk
# MAGIC  
# MAGIC ) 
# MAGIC
# MAGIC SELECT * FROM tab_fundos
# MAGIC
# MAGIC

# COMMAND ----------

# MAGIC %sql
# MAGIC     WITH 
# MAGIC tab_booksoverview AS (
# MAGIC
# MAGIC  SELECT
# MAGIC  distinct
# MAGIC    PositionDate
# MAGIC    ,Book          --Book: Classificacao organizacional dos ativos dos fundos
# MAGIC    ,Product       --Product: Produto, é o prório ativo
# MAGIC    ,ProductClass  --ProductClass: Tipo de Produto (Debenture,Fidc, Cri/Cra, etc)
# MAGIC    ,TradingDesk   --Fundo
# MAGIC    ,Position      --Posicao em valor financeiro total do ativo
# MAGIC
# MAGIC  FROM
# MAGIC  desafio_kinea.boletagem_cp.booksoverviewposicao_fechamento  --Tabela com as posicoes dos fundos
# MAGIC
# MAGIC
# MAGIC  where (  LOWER(ProductClass) like '%debenture%'  --Apenas Ativos de Crédito Privado
# MAGIC      or LOWER(ProductClass) like '%bonds%' 
# MAGIC      or LOWER(ProductClass) like '%cra%' 
# MAGIC      or LOWER(ProductClass) like '%cri%' 
# MAGIC      or LOWER(ProductClass) like '%funds%' 
# MAGIC      or LOWER(ProductClass) like '%letra%' 
# MAGIC      or LOWER(ProductClass) like '%nota%'
# MAGIC      )
# MAGIC
# MAGIC   and (  LOWER(Book) like '%ivan%') --Filtra Books Ivan (gestor do fundo) - Apenas Crédito Privado
# MAGIC
# MAGIC and TradingDesk in ('KCP','RFA','KOP', '846', '134', '678','FRA', 'CPI','PAL','ID2','PID','APO','APP','IRF','KAT','PEM','PDA',"KRF","652","389","348","BVP") --Apenas fundos finais
# MAGIC
# MAGIC )
# MAGIC
# MAGIC , tab_pl as (
# MAGIC
# MAGIC  SELECT
# MAGIC    distinct
# MAGIC    Data as PositionDate
# MAGIC    ,Codigo as TradingDesk
# MAGIC    ,PL
# MAGIC   from desafio_kinea.boletagem_cp.cotas cotas --Tabela com o PL dos fundos
# MAGIC )
# MAGIC
# MAGIC ,tab_fundos as (
# MAGIC  SELECT
# MAGIC  DISTINCT
# MAGIC  tab_booksoverview.*
# MAGIC  ,tab_pl.PL
# MAGIC  FROM
# MAGIC  tab_booksoverview
# MAGIC  LEFT JOIN
# MAGIC  tab_pl
# MAGIC  ON tab_pl.PositionDate = tab_booksoverview.PositionDate and tab_pl.TradingDesk = tab_booksoverview.TradingDesk
# MAGIC  
# MAGIC ) 
# MAGIC
# MAGIC SELECT t1.TradingDesk, SUM(Position) as PlCreditoPrivado FROM tab_fundos as t1 --soma e acha o total de crédito privado de cada fundo
# MAGIC JOIN --join na tabela de data mais recente, filtrando a tabela para as combinações de cada fundo - ativo mais recentes
# MAGIC (
# MAGIC -- acha a data mais recente para cada combinação fundo e ativo
# MAGIC SELECT TradingDesk, Product, MAX(PositionDate) AS MaxData from tab_fundos
# MAGIC GROUP BY TradingDesk, Product
# MAGIC ) t2
# MAGIC ON t1.TradingDesk = t2.TradingDesk AND t1.Product = t2.Product AND t1.PositionDate = t2.MaxData
# MAGIC GROUP BY t1.TradingDesk --groupby pelo fundo/trading desk

# COMMAND ----------

"""
Classes de retorno do verificador de operação
"""

class __Resultado:
    """
    Classe que representa o resultado de uma análise de alocação de crédito privado, com uma flag bool ditando se esse resultado teve sucesso ou não
    e uma tupla que representa o range de alocação possível
    """
    aprovada:bool
    range_possivel:tuple[float,float] | None

    def __init__(self,aprovada:bool,feedback:str,range_possivel:tuple[float,float]):
        self.aprovada = aprovada
        self.range_possivel = range_possivel


class ResultadoRange(__Resultado):
    """
    Diz o status da alocacao no teste de range de alocação de crédito privado, como ditado pela tabela range_alocacao:

    Retorno: Flag bool e range possível númerico que se encaixa nas regras de range do fundo
    """

class ResultadoRestricaoBook(__Resultado):
    """
    Diz o status da alocacao no teste de se o book_micro do fundo está como válido (valor da flag true) na tabela restricao_book

    Retorno: Flag bool, None
    """

class ResultadoRating(__Resultado):
    """
    Diz o resultado da alocação do ativo no teste de rating, como ditado pelas tabelas tabelacar_

    Retorno: Flag bool, None
    """

class ResultadoMaxEmissor(__Resultado):
    """
    Diz o resultado da alocação do ativo no teste de max_emissor, como ditado pelas tabelas tabelacar_

    Retorno: Flag bool e um teto que se encaixa no MaxEmissor
    """

@dataclass
class ResultadoAlocacao:
    """
    Resultado final da análise da alocação, com flag booleana de se foi aceita ou não e também feedback e ranges possíveis para cada verificação caso não seja aprovadas
    """

    aprovada: bool
    resultado_range: ResultadoRange
    resultado_restricao_book: ResultadoRestricaoBook
    resultado_rating: ResultadoRating
    resultado_max_emissor: ResultadoMaxEmissor


# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC WITH 
# MAGIC tab_booksoverview AS (
# MAGIC  SELECT
# MAGIC    DISTINCT
# MAGIC    PositionDate,
# MAGIC    Book,          -- Classificação organizacional dos ativos dos fundos
# MAGIC    Product,       -- Produto: ativo específico
# MAGIC    ProductClass,  -- Tipo de Produto (Debenture, Fidc, Cri/Cra, etc.)
# MAGIC    TradingDesk,   -- Fundo
# MAGIC    Position       -- Posição em valor financeiro total do ativo
# MAGIC  FROM
# MAGIC    desafio_kinea.boletagem_cp.booksoverviewposicao_fechamento  -- Tabela ajustada para posições dos fundos
# MAGIC  WHERE 
# MAGIC    (
# MAGIC      LOWER(ProductClass) LIKE '%debenture%'  -- Apenas Ativos de Crédito Privado
# MAGIC      OR LOWER(ProductClass) LIKE '%bonds%'
# MAGIC      OR LOWER(ProductClass) LIKE '%cra%'
# MAGIC      OR LOWER(ProductClass) LIKE '%cri%'
# MAGIC      OR LOWER(ProductClass) LIKE '%funds%'
# MAGIC      OR LOWER(ProductClass) LIKE '%letra%'
# MAGIC      OR LOWER(ProductClass) LIKE '%nota%'
# MAGIC    )
# MAGIC    AND (LOWER(Book) LIKE '%ivan%') -- Filtra Books Ivan (gestor do fundo) - Apenas Crédito Privado
# MAGIC    AND TradingDesk IN (
# MAGIC      'KCP', 'RFA', 'KOP', '846', '134', '678', 'FRA', 'CPI', 'PAL', 'ID2', 'PID', 
# MAGIC      'APO', 'APP', 'IRF', 'KAT', 'PEM', 'PDA', 'KRF', '652', '389', '348', 'BVP'
# MAGIC    ) -- Apenas fundos finais
# MAGIC ),
# MAGIC
# MAGIC tab_pl AS (
# MAGIC  SELECT
# MAGIC    DISTINCT
# MAGIC    Data AS PositionDate,
# MAGIC    Codigo AS TradingDesk,
# MAGIC    PL
# MAGIC  FROM
# MAGIC    desafio_kinea.boletagem_cp.cotas -- Tabela ajustada com o PL dos fundos
# MAGIC ),
# MAGIC
# MAGIC tab_fundos AS (
# MAGIC  SELECT
# MAGIC    DISTINCT
# MAGIC    tab_booksoverview.*,
# MAGIC    tab_pl.PL
# MAGIC  FROM
# MAGIC    tab_booksoverview
# MAGIC  LEFT JOIN
# MAGIC    tab_pl
# MAGIC  ON 
# MAGIC    tab_pl.PositionDate = tab_booksoverview.PositionDate 
# MAGIC    AND tab_pl.TradingDesk = tab_booksoverview.TradingDesk
# MAGIC ),
# MAGIC
# MAGIC PL_por_fundo (SELECT t1.TradingDesk, SUM(Position) as PlCreditoPrivado FROM tab_fundos as t1 --soma e acha o total de crédito privado de cada fundo
# MAGIC JOIN --join na tabela de data mais recente, filtrando a tabela para as combinações de cada fundo - ativo mais recentes
# MAGIC (
# MAGIC -- acha a data mais recente para cada combinação fundo e ativo
# MAGIC SELECT TradingDesk, Product, MAX(PositionDate) AS MaxData from tab_fundos
# MAGIC GROUP BY TradingDesk, Product
# MAGIC ) t2
# MAGIC ON t1.TradingDesk = t2.TradingDesk AND t1.Product = t2.Product AND t1.PositionDate = t2.MaxData
# MAGIC GROUP BY t1.TradingDesk --groupby pelo fundo/trading desk
# MAGIC )
# MAGIC
# MAGIC -- Query para etapa final, de relacionar ativos com seus fundos, dando join pelo book do ativo
# MAGIC -- com o book_micro das restrições de cada book para verificar se o ativo pode ser alocado ou não
# MAGIC -- dentro daquele book para determinado fundo (apontado pela flag "flag").
# MAGIC
# MAGIC -- Há também relacionado qual o peso de cada classe de ativo que será alocado para cada fundo, além
# MAGIC -- do range de alocação mínima e máxima para cada fundo.
# MAGIC
# MAGIC -- Será utilizado no processamento final para realizar a redistribuição entre os fundos de acordo com
# MAGIC -- a régua que é calculada anteriormente no processo.
# MAGIC
# MAGIC -- Essa tabela está relacionada com as restrições das classes ResultadoRange e ResultadoRestricaoBook
# MAGIC
# MAGIC SELECT 
# MAGIC   book_ativos.ativo,
# MAGIC   restricao_book.fundo,
# MAGIC   book_ativos.fundo_restrito,
# MAGIC   restricao_book.book_macro, 
# MAGIC   restricao_book.book_micro,
# MAGIC   restricao_book.flag,
# MAGIC   pesos_classes.peso,
# MAGIC   range_alocacao.alocacao_maxima,
# MAGIC   range_alocacao.alocacao_minima,
# MAGIC   PL_por_fundo.PlCreditoPrivado
# MAGIC FROM desafio_kinea.boletagem_cp.book_ativos as book_ativos
# MAGIC JOIN desafio_kinea.boletagem_cp.restricao_book as restricao_book 
# MAGIC ON book_ativos.book = restricao_book.book_micro
# MAGIC JOIN desafio_kinea.boletagem_cp.pesos_classes as pesos_classes
# MAGIC ON restricao_book.book_macro = pesos_classes.classe
# MAGIC JOIN desafio_kinea.boletagem_cp.range_alocacao as range_alocacao
# MAGIC ON pesos_classes.Fundo = range_alocacao.Fundo AND restricao_book.fundo = range_alocacao.Fundo
# MAGIC JOIN PL_por_fundo
# MAGIC ON PL_por_fundo.TradingDesk = restricao_book.fundo;
# MAGIC
# MAGIC -- SELECT * FROM (
# MAGIC --     SELECT DISTINCT Fundo FROM desafio_kinea.boletagem_cp.range_alocacao
# MAGIC --     EXCEPT
# MAGIC --     SELECT DISTINCT TradingDesk FROM PL_por_fundo
# MAGIC     
# MAGIC -- );
# MAGIC
# MAGIC -- SELECT * FROM (
# MAGIC --     SELECT DISTINCT TradingDesk FROM PL_por_fundo
# MAGIC --     EXCEPT
# MAGIC --     SELECT DISTINCT Fundo FROM desafio_kinea.boletagem_cp.range_alocacao
# MAGIC     
# MAGIC -- );
# MAGIC

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC -- Testando relações entre as tabelas para verificar se há perda de informação sobre os ativos no processo
# MAGIC
# MAGIC -- select * from desafio_kinea.boletagem_cp.restricao_book;
# MAGIC
# MAGIC -- select * from desafio_kinea.boletagem_cp.book_ativos;
# MAGIC
# MAGIC select Fundo from desafio_kinea.boletagem_cp.range_alocacao;
# MAGIC
# MAGIC -- select DISTINCT book, restricao_book.book_micro from desafio_kinea.boletagem_cp.restricao_book
# MAGIC --   join desafio_kinea.boletagem_cp.book_ativos on book_ativos.book = restricao_book.book_micro;