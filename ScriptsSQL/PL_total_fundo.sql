SELECT t1.Codigo,t1.Data,t1.PL
FROM desafio_kinea.boletagem_cp.cotas as t1
JOIN ( --subquery para pegar as datas mais recentes
    SELECT Codigo, MAX(Data) AS MaxData --pega a data mais recente
    FROM desafio_kinea.boletagem_cp.cotas
    GROUP BY Codigo --groupby pelo código do fundo 
) t2 
ON t1.Codigo = t2.Codigo AND t1.Data = t2.MaxData --join pelo código e data mais recente
ORDER BY Data DESC; --ordenar
