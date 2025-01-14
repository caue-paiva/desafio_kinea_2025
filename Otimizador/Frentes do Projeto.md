### Funcionamento do Projeto:
* Recebemos uma ordem
* Extraímos dados necessários para Cálculo de Régua Book Macro
* Calculamos a Régua Book Macro
* Redistribuímos de acordo com as Restrições de Book Micro e Fundo Restrito
	* Revisar fórmula de redistribuição e como ela se comporta com várias restrições de uma vez?
	* Fazemos  a redistribuição por etapas ou toda de uma vez?
* Com a Régua Pré Verificação passamos pelas funções de verificação (Cauê e Cicero)
	* Como conseguimos quanto e de onde será redistribuido?
	* Redistribuimos a cada verificação ou apenas ao final?
	* Precisamos de Métodos otimizadores? Se sim Qual? Se não , a redistribuição utilizada até agora funciona?
* Gerar Régua Final Discretizada

### Pendências:
#### Teórico:
1. Verificar fórmulas de redistribuição até Régua Pré Verificação
2. Verificar se podemos fazer para varias restrições em 1 equação só
3. Formalizar o que as funções dos meninos irão retornar e como calculamos o erro 
4. Como redistribuímos o erro? Mantemos o mesmo formato?
#### Implementação:
* Terminar Função principal
1. Terminar função de extração de informações
1. Implementar função de redistribuição
2. Implementar funções para consumir funções geradas pelo Cauê e Cícero 
	1. Fazer funções imaginarias de exemplo como se fossem a do caue e cicero
3. Implementar Discretização e retornar Régua Final

