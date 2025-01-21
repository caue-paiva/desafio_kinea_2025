
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
-- Até aqui é a query que foi proporcionada pelo Caio para filtrar apenas para os ativos certos e de crédito privado

/*
Query Adicional para com os objetivos:

1) Agrupar pelas combinações únicas de ativos/produtos e fundos 
2) Achar data mais recentes para essa combinação
3) Somar o total da coluna Position desses agrupamentos
4) Achar no total de PL de crédito privado de cada fundo
*/


SELECT t1.TradingDesk, SUM(Position) as PlCreditoPrivado FROM tab_fundos as t1 --soma e acha o total de crédito privado de cada fundo
JOIN --join na tabela de data mais recente, filtrando a tabela para as combinações de cada fundo - ativo mais recentes
(
  -- acha a data mais recente para cada combinação fundo e ativo
  SELECT TradingDesk, Product, MAX(PositionDate) AS MaxData from tab_fundos
  GROUP BY TradingDesk, Product
) t2
ON t1.TradingDesk = t2.TradingDesk AND t1.Product = t2.Product AND t1.PositionDate = t2.MaxData
GROUP BY t1.TradingDesk --groupby pelo fundo/trading desk