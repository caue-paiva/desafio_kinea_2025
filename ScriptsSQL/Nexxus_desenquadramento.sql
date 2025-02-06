-- Query para buscar e relacionar os dados das tabelas do nexxus, puxando a última data da tabela de histórico de enquadramento, e relacionando as regras específicas (like L% com a tabela nxenq_regras e like CM% ou CD% com a tabela nxenq_regrasconcentracao), além de puxar a memória de cálculo da tabela referente ao cálculo dos desenquadramentos


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
    nxr.ValorMin as ValorMin_nexusregras,
    nxr.ValorMax as ValorMax_nexusregras,
    nxr.Descricao as Descricao_nexusregras,
    nxr.DescricaoDetalhada as DescricaoDetalhada_nexusregras,
    nxrc.LimiteMin as LimiteMin_concentracao,
    nxrc.LimiteMax as LimiteMax_concentracao,
    nxrc.Descricao as Descricao_concentracao,
    nxrc.DescricaoDetalhada as DescricaoDetalhada_concentracao,
    nxmc.MemoriaCalculo as MemoriaCalculo
FROM desafio_kinea.boletagem_cp.nxenq_resultadoenquadramentohist nxe 
INNER JOIN UltimoHistorico uh 
    ON nxe.DataHoraVersao = uh.UltimaData -- join para filtrar apenas para o último timestamp de simulação (nxe.DataHoraVersao)
LEFT JOIN desafio_kinea.boletagem_cp.nxenq_regras nxr 
    ON nxr.IdRegra = CAST(regexp_replace(nxe.IdRegra, '[^0-9]', '') AS INT) -- join para a tabela de regras do tipo L%
    AND nxe.IdRegra LIKE 'L%'  
LEFT JOIN desafio_kinea.boletagem_cp.nxenq_regrasporconcentracao nxrc
    ON nxrc.IdRegra = CAST(regexp_replace(nxe.IdRegra, '[^0-9]', '') AS INT)
    AND (nxe.IdRegra LIKE 'CM%' OR nxe.IdRegra LIKE 'CD%') -- join para a tabela de regras de concentração (CM%/CD%)
LEFT JOIN desafio_kinea.boletagem_cp.nxenq_memoriacalculo nxmc --join com tabela de memoria de cálculo
    ON nxmc.DataHoraVersao = uh.UltimaData --join pela DataHoraVersao(última simulação), pelo Id do fundo e Id da regra
    AND nxe.IdRegra = nxmc.IdRegra
    AND nxe.IdFundo = nxmc.IdFundo
where nxe.status = 1; -- filtro para apenas quando há algum desenquadramento