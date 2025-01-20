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
 desafio_kinea.boletagem_cp. booksoverviewposicao_fechamento  --Tabela com as posicoes dos fundos


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

SELECT 
    TradingDesk, 
    Product, 
    PositionDate, 
    Position
FROM 
    tab_fundos t1
WHERE 
    PositionDate = (
        SELECT 
            MAX(PositionDate)
        FROM 
            tab_fundos t2
        WHERE 
            t1.TradingDesk = t2.TradingDesk 
            AND t1.Product = t2.Product
    )
ORDER BY TradingDesk, Product;