-- busca a última data relativa à uma simulação no nexxus
WITH UltimoHistorico AS (
    SELECT MAX(DataHoraVersao) AS UltimaData
    FROM desafio_kinea.boletagem_cp.nxenq_resultadoenquadramentohist
    WHERE status = 1
)

SELECT 
    nxe.IdFundo as IdFundo,
    nxe.IdRegra AS IdRegra_resultado_enquadramento,  
    nxe.DataHoraVersao as DataHoraVersao,
    nxe.SaldoBaseCalculo as SaldoBaseCalculo,
    nxe.ValorExposicao as ValorExposicao,
    nxe.SaldoObjeto as SaldoObjeto,
    nxe.LimiteMin as LimiteMin,
    nxe.LimiteMax as LimiteMax,
    nxr.ValorMin as LimiteMin_nexxus,
    nxr.ValorMax as LimiteMax_nexxus,
    nxr.Descricao as Descricao_nexxus,
    nxr.DescricaoDetalhada as DescricaoDetalhada_nexxus,
    nxmc.MemoriaCalculo as MemoriaCalculo
FROM desafio_kinea.boletagem_cp.nxenq_resultadoenquadramentohist nxe 
INNER JOIN UltimoHistorico uh 
    ON nxe.DataHoraVersao = uh.UltimaData -- join para filtrar apenas para o último timestamp de simulação (nxe.DataHoraVersao)
INNER JOIN desafio_kinea.boletagem_cp.nxenq_regras nxr
    ON nxr.IdRegra = CAST(regexp_replace(nxe.IdRegra, '[^0-9]', '') AS INT)
    AND nxe.IdRegra LIKE 'L%'
LEFT JOIN desafio_kinea.boletagem_cp.nxenq_memoriacalculo nxmc --join com tabela de memoria de cálculo
    ON nxmc.DataHoraVersao = uh.UltimaData --join pela DataHoraVersao(última simulação), pelo Id do fundo e Id da regra
    AND nxe.IdRegra = nxmc.IdRegra
    AND nxe.IdFundo = nxmc.IdFundo
where nxe.status = 1; -- filtro para apenas quando há algum desenquadramento