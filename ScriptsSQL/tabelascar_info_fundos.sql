/*
O objetivo dessa query é ditar qual a porcentagem do PL de certo fundo é composto por ativos de crédito privado de até certo rating, de acordo com a lógica das tabelas CAR
*/

WITH pl_total_fundo AS (
  SELECT t1.Codigo,t1.Data,t1.PL
  FROM desafio_kinea.boletagem_cp.cotas as t1
  JOIN ( --subquery para pegar as datas mais recentes
      SELECT Codigo, MAX(Data) AS MaxData --pega a data mais recente
      FROM desafio_kinea.boletagem_cp.cotas
      GROUP BY Codigo --groupby pelo código do fundo 
  ) t2 
  ON t1.Codigo = t2.Codigo AND t1.Data = t2.MaxData --join pelo código e data mais recente
  ORDER BY Data DESC --ordenar
)

/*
SELECT Codigo, PL AS pl_total, soma_pl_rating, soma_pl_rating/PL AS porcentagem_pl_rating FROM pl_total_fundo
JOIN (
  -- subquery para achar qual a porcenta
  SELECT ativos_pl.fundo, SUM(ativos_pl.PL) as soma_pl_rating FROM
  (

      WITH 
      tab_booksoverview AS (
      SELECT
        DISTINCT
        PositionDate,
        Book,          -- Classificação organizacional dos ativos dos fundos
        Product,       -- Produto: ativo específico
        ProductClass,  -- Tipo de Produto (Debenture, Fidc, Cri/Cra, etc.)
        TradingDesk,   -- Fundo
        Position       -- Posição em valor financeiro total do ativo
      FROM
        desafio_kinea.boletagem_cp.booksoverviewposicao_fechamento  -- Tabela ajustada para posições dos fundos
      WHERE 
        (
          LOWER(ProductClass) LIKE '%debenture%'  -- Apenas Ativos de Crédito Privado
          OR LOWER(ProductClass) LIKE '%bonds%'
          OR LOWER(ProductClass) LIKE '%cra%'
          OR LOWER(ProductClass) LIKE '%cri%'
          OR LOWER(ProductClass) LIKE '%funds%'
          OR LOWER(ProductClass) LIKE '%letra%'
          OR LOWER(ProductClass) LIKE '%nota%'
        )
        AND (LOWER(Book) LIKE '%ivan%') -- Filtra Books Ivan (gestor do fundo) - Apenas Crédito Privado
        AND TradingDesk IN (
          'KCP', 'RFA', 'KOP', '846', '134', '678', 'FRA', 'CPI', 'PAL', 'ID2', 'PID', 
          'APO', 'APP', 'IRF', 'KAT', 'PEM', 'PDA', 'KRF', '652', '389', '348', 'BVP'
        ) -- Apenas fundos finais
      ),

      tab_pl AS (
        SELECT
          DISTINCT
          Data AS PositionDate,
          Codigo AS TradingDesk,
          PL
        FROM
          desafio_kinea.boletagem_cp.cotas -- Tabela ajustada com o PL dos fundos
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
        ),

        PL_por_fundo (SELECT t1.TradingDesk, SUM(Position) as PlCreditoPrivado FROM tab_fundos as t1 --soma e acha o total de crédito privado de cada fundo
        JOIN --join na tabela de data mais recente, filtrando a tabela para as combinações de cada fundo - ativo mais recentes
        (
        -- acha a data mais recente para cada combinação fundo e ativo
        SELECT TradingDesk, Product, MAX(PositionDate) AS MaxData from tab_fundos
        GROUP BY TradingDesk, Product
        ) t2
        ON t1.TradingDesk = t2.TradingDesk AND t1.Product = t2.Product AND t1.PositionDate = t2.MaxData
        GROUP BY t1.TradingDesk --groupby pelo fundo/trading desk
        )

        -- Query para etapa final, de relacionar ativos com seus fundos, dando join pelo book do ativo
        -- com o book_micro das restrições de cada book para verificar se o ativo pode ser alocado ou não
        -- dentro daquele book para determinado fundo (apontado pela flag "flag").

        -- Há também relacionado qual o peso de cada classe de ativo que será alocado para cada fundo, além
        -- do range de alocação mínima e máxima para cada fundo.

        -- Será utilizado no processamento final para realizar a redistribuição entre os fundos de acordo com
        -- a régua que é calculada anteriormente no processo.

        -- Essa tabela está relacionada com as restrições das classes ResultadoRange e ResultadoRestricaoBook

        SELECT 
          book_ativos.ativo,
          restricao_book.fundo,
          PL_por_fundo.PlCreditoPrivado,
          tabela_pl.PL 
        FROM desafio_kinea.boletagem_cp.book_ativos as book_ativos
        JOIN desafio_kinea.boletagem_cp.restricao_book as restricao_book 
        ON book_ativos.book = restricao_book.book_micro
        JOIN desafio_kinea.boletagem_cp.pesos_classes as pesos_classes
        ON restricao_book.book_macro = pesos_classes.classe
        JOIN desafio_kinea.boletagem_cp.range_alocacao as range_alocacao
        ON pesos_classes.Fundo = range_alocacao.Fundo AND restricao_book.fundo = range_alocacao.Fundo
        JOIN PL_por_fundo
        ON PL_por_fundo.TradingDesk = restricao_book.fundo
        JOIN ( --subquery para achar o PL total
            SELECT t1.Codigo,t1.Data,t1.PL
            FROM desafio_kinea.boletagem_cp.cotas as t1
            JOIN (
                SELECT Codigo, MAX(Data) AS MaxData
                FROM desafio_kinea.boletagem_cp.cotas
                GROUP BY Codigo
            ) t2 
            ON t1.Codigo = t2.Codigo AND t1.Data = t2.MaxData
        ) tabela_pl
        ON tabela_pl.Codigo = restricao_book.fundo
  ) AS ativos_pl --query para achar ativos e os fundos a que eles pertencem e o PL dos fundos
  JOIN  (
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
  ) AS ativos_rating ON ativos_rating.Ativo = ativos_pl.ativo --join na tabela de rating de ativos
  WHERE RatingOp IN ('Baa3','Baa4')
  GROUP BY fundo

) AS soma_pl_rating ON soma_pl_rating.fundo = pl_total_fundo.Codigo
*/


  SELECT * FROM
  (

      WITH 
      tab_booksoverview AS (
      SELECT
        DISTINCT
        PositionDate,
        Book,          -- Classificação organizacional dos ativos dos fundos
        Product,       -- Produto: ativo específico
        ProductClass,  -- Tipo de Produto (Debenture, Fidc, Cri/Cra, etc.)
        TradingDesk,   -- Fundo
        Position       -- Posição em valor financeiro total do ativo
      FROM
        desafio_kinea.boletagem_cp.booksoverviewposicao_fechamento  -- Tabela ajustada para posições dos fundos
      WHERE 
        (
          LOWER(ProductClass) LIKE '%debenture%'  -- Apenas Ativos de Crédito Privado
          OR LOWER(ProductClass) LIKE '%bonds%'
          OR LOWER(ProductClass) LIKE '%cra%'
          OR LOWER(ProductClass) LIKE '%cri%'
          OR LOWER(ProductClass) LIKE '%funds%'
          OR LOWER(ProductClass) LIKE '%letra%'
          OR LOWER(ProductClass) LIKE '%nota%'
        )
        AND (LOWER(Book) LIKE '%ivan%') -- Filtra Books Ivan (gestor do fundo) - Apenas Crédito Privado
        AND TradingDesk IN (
          'KCP', 'RFA', 'KOP', '846', '134', '678', 'FRA', 'CPI', 'PAL', 'ID2', 'PID', 
          'APO', 'APP', 'IRF', 'KAT', 'PEM', 'PDA', 'KRF', '652', '389', '348', 'BVP'
        ) -- Apenas fundos finais
      ),

      tab_pl AS (
        SELECT
          DISTINCT
          Data AS PositionDate,
          Codigo AS TradingDesk,
          PL
        FROM
          desafio_kinea.boletagem_cp.cotas -- Tabela ajustada com o PL dos fundos
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
        ),

        PL_por_fundo (SELECT t1.TradingDesk, SUM(Position) as PlCreditoPrivado FROM tab_fundos as t1 --soma e acha o total de crédito privado de cada fundo
        JOIN --join na tabela de data mais recente, filtrando a tabela para as combinações de cada fundo - ativo mais recentes
        (
        -- acha a data mais recente para cada combinação fundo e ativo
        SELECT TradingDesk, Product, MAX(PositionDate) AS MaxData from tab_fundos
        GROUP BY TradingDesk, Product
        ) t2
        ON t1.TradingDesk = t2.TradingDesk AND t1.Product = t2.Product AND t1.PositionDate = t2.MaxData
        GROUP BY t1.TradingDesk --groupby pelo fundo/trading desk
        )

        -- Query para etapa final, de relacionar ativos com seus fundos, dando join pelo book do ativo
        -- com o book_micro das restrições de cada book para verificar se o ativo pode ser alocado ou não
        -- dentro daquele book para determinado fundo (apontado pela flag "flag").

        -- Há também relacionado qual o peso de cada classe de ativo que será alocado para cada fundo, além
        -- do range de alocação mínima e máxima para cada fundo.

        -- Será utilizado no processamento final para realizar a redistribuição entre os fundos de acordo com
        -- a régua que é calculada anteriormente no processo.

        -- Essa tabela está relacionada com as restrições das classes ResultadoRange e ResultadoRestricaoBook

        SELECT 
          book_ativos.ativo,
          restricao_book.fundo,
          PL_por_fundo.PlCreditoPrivado,
          tabela_pl.PL 
        FROM desafio_kinea.boletagem_cp.book_ativos as book_ativos
        JOIN desafio_kinea.boletagem_cp.restricao_book as restricao_book 
        ON book_ativos.book = restricao_book.book_micro
        JOIN desafio_kinea.boletagem_cp.pesos_classes as pesos_classes
        ON restricao_book.book_macro = pesos_classes.classe
        JOIN desafio_kinea.boletagem_cp.range_alocacao as range_alocacao
        ON pesos_classes.Fundo = range_alocacao.Fundo AND restricao_book.fundo = range_alocacao.Fundo
        JOIN PL_por_fundo
        ON PL_por_fundo.TradingDesk = restricao_book.fundo
        JOIN ( --subquery para achar o PL total
            SELECT t1.Codigo,t1.Data,t1.PL
            FROM desafio_kinea.boletagem_cp.cotas as t1
            JOIN (
                SELECT Codigo, MAX(Data) AS MaxData
                FROM desafio_kinea.boletagem_cp.cotas
                GROUP BY Codigo
            ) t2 
            ON t1.Codigo = t2.Codigo AND t1.Data = t2.MaxData
        ) tabela_pl
        ON tabela_pl.Codigo = restricao_book.fundo
  ) AS ativos_pl --query para achar ativos e os fundos a que eles pertencem e o PL dos fundos
  JOIN  (
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
  ) AS ativos_rating ON ativos_rating.Ativo = ativos_pl.ativo --join na tabela de rating de ativos
  WHERE RatingOp IN ('Baa3','Baa4')
  --GROUP BY fundo
 