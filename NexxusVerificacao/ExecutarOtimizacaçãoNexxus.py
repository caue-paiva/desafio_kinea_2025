!pip install openai==0.28
dbutils.library.restartPython()
import pandas as pd
import numpy as np
import scipy
import ParsingMemoriaCalculo
import openai
import ast
openai.api_type = "azure"
openai.api_base = "https://oai-dk.openai.azure.com/"
openai.api_version = "2023-12-01-preview"
openai.api_key = dbutils.secrets.get('akvdesafiokinea','azure-oai-dk')

def gerar_restricao(descricao,ativos,saldo_base,exposicao,l_max,l_min):   
    '''
    Função para gerar código de restrição que será utilizado na otimização
    '''
    contexto_gpt = '''
        Você irá receber a descrição de uma regra, um conjunto posições de ativos que são considerados para o cálculo dessa regra, um saldo base, limite minimo e máximo em relação a esse saldo base, a porcentagem que não por essa restrição e o saldo dos outros ativos naquele fundo. 
        
        Lembre-se de considerar se a porcentagem está acima do limite_maximo ou abaixo do limite minimo para tomar a decisão de como escrever o código.
        Lembre-se também que o saldo outros ativos deve ser diminuido na hora do retorno. Não se esqueça disso

        A partir disso você deve gerar um código de restrição no formato utilizado pelo scipy.minimize.
        
        Exemplo 1:
            Descrição: Art. 45. Cumulativamente aos limites de concentração por emissor, a classe de cotas deve observar os seguintes limites de concentração por modalidade de ativo financeiro, sem prejuízo das normas aplicáveis ao seu tipo: I - ate 20% (vinte por cento) de ativos de renda fixa;
            Posição Ativos: [0,1,4,5,6]
            Saldo Base: 500000
            Limite Mínimo: 0
            Limite Máximo: 0.2
            Porcentagem:0.25
            SaldoOutrosAtivos: 250000
            def restricao(x,SaldoOutrosAtivos):
                ativos_considerados = [x[0],x[1],x[4],x[5],x[6]...]
                return  (0.2 * 500000 ) - SaldoOutrosAtivos - sum(ativos_considerados)
               
        Exemplo 2: 
            Descrição: Regulamento - POLÍTICA DE INVESTIMENTO - O objetivo do FUNDO é aplicar, no mínimo, 80% (oitenta por cento) de seus recursos em ativos financeiros de renda fixa relacionados diretamente, ou sintetizados via derivativos, ao fator de risco que dá nome à classe, observado que a rentabilidade do FUNDO será impactada pelos custos e despesas do FUNDO, inclusive taxa de administração.
            Posição Ativos: [0,1,4,5,6]
            Saldo Base: 500000
            Limite Mínimo: 0.8
            Limite Máximo: 1
            Porcentagem: 0.68
            SaldoOutrosAtivos: 250000
            def restricao(x,SaldoOutrosAtivos):
                ativos_considerados = [x[0],x[1],x[4],x[5],x[6]...]
                return sum(ativos_considerados) + SaldoOutrosAtivos - (0.8 * 500000) 
         
         Exemplo 3:
            Descrição: Vedação
            Posição Ativos: [0,1,4,5,6]
            Saldo Base: 500000
            Limite Mínimo: null
            Limite Máximo: null
            Porcentagem: null
            def restricao(x,SaldoOutrosAtivos):
                ativos_considerados = [x[0],x[1],x[4],x[5],x[6]...]
                return -sum(ativos_considerados)
    '''
    message_text = [
                {"role":"system","content":contexto_gpt},
                {"role":"user","content":f"Descrição: {descricao}\n Posições Ativos: {ativos} \n Saldo Base: {saldo_base} \n Limite Mínimo {l_min}  \n Limite Máximo: {l_max} \n Porcentagem: {exposicao}"}
               ]
    
    completion = openai.ChatCompletion.create(
        engine="gpt35turbo16k",
        messages = message_text,
        temperature=0.0,
        max_tokens=1200,
        top_p=0.95,
        frequency_penalty=0.0,
        presence_penalty=0.0,
        stop=None,
        )

    return completion.to_dict()['choices'][0]['message']['content']

def indices_ativos (ordem,fundo,ativos):
    '''
    Função para retornar index dos ativos para que possamos utilizar isso na otimização
    '''
    ativos_nomes = []
    for ativo in ativos:
        ativos_nomes.append(ativo.split(" ")[1])
    indices = ordem[(ordem['FUNDO'] == fundo)  & (ordem['ATIVO'].isin(ativos_nomes))].index
    return indices

def calcula_saldo_outros_ativos(fundo,memoriacalculo,ordem):
    ordem_fundo = ordem[ordem['FUNDO'] == fundo][["ATIVO","PU"]].rename(columns={'PU':'POSIÇÃO_ORDEM','ATIVO':'NOME'})
    memoriacalculo = memoriacalculo.groupby('NOME',as_index=False)['POSIÇÃO'].sum()
    df = pd.merge(memoriacalculo,ordem_fundo,on='NOME',how='left').fillna(0)
    df['POSIÇÃO_REAL'] = df['POSIÇÃO'] - df['POSIÇÃO_ORDEM']
    return df['POSIÇÃO_REAL'].sum()

def otimiza_ordem():
    ordem = spark.read.options(header='True', inferSchema='True').csv('/Volumes/desafio_kinea/boletagem_cp/files/InputNexxus/input_nexxus.csv').toPandas()   
    order = ordem.drop(columns='_c0')
    ordem['VALOR'] = ordem['PU'] * ordem['QTDE']
    #Gerando Vetor Inicial com Distribuição Uniforme Entre os Fundos, necessário igual a somar final
    ordem_0 = np.random.uniform(min(ordem['VALOR'].values),max(ordem['VALOR'].values),len(ordem))

    #Percorrer Cada Linha gerando as restrições e adicionando elas em um 
    restricoes = []
    
    #Adicionando restrições para valores negativos se manterem negativos e valores positivos se manterem positivos
    for idx, valor in enumerate(ordem['VALOR'].values):  
        if valor < 0:
            restricoes.append({'type': 'ineq', 'fun': lambda x, idx=idx: -x[idx]})  
        else:
            restricoes.append({'type': 'ineq', 'fun': lambda x, idx=idx: x[idx]})  

    #Adicionando Restrição para que soma do alocado em um ativo se mantenha sempre igual
    for nome_ativo in ordem['ATIVO'].unique():
        # Obtém os índices dos ativos correspondentes
        ativos_ = ordem[ordem['ATIVO'] == nome_ativo].index.tolist()
        
        # Calcula a soma inicial para esses ativos
        soma_ativo = sum(ordem['VALOR'].iloc[i] for i in ativos_)

        # Define a função de restrição
        def ativo_(x, ativos_=ativos_, soma_ativo=soma_ativo):
            return sum(x[i] for i in ativos_) - soma_ativo

        # Adiciona a restrição à lista
        restricoes.append({'type': 'eq', 'fun': ativo_})
   
    #Ler Histórico Nexxus pra DataHoraVersão Mais recente
    sql = """
       WITH UltimoHistorico AS (
            SELECT '{DataHoraVersao}' AS UltimaData
            FROM desafio_kinea.boletagem_cp.nxenq_resultadoenquadramentohist
            WHERE status = 1
        )

        SELECT DISTINCT
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
            ON nxe.DataHoraVersao = uh.UltimaData -- join para filtrar apenas para o último timestamp de simulação (nxe.DataHoraVersao)
        LEFT JOIN desafio_kinea.boletagem_cp.nxenq_regras nxr 
            ON nxr.IdRegra = CAST(regexp_replace(nxe.IdRegra, '[^0-9]', '') AS INT) -- join para a tabela de regras do tipo L%
            AND nxe.IdRegra LIKE 'L%'  
        LEFT JOIN desafio_kinea.boletagem_cp.nxenq_regrasporconcentracao nxrc
            ON nxrc.IdRegra = CAST(regexp_replace(nxe.IdRegra, '[^0-9]', '') AS INT)
            AND (nxe.IdRegra LIKE 'CM%' OR nxe.IdRegra LIKE 'CD%') -- join para a tabela de regras de concentração (CM%/CD%)
        LEFT JOIN desafio_kinea.boletagem_cp.nxenq_memoriacalculo nxmc --join com tabela de memoria de cálculo
            ON nxmc.DataHoraVersao = uh.UltimaData --join pela DataHoraVersao(última simulação), pelo Id do fundo e Id da regra
            AND nxe.IdRegra = nxmc.IdRegra
            AND nxe.IdFundo = nxmc.IdFundo
        where nxe.status = 1  
        and nxe.IdFundo = 'CPI'
        and nxe.IdRegra = 'L677'
        --and nxe.IdFundo = 'CP4' -- Adição de Cláusula para Teste
        --and (nxe.IdRegra = 'L1206' or nxe.IdRegra = 'L636') -- Adição de Cláusula para Teste
        """
    #DataHoraVersaoEscolhida = '2025-02-12T14:46:18.000+00:00' - Exemplo Teste Mínimo
    #DataHoraVersaoEscolhida = '2025-02-10T11:12:37.000+00:00' - Exemplo Teste Máximo
    DataHoraVersaoEscolhida = '2025-02-07T11:22:56.000+00:00'
    historico_nexxus = spark.sql(sql.format(DataHoraVersao = DataHoraVersaoEscolhida)).toPandas()

    #Aqui começamos o looping para pegar as retrições de cada linha do historico
    for idx, row in historico_nexxus.iterrows():
        #row = historico_nexxus.loc[0] #Apenas para Testes enquanto o Ali não envia
        memoriacalculo = ParsingMemoriaCalculo.tabela_texto_memoria_para_df(row['MemoriaCalculo'])    
        ativos = memoriacalculo['NOME'].unique() 
        index_ativos = indices_ativos(ordem,row['IdFundo'],ativos)
        
        descricao = row['DescricaoDetalhada_nexusregras']
        if descricao is None or descricao == '':
            descricao = row['DescricaoDetalhada_nexusregras']

        restricao = gerar_restricao(descricao,index_ativos,row['SaldoBaseCalculo'],row['ValorExposicao'],row['LimiteMax'],row['LimiteMin'])
        restricao = restricao[:13]+f"_{idx}"+restricao[13:] #Adicionando um numerador na restrição

        #Executando Função Criada
        local_scope = {}
        exec(restricao, globals(), local_scope)
        # Recuperar a função criada
        nome_funcao = f"restricao_{idx}"
        restricao_func = local_scope[nome_funcao]
        
        #Calculo do Saldo Restante
        #SaldoOutrosAtivos = calcula_saldo_outros_ativos(row['IdFundo'],memoriacalculo,ordem)  - Real
        #SaldoOutrosAtivos = 4488409934.9951079157038857079701 #Saldo necessário pra teste - Exemplo Teste Limite Mínimo
        #SaldoOutrosAtivos = 711723122.4708 #Exemplo Teste Limite Máximo
        SaldoOutrosAtivos = 51659592.775116
        restricoes.append({'type':'ineq','fun':restricao_func,'args':(SaldoOutrosAtivos,)})    
    

    #Definindo função objetivo
    def objetivo(x,ordem_ideal):
        return (np.abs(ordem_ideal - x).sum())
    
    #Realizar minimização
    minimizador = scipy.optimize.minimize(
        fun=objetivo,
        x0=ordem_0,
        args=(ordem['VALOR'].values),
        constraints=restricoes,
        method='trust-constr',
        options={'maxiter': 100000,'disp':False}
    )

   
    ordem['FINAL'] = minimizador.x
    ordem['QTDE_FINAL'] = round(ordem['FINAL']/ordem['PU'])
    
    '''
    Logs Teste Limite Mínimo
    print(f"Exposição pós Ajuste Discretizado {((ordem['QTDE_FINAL']*ordem['PU'])[3:].sum()+SaldoOutrosAtivos)/row['SaldoBaseCalculo']}")
    
    Logs Teste Limite Máximo
    print(f"Exposição pós Ajuste Discretizado {((ordem['QTDE_FINAL']*ordem['PU'])[:2].sum()+SaldoOutrosAtivos)/row['SaldoBaseCalculo']}")
    '''
    print(minimizador)
    
    #order_otimizada.to_csv("/Volumes/desafio_kinea/boletagem_cp/files/InputNexxus/input_nexxus.csv") salvar o final no input para re-entrada no nexxus
    
    return ordem

if __name__ == "__main__":
    teste = otimiza_ordem()
    display(teste)