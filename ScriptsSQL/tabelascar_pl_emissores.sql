/*
O objetivo dessa query é ditar qual a porcentagem do PL de certo fundo é composto por emissores com rating de certo nível
*/

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


SELECT Emissor, RatingGrupo, TradingDesk, pl_emissor, PL FROM pl_total_fundo --query dando join da tabela de Pl total com a tabela de PL filtrado por emissores
JOIN 
( --subquery para agregar PL de crédito privado por emissor,
  SELECT Emissor,RatingGrupo, t2.TradingDesk, SUM(Position) as pl_emissor FROM tab_fundos as t1 --soma e acha o total de crédito privado de cada fundo agrupado pelo emissores
  JOIN --join na tabela de data mais recente, filtrando a tabela para as combinações de cada fundo <-> ativo mais recentes
  (
    -- acha a data mais recente para cada combinação fundo e ativo
    SELECT TradingDesk, Product, MAX(PositionDate) AS MaxData from tab_fundos
    GROUP BY TradingDesk, Product
  ) t2
  ON t1.TradingDesk = t2.TradingDesk AND t1.Product = t2.Product AND t1.PositionDate = t2.MaxData --join na data mais recente
  JOIN --subquery para o rating dos ativos
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
  ON  t1.Product = Ativo --join no nome do ativo
  GROUP BY Emissor,RatingGrupo, t2.TradingDesk --groupby pelo emissor , seu rating (que é o mesmo para todas as linhas de um mesmo emissor, então não muda mta coisa) e o fundo que ele está inserido
) AS tabela_emissor
ON pl_total_fundo.Codigo = tabela_emissor.TradingDesk --join pela coluna de fundos entre a tabela de PL total e a tabela de PL filtrada por emissor