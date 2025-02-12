import pandas as pd
import scipy
import ParsingMemoriaCalculo
def gerar_restricao(descricao,ativos,saldo_base,exposicao,l_max,l_min):   
    '''
    Função para gerar código de restrição que será utilizado na otimização
    '''
    contexto_gpt = '''
        Você irá receber a descrição de uma regra, um conjunto posições de ativos que são considerados para o cálculo dessa regra, um saldo base, limite minimo e máximo em relação a esse saldo base e a porcentagem que não por essa restrição. Lembre-se de considerar se a porcentagem está acima do limite_maximo ou abaixo do limite minimo para tomar a decisão de como escrever o código
        A partir disso você deve gerar um código de restrição no formato utilizado pelo scipy.minimize.
        
        Exemplo 1:
            Descrição: Art. 45. Cumulativamente aos limites de concentração por emissor, a classe de cotas deve observar os seguintes limites de concentração por modalidade de ativo financeiro, sem prejuízo das normas aplicáveis ao seu tipo: I - ate 20% (vinte por cento) de ativos de renda fixa;
            Posição Ativos: [0,1,4,5,6]
            Saldo Base: 500000
            Limite Mínimo: 0
            Limite Máximo: 0.2
            Porcentagem:0.25
            def restricao(x):
                ativos_considerados = [x[0],x[1],x[4],x[5],x[6]...]
                return  0.2 * 500000 -  sum(ativos_considerados)
        Exemplo 2: 
            Descrição: Regulamento - POLÍTICA DE INVESTIMENTO - O objetivo do FUNDO é aplicar, no mínimo, 80% (oitenta por cento) de seus recursos em ativos financeiros de renda fixa relacionados diretamente, ou sintetizados via derivativos, ao fator de risco que dá nome à classe, observado que a rentabilidade do FUNDO será impactada pelos custos e despesas do FUNDO, inclusive taxa de administração.
            Posição Ativos: [0,1,4,5,6]
            Saldo Base: 500000
            Limite Mínimo: 0.8
            Limite Máximo: 1
            Porcentagem: 0.68
            def restricao(x):
                ativos_considerados = [x[0],x[1],x[4],x[5],x[6]...]
                return sum(ativos_considerados) - 0.8 * 500000    
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
    indices = ordem[(ordem['fundo'] == fundo)  & (ordem['ativo'].isin(ativos))].index
    return indices

def otimiza_ordem():
    #Ler ordem que foi usada de input pro nexxus
    ordem = pd.read_csv("/Volumes/desafio_kinea/boletagem_cp/files/InputNexxus/input_nexxus.csv")
    
    #Ler Histórico Nexxus pra DataHoraVersão Mais recente
    historico_nexxus = spark.sql("") #Completar  com query do Cícero

    #Percorrer Cada Linha gerando as restrições e adicionando elas em um 
    restricoes = []
    for i,row in historico_nexxus.iterrows():
        #Recuperar Ativos que são necessários para a restrição
        ativos = ParsingMemoriaCalculo.tabela_texto_memoria_para_df(row['MemoriaCalculo'])['NOME'] #Teremos que tratar para termos o nome igual da ordem
        
        #Extraindo Indices dos ativos para serem passados para o gerador de restrição
        indices_ativos = indices_ativos(ordem,row['fundo'],ativos)
        
        #Gera Restrição
        restricao = gerar_restricao(row['descricao'],indices_ativos,row['saldo_base'],row['exposicao'],row['l_max'],row['l_min'])
        restricao = restricao[:13]+"_" + i +restricao[13:] #Adicionando um numerador na restrição
        
        # Dicionário para capturar a função definida dinamicamente
        local_scope = {}
        exec(restricao_codigo, globals(), local_scope)
        
        # Recuperar a função criada
        nome_funcao = f"restricao_{i}"
        restricao_func = local_scope[nome_funcao]

        restricoes.append({'type':'ineq','fun':restricao_func})    

    #Definindo função objetivo
    def objetivo(x,ordem_ideal):
        y = np.abs(x -regua_ideal['percentual_alocacao']).sum()
        return y

    #Realizar minimização
    minimizador = scipy.optimize.minimize(
        fun=objetivo,
        x0=ordem,
        args=(regua_ideal),
        constraints=restricoes,
        bounds= bounds,
        method='SLSQP',
        options={'maxiter': 100000,'disp':False}
    )

    ordem_otimizada = minimizador.x


if __name__ == "__main__":
    ExecutarOtimização()