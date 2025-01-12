SELECT t1.Codigo,t1.Data,t1.PL
FROM desafio_kinea.boletagem_cp.cotas as t1
JOIN (
    SELECT Codigo, MAX(Data) AS MaxData
    FROM desafio_kinea.boletagem_cp.cotas
    GROUP BY Codigo
) t2 
ON t1.Codigo = t2.Codigo AND t1.Data = t2.MaxData
ORDER BY Data DESC;
