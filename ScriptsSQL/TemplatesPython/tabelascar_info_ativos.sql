
/*
Query para pegar valores para avaliar alocações de ativos seguindo das regras da tabelacar, cada linha é um ativo, com seu emissor, sua data de experição, seu rating
e rating do seu emissor.

OBS: Essa query é bem experimental e deve ser testada ainda, além disso o uso da tabela agendacp é provisória, pois seria melhor extrair os nomes dos ativos a partir
da tabela cadastroativo e achar seu emissor por um join com o emissor ID, mas não temos essa tabela agora.
*/

--seria melhor começar da tabela cadastro ativo e dar join numa tabela com o ID do grupo, mas não temos essa informação ainda
SELECT DISTINCT 
  Emissor, 
  Ativo, 
  FLOOR(DATEDIFF(Vencimento,CURRENT_DATE) / 360) AS ExpiracaoAnos,
  RatingOp,
  RatingGrupo 
FROM desafio_kinea.boletagem_cp.agendacp
JOIN desafio_kinea.boletagem_cp.cadastroativo ON TickerOp = Ativo --join para ter a coluna de Vencimento
JOIN desafio_kinea.boletagem_cp.ratingopatual ON ratingopatual.TickerOp = Ativo--join para ter coluna de rating
JOIN desafio_kinea.boletagem_cp.ratinggrupoatual ON NomeGrupo = Emissor 