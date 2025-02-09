from io import StringIO
import pandas as pd
from itertools import groupby


def __chega_final_texto(texto_memoria:str)->str:
    index1 = texto_memoria.find("MEMÓRIA DE CÁLCULO (PROCESSAMENTO)") #index do final da string, perto das colunas
    index_coluna = texto_memoria.find("TÍTULO",index1) #index da primeira coluna (TITULO)
    texto_final = texto_memoria[index_coluna:]

    linhas = texto_final.splitlines()
    apenas_linhas_dados = "\n".join(linhas[2:]) #pula linha de coluna e linhas tracejadas

    return apenas_linhas_dados


def tabela_texto_memoria_para_df(texto:str)->pd.DataFrame:
  
    final_texto = __chega_final_texto(texto).strip() #chega no final da string, onde tem as colunas de dados da memória
    #print(final_texto)
    colspecs = [
        (0, 20),   # TÍTULO
        (21, 51),  # NOME
        (52, 72),  # POSIÇÃO
        (73, 83),  # %PL
        (84, 144), # GRUPO
        (144, None) # EMISSOR 
    ]

    # Cehca se o input não é vazio
    if final_texto:
        # checa se o input é uma única linha
        if len(final_texto.splitlines()) == 1:
            data = [final_texto[start:end].strip() for start, end in colspecs]
            df = pd.DataFrame([data], columns=["TÍTULO", "NOME", "POSIÇÃO", "%PL", "GRUPO", "EMISSOR"])
        else:
            df = pd.read_fwf(
                StringIO(final_texto),
                colspecs=colspecs,
            )
            df.columns = ["TÍTULO", "NOME", "POSIÇÃO", "%PL", "GRUPO", "EMISSOR"]
        df = df.apply(lambda col: col.str.strip())

        def para_float_br(x):
            return float(x.replace('.', '').replace(',', '.'))

        df["POSIÇÃO"] = df["POSIÇÃO"].apply(para_float_br)
        df["%PL"] = df["%PL"].apply(para_float_br)

        #display(df)
        return df
    else:
        print("The dataset is empty.")


def get_desenquadramento_rating(text:str)->list[dict]:
    """
    Dado a string da memória de cálculo, faz o loop pelo veredito de cada ativo na alocação e retorna uma lista de dicts para os ativos desenquadrados, para cada dict temos o nome do ativo,
    o pior rating permitido no fundo, o rating do ativo e a posição dele no fundo como chaves.

    Args:
        text (str): texto do cálculo de memória
    
    Return:
        list[dict]: lista de dicts com os ativos desenquadrados, caada ativo com seu dict e informações mencionadas anteriormente.
    """
    split_por_ativo = text.split("TITULO:")[1:] #separa por análise de cada ativo
    ultima_chunk = split_por_ativo[-1]
    split_por_ativo[-1] = ultima_chunk[:ultima_chunk.find("MEMÓRIA DE CÁLCULO (PROCESSAMENTO)")] #ultima chunk tem a tabela dos dados, vamos tirar ela
    resultado_desenquadramento = []    #lista de dicts
    
    for i,chunk in enumerate(split_por_ativo): #loop pelos vereditos individuais para cada ativo 
        icomeco_ativo = chunk.find("DEBN") + 4
        ifinal_ativo = chunk.find("/")
        ativo = chunk[icomeco_ativo:ifinal_ativo].strip()
        comeco_string_veredito = chunk.find("[")
        veredito = chunk[comeco_string_veredito:].strip()
      
        if "DESCONSIDERADO"  not in veredito: #ativo desequadrou
            #print(veredito + " ---- "+ str(i))
            #print(ativo)
            pior_rating_agencia = None
            rating_ativo = None
            numeros_linha = []
            for  eh_numero,grupo in groupby(veredito, key=lambda x: x.isnumeric() or x == "." or x == ","): #agrupa substrs da linha entre as de números e as que n são numeros
                if eh_numero:
                    numeros_linha.append("".join(grupo))
            
            #print(numeros_linha)
            resultado_desenquadramento.append(
                {
                    "ativo":ativo,
                    "pior_rating_permitido": int(numeros_linha[0]), #maior número == pior rating
                    "rating do ativo": int(numeros_linha[1]),
                    "posicao_ativo": float(numeros_linha[2].replace(".","").replace(",",""))
                }
            )
        else:
            continue
    
    return resultado_desenquadramento


def agrupa_ativos(txt:str)->dict:
    """
    Várias memórias de cálculo do nexxus tem um agrupamento de ativos da seguinte forma:
    ============================
    ==      Classe ativo      ==
    ============================

    Ativo 1

    Ativo 2

    ============================
    ==   outra Classe ativo   ==
    ============================
    ....

    O objetivo dessa função é agrupar os ativos em cada classe, retornando um dict com a chave sendo o nome da classe e o valor uma lista de ativos que entram nesse caso.

    Return:
        dict[str,list]: dict cuja key é o nome do agrupamento e o valor uma lista de ativos agrupados nele
    """

    linhas = txt.splitlines() 
    resultado = {}
    i = 0

    while i < len(linhas):
        linha_atual = linhas[i].strip() #tirar whitespace do começo e final
        # Se a linha estiver vazia, pula para a próxima
        if not linha_atual:
            i += 1 
            continue

        # Verifica se a linha é um separador (composta somente pelo caractere "=")
        if set(linha_atual) == {"="}:
            # Verifica se há linhas suficientes para obter o cabeçalho da classe e o separador seguinte
            if i + 2 >= len(linhas):
                break

            # A linha seguinte deve conter o nome da classe, envolvido por "=="
            linha_classe = linhas[i + 1].strip()
            if linha_classe.startswith("==") and linha_classe.endswith("=="):
                # Remove os "==" do início e fim e os espaços laterais
                nome_classe = linha_classe[2:-2].strip()
            else:
                nome_classe = linha_classe.strip()

            # Pula o separador, a linha de classe e o segundo separador
            i += 3

            ativos = []
            # Coleta os ativos até encontrar uma nova linha de separador ou o fim do texto
            while i < len(linhas):
                linha_ativo = linhas[i].strip()
                # Se encontrar uma linha de separador, encerra o bloco atual
                if linha_ativo and set(linha_ativo) == {"="}:
                    break
                if linha_ativo: #linha não tem == e não é vazia
                    if linha_ativo == 'MEMÓRIA DE CÁLCULO (PROCESSAMENTO)': #chegamos no final da primeira parte da memória calculo, depois vai ser a tabela
                        #print("final")
                        resultado[nome_classe] = ativos
                        return resultado #retorna resultado até agora
                    ativos.append(linha_ativo)
                i += 1 #se linha for vazia, pula apenas

            resultado[nome_classe] = ativos
        else:
            i += 1

    return resultado

if __name__ == "__main__":
   
    txt = """
   MEMÓRIA DE CÁLCULO (PROCESSAMENTO)
----------------------------------

TÍTULO               NOME                           POSIÇÃO              %PL        GRUPO                                                        EMISSOR
-------------------- ------------------------------ -------------------- ---------- ------------------------------------------------------------ ------------------------------------------------------------
DEBN AEGPA0_052029   DEBN AEGPA0 H750651                      279.245,48       0,01 10440 - Títulos Privados-Debêntures Incent. (Lei 12.431)     AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN AEGPA3_032026   DEBN AEGPA3 I109165                    5.416.180,06       0,29 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN CMPH14_112028   DEBN CMPH14 I559118                      338.894,03       0,02 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN CMPH14_112028   DEBN CMPH14 I559118                      844.077,69       0,04 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN CMPH14_112028   DEBN CMPH14 I559118                    3.280.536,37       0,17 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN CMPH14_112028   DEBN CMPH14 I559118                        6.841,03       0,00 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN DASAA4_102025   DEBN DASAA4                            2.581.682,18       0,14 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAA4_102025   DEBN DASAA4                           15.021.707,95       0,80 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAA4_102025   DEBN DASAA4                            3.799.180,03       0,20 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAA4_102025   DEBN DASAA4                            1.496.707,99       0,08 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAA4_102025   DEBN DASAA4                               62.721,12       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAA4_102025   DEBN DASAA4                            3.796.145,13       0,20 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN AEGPA3_032026   DEBN AEGPA3 I109165                    1.779.495,60       0,09 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN DASAA4_102025   DEBN DASAA4                               28.325,67       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAA5_102026   DEBN DASAA5_102026                     2.746.779,26       0,15 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAA6_042027   DEBN DASAA6 H979858                    7.911.659,78       0,42 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAA6_042027   DEBN DASAA6 H979858                       26.934,47       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAA6_042027   DEBN DASAA6 H979858                   14.472.465,65       0,77 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAA6_042027   DEBN DASAA6 H979858                    1.405.401,95       0,07 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAA6_042027   DEBN DASAA6 H979858                    3.568.816,72       0,19 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAA6_042027   DEBN DASAA6 H979858                    2.526.068,12       0,13 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAA6_042027   DEBN DASAA6 H979858                       61.564,49       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAA6_042027   DEBN DASAA6 H979858                    3.562.083,11       0,19 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN AEGPA3_032026   DEBN AEGPA3 I109165                       88.336,20       0,00 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN DASAA6_042027   DEBN DASAA6 H979858                    4.737.400,54       0,25 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAA8_102027   DEBN DASAA8 I338851                    5.320.979,70       0,28 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAA8_102027   DEBN DASAA8 I338851                       57.786,08       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAA8_102027   DEBN DASAA8 I338851                    8.208.419,72       0,44 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAA8_102027   DEBN DASAA8 I338851                      123.960,47       0,01 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAA8_102027   DEBN DASAA8 I338851                   28.852.031,44       1,53 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAA8_102027   DEBN DASAA8 I338851                    8.103.099,93       0,43 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAA8_102027   DEBN DASAA8 I338851                    3.206.195,51       0,17 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAB4_102027   DEBN DASAB4                               18.247,06       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAB4_102027   DEBN DASAB4                            1.025.676,90       0,05 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN AEGPA3_032026   DEBN AEGPA3 I109165                   18.233.444,07       0,97 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN DASAB4_102027   DEBN DASAB4                              773.099,16       0,04 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAB4_102027   DEBN DASAB4                                8.643,34       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAB4_102027   DEBN DASAB4                            1.024.716,53       0,05 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAB4_102027   DEBN DASAB4                            4.842.193,76       0,26 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAB4_102027   DEBN DASAB4                              403.356,08       0,02 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAB5_102028   DEBN DASAB5 H911988                      580.066,95       0,03 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAB5_102028   DEBN DASAB5 H911988                      229.286,30       0,01 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAB5_102028   DEBN DASAB5 H911988                    2.126.607,64       0,11 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAB5_102028   DEBN DASAB5 H911988                        4.567,46       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAB5_102028   DEBN DASAB5 H911988                      690.599,39       0,04 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN AEGPA7_092026   DEBN AEGPA7 I445412                      331.951,35       0,02 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN DASAB5_102028   DEBN DASAB5 H911988                       10.048,40       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAB5_102028   DEBN DASAB5 H911988                      587.374,88       0,03 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAB5_102028   DEBN DASAB5 H911988                      400.109,18       0,02 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAC5_102031   DEBN DASAC5 H910152                   13.905.847,16       0,74 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAC5_102031   DEBN DASAC5 H910152                      436.642,39       0,02 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAC5_102031   DEBN DASAC5 H910152                        4.331,77       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAC5_102031   DEBN DASAC5 H910152                      686.152,32       0,04 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAC5_102031   DEBN DASAC5 H910152                       10.396,25       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAC5_102031   DEBN DASAC5 H910152                    1.740.505,07       0,09 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAC5_102031   DEBN DASAC5 H910152                    1.497.059,62       0,08 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN AEGPA7_092026   DEBN AEGPA7 I445412                    3.396.117,73       0,18 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN GUAR16_102027   DEBN GUAR16 I488305                       82.311,61       0,00 10403 - Títulos Privados-Debêntures simples                  GUAR - GUARARAPES CONFECCOES SA (EX CONFECCOES GUARARAPES   
DEBN GUAR16_102027   DEBN GUAR16 I488305                       34.383,33       0,00 10403 - Títulos Privados-Debêntures simples                  GUAR - GUARARAPES CONFECCOES SA (EX CONFECCOES GUARARAPES   
DEBN GUAR16_102027   DEBN GUAR16 I488305                   14.496.220,03       0,77 10403 - Títulos Privados-Debêntures simples                  GUAR - GUARARAPES CONFECCOES SA (EX CONFECCOES GUARARAPES   
DEBN MGLUA0_102026   DEBN MGLUA0 I338896                    2.109.810,03       0,11 10403 - Títulos Privados-Debêntures simples                  MGLU - MAGAZINE LUIZA SA                                    
DEBN MGLUA0_102026   DEBN MGLUA0 I338896                    1.086.961,50       0,06 10403 - Títulos Privados-Debêntures simples                  MGLU - MAGAZINE LUIZA SA                                    
DEBN MGLUA0_102026   DEBN MGLUA0 I338896                   45.510.348,27       2,42 10403 - Títulos Privados-Debêntures simples                  MGLU - MAGAZINE LUIZA SA                                    
DEBN MGLUA0_102026   DEBN MGLUA0 I338896                    1.383.853,89       0,07 10403 - Títulos Privados-Debêntures simples                  MGLU - MAGAZINE LUIZA SA                                    
DEBN MGLUA0_102026   DEBN MGLUA0 I338896                      422.159,28       0,02 10403 - Títulos Privados-Debêntures simples                  MGLU - MAGAZINE LUIZA SA                                    
DEBN MGLUA0_102026   DEBN MGLUA0 I338896                    1.886.894,15       0,10 10403 - Títulos Privados-Debêntures simples                  MGLU - MAGAZINE LUIZA SA                                    
DEBN MGLUA0_102026   DEBN MGLUA0 I338896                      580.962,18       0,03 10403 - Títulos Privados-Debêntures simples                  MGLU - MAGAZINE LUIZA SA                                    
DEBN AEGPA7_092026   DEBN AEGPA7 I445412                        7.447,63       0,00 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN MGLUA0_102026   DEBN MGLUA0 I338896                    2.465.883,63       0,13 10403 - Títulos Privados-Debêntures simples                  MGLU - MAGAZINE LUIZA SA                                    
DEBN MGLUA0_102026   DEBN MGLUA0 I338896                    2.737.130,83       0,15 10403 - Títulos Privados-Debêntures simples                  MGLU - MAGAZINE LUIZA SA                                    
DEBN MGLUA0_102026   DEBN MGLUA0 I338896                      202.202,46       0,01 10403 - Títulos Privados-Debêntures simples                  MGLU - MAGAZINE LUIZA SA                                    
DEBN MGLUA0_102026   DEBN MGLUA0 I338896                   25.276.293,56       1,34 10403 - Títulos Privados-Debêntures simples                  MGLU - MAGAZINE LUIZA SA                                    
DEBN MGLUA0_102026   DEBN MGLUA0 I338896                       93.703,58       0,00 10403 - Títulos Privados-Debêntures simples                  MGLU - MAGAZINE LUIZA SA                                    
DEBN MGLUA0_102026   DEBN MGLUA0 I338896                   17.437.742,68       0,93 10403 - Títulos Privados-Debêntures simples                  MGLU - MAGAZINE LUIZA SA                                    
DEBN MGLUA0_102026   DEBN MGLUA0 I338896                   17.626.136,19       0,94 10403 - Títulos Privados-Debêntures simples                  MGLU - MAGAZINE LUIZA SA                                    
DEBN MGLUA0_102026   DEBN MGLUA0 I338896                    2.147.291,47       0,11 10403 - Títulos Privados-Debêntures simples                  MGLU - MAGAZINE LUIZA SA                                    
DEBN MGLUA0_102026   DEBN MGLUA0 I338896                    3.018.241,56       0,16 10403 - Títulos Privados-Debêntures simples                  MGLU - MAGAZINE LUIZA SA                                    
DEBN MGLUA0_102026   DEBN MGLUA0 I338896                      708.201,78       0,04 10403 - Títulos Privados-Debêntures simples                  MGLU - MAGAZINE LUIZA SA                                    
DEBN AEGPA7_092026   DEBN AEGPA7 I445412                       15.959,20       0,00 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN MRVEB2_072025   DEBN MRVEB2 I650257                      935.279,07       0,05 10403 - Títulos Privados-Debêntures simples                  MRVE - MRV ENGENHARIA PARTICIPACOES SA                      
DEBN MRVEB2_072025   DEBN MRVEB2 I650257                      283.111,50       0,02 10403 - Títulos Privados-Debêntures simples                  MRVE - MRV ENGENHARIA PARTICIPACOES SA                      
DEBN MRVEB2_072025   DEBN MRVEB2 I650257                        5.055,56       0,00 10403 - Títulos Privados-Debêntures simples                  MRVE - MRV ENGENHARIA PARTICIPACOES SA                      
DEBN MRVEB2_072025   DEBN MRVEB2 I650257                      247.722,56       0,01 10403 - Títulos Privados-Debêntures simples                  MRVE - MRV ENGENHARIA PARTICIPACOES SA                      
DEBN MRVEB2_072025   DEBN MRVEB2 I650257                      101.111,25       0,01 10403 - Títulos Privados-Debêntures simples                  MRVE - MRV ENGENHARIA PARTICIPACOES SA                      
DEBN PSAN11_092025   DEBN PSAN11 I504450                   62.733.796,80       3,33 10403 - Títulos Privados-Debêntures simples                  PSAN - PARSAN S.A.                                          
DEBN PSAN11_092025   DEBN PSAN11 I504450                      313.451,90       0,02 10403 - Títulos Privados-Debêntures simples                  PSAN - PARSAN S.A.                                          
DEBN RBRA26_122027   DEBN RBRA26 I576091                   28.244.046,37       1,50 10403 - Títulos Privados-Debêntures simples                  RBRA - OPEA SECURITIZADORA S.A.                             
DEBN RBRA26_122027   DEBN RBRA26 I576091                      509.699,39       0,03 10403 - Títulos Privados-Debêntures simples                  RBRA - OPEA SECURITIZADORA S.A.                             
DEBN RBRA26_122027   DEBN RBRA26 I576091                   70.990.595,75       3,77 10403 - Títulos Privados-Debêntures simples                  RBRA - OPEA SECURITIZADORA S.A.                             
DEBN AEGPA7_092026   DEBN AEGPA7 I445412                    1.009.685,38       0,05 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN RBRA26_122027   DEBN RBRA26 I576091                   26.988.941,54       1,43 10403 - Títulos Privados-Debêntures simples                  RBRA - OPEA SECURITIZADORA S.A.                             
DEBN RBRA26_122027   DEBN RBRA26 I576091                      849.498,98       0,05 10403 - Títulos Privados-Debêntures simples                  RBRA - OPEA SECURITIZADORA S.A.                             
DEBN RBRA26_122027   DEBN RBRA26 I576091                    8.128.867,70       0,43 10403 - Títulos Privados-Debêntures simples                  RBRA - OPEA SECURITIZADORA S.A.                             
DEBN RBRA26_122027   DEBN RBRA26 I576091                   50.252.052,33       2,67 10403 - Títulos Privados-Debêntures simples                  RBRA - OPEA SECURITIZADORA S.A.                             
DEBN SBFC12_052025   DEBN SBFC12 I168246                        3.098,55       0,00 10403 - Títulos Privados-Debêntures simples                  SBFC - SBF COMERCIO DE PRODUTOS ESPORTIVOS S.A.             
DEBN SBFC12_052025   DEBN SBFC12 I168246                       13.082,75       0,00 10403 - Títulos Privados-Debêntures simples                  SBFC - SBF COMERCIO DE PRODUTOS ESPORTIVOS S.A.             
DEBN SBFC12_052025   DEBN SBFC12 I168246                    2.448.883,93       0,13 10403 - Títulos Privados-Debêntures simples                  SBFC - SBF COMERCIO DE PRODUTOS ESPORTIVOS S.A.             
DEBN SBFC12_052025   DEBN SBFC12 I168246                      380.088,27       0,02 10403 - Títulos Privados-Debêntures simples                  SBFC - SBF COMERCIO DE PRODUTOS ESPORTIVOS S.A.             
DEBN SBFC12_052025   DEBN SBFC12 I168246                      114.301,91       0,01 10403 - Títulos Privados-Debêntures simples                  SBFC - SBF COMERCIO DE PRODUTOS ESPORTIVOS S.A.             
DEBN SBFC12_052025   DEBN SBFC12 I168246                        6.541,37       0,00 10403 - Títulos Privados-Debêntures simples                  SBFC - SBF COMERCIO DE PRODUTOS ESPORTIVOS S.A.             
DEBN AEGPA7_092026   DEBN AEGPA7 I445412                    6.534.760,38       0,35 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN SBFC12_052025   DEBN SBFC12 I168246                    1.446.676,54       0,08 10403 - Títulos Privados-Debêntures simples                  SBFC - SBF COMERCIO DE PRODUTOS ESPORTIVOS S.A.             
DEBN SBFC12_052025   DEBN SBFC12 I168246                      386.629,64       0,02 10403 - Títulos Privados-Debêntures simples                  SBFC - SBF COMERCIO DE PRODUTOS ESPORTIVOS S.A.             
DEBN URBS17_032029   DEBN URBS17 I705514                       52.412,28       0,00 10403 - Títulos Privados-Debêntures simples                  URBS - URBA DESENVOLVIMENTO URBANO S.A.                     
DEBN URBS17_032029   DEBN URBS17 I705514                   11.366.127,08       0,60 10403 - Títulos Privados-Debêntures simples                  URBS - URBA DESENVOLVIMENTO URBANO S.A.                     
DEBN URBS17_032029   DEBN URBS17 I705514                   20.964.912,07       1,11 10403 - Títulos Privados-Debêntures simples                  URBS - URBA DESENVOLVIMENTO URBANO S.A.                     
DEBN URBS17_032029   DEBN URBS17 I705514                    2.985.403,48       0,16 10403 - Títulos Privados-Debêntures simples                  URBS - URBA DESENVOLVIMENTO URBANO S.A.                     
DEBN URBS17_032029   DEBN URBS17 I705514                      963.337,71       0,05 10403 - Títulos Privados-Debêntures simples                  URBS - URBA DESENVOLVIMENTO URBANO S.A.                     
DEBN URBS17_032029   DEBN URBS17 I705514                    2.970.728,04       0,16 10403 - Títulos Privados-Debêntures simples                  URBS - URBA DESENVOLVIMENTO URBANO S.A.                     
DEBN VVEO15_072027   DEBN VVEO15 I346092                       87.611,55       0,00 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN VVEO15_072027   DEBN VVEO15 I346092                       98.752,90       0,01 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN AEGPA0_052029   DEBN AEGPA0 H750651                        5.171,21       0,00 10440 - Títulos Privados-Debêntures Incent. (Lei 12.431)     AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN AEGPA7_092026   DEBN AEGPA7 I445412                    1.009.685,38       0,05 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN VVEO15_072027   DEBN VVEO15 I346092                    2.617.711,62       0,14 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN VVEO15_072027   DEBN VVEO15 I346092                       61.783,87       0,00 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN VVEO15_072027   DEBN VVEO15 I346092                    3.615.369,16       0,19 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN VVEO15_072027   DEBN VVEO15 I346092                      120.529,19       0,01 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN VVEO15_072027   DEBN VVEO15 I346092                      604.671,63       0,03 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN VVEO15_072027   DEBN VVEO15 I346092                   14.218.898,99       0,75 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN VVEO15_072027   DEBN VVEO15 I346092                       40.514,01       0,00 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN VVEO15_072027   DEBN VVEO15 I346092                    2.233.841,35       0,12 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN VVEO15_072027   DEBN VVEO15 I346092                       34.436,91       0,00 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN VVEO15_072027   DEBN VVEO15 I346092                    4.949.799,44       0,26 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN AEGPA8_012031   DEBN AEGPA8 I464511                    2.153.215,80       0,11 10440 - Títulos Privados-Debêntures Incent. (Lei 12.431)     AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN VVEO15_072027   DEBN VVEO15 I346092                    1.992.276,54       0,11 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN VVEO15_072027   DEBN VVEO15 I346092                    5.074.886,45       0,27 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN VVEO15_072027   DEBN VVEO15 I346092                    7.135.530,39       0,38 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN VVEO15_072027   DEBN VVEO15 I346092                   19.094.760,36       1,01 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN VVEO16_102027   DEBN VVEO16 I656609                    2.456.716,23       0,13 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN VVEO16_102027   DEBN VVEO16 I656609                      187.558,44       0,01 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN VVEO16_102027   DEBN VVEO16 I656609                    1.968.864,75       0,10 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN VVEO16_102027   DEBN VVEO16 I656609                      637.000,33       0,03 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN VVEO16_102027   DEBN VVEO16 I656609                      227.464,49       0,01 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN VVEO16_102027   DEBN VVEO16 I656609                    2.801.404,72       0,15 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN AEGPA8_012031   DEBN AEGPA8 I464511                      116.390,04       0,01 10440 - Títulos Privados-Debêntures Incent. (Lei 12.431)     AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN VVEO16_102027   DEBN VVEO16 I656609                      621.536,73       0,03 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN VVEO16_102027   DEBN VVEO16 I656609                        5.487,08       0,00 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN VVEO16_102027   DEBN VVEO16 I656609                       11.472,99       0,00 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
LFT 01032027         LFT 01032027                          79.953.279,60       4,24 10106 - Títulos Púb Federais-LFTs-Definitivo                 STNC - SECRETARIA TESOURO NACIONAL                          
LFT 01032027         LFT 01032027                           7.995.327,96       0,42 10106 - Títulos Púb Federais-LFTs-Definitivo                 STNC - SECRETARIA TESOURO NACIONAL                          
LFT 01032027         LFT 01032027                          31.981.311,84       1,70 10106 - Títulos Púb Federais-LFTs-Definitivo                 STNC - SECRETARIA TESOURO NACIONAL                          
LFT 01032027         LFT 01032027                          31.981.311,84       1,70 10106 - Títulos Púb Federais-LFTs-Definitivo                 STNC - SECRETARIA TESOURO NACIONAL                          
LFT 01032028         LFT 01032028 H629313A                 26.005.255,56       1,38 10106 - Títulos Púb Federais-LFTs-Definitivo                 STNC - SECRETARIA TESOURO NACIONAL                          
LFT 01032029         LFT 01032029 K676785A                 10.676.567,72       0,57 10106 - Títulos Púb Federais-LFTs-Definitivo                 STNC - SECRETARIA TESOURO NACIONAL                          
LFT 01032029         LFT 01032029 K676785A                  1.593.517,57       0,08 10106 - Títulos Púb Federais-LFTs-Definitivo                 STNC - SECRETARIA TESOURO NACIONAL                          
DEBN AEGPA8_012031   DEBN AEGPA8 I464511                      352.129,20       0,02 10440 - Títulos Privados-Debêntures Incent. (Lei 12.431)     AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
LFT 01032029         LFT 01032029 K676785A                 95.611.054,25       5,08 10106 - Títulos Púb Federais-LFTs-Definitivo                 STNC - SECRETARIA TESOURO NACIONAL                          
LFT 01032029         LFT 01032029 K676785A                 12.222.279,77       0,65 10106 - Títulos Púb Federais-LFTs-Definitivo                 STNC - SECRETARIA TESOURO NACIONAL                          
DEBN AEGPA8_012031   DEBN AEGPA8 I464511                    1.181.654,84       0,06 10440 - Títulos Privados-Debêntures Incent. (Lei 12.431)     AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN AEGPA8_012031   DEBN AEGPA8 I464511                        2.959,07       0,00 10440 - Títulos Privados-Debêntures Incent. (Lei 12.431)     AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN AEGPA8_012031   DEBN AEGPA8 I464511                        5.918,14       0,00 10440 - Títulos Privados-Debêntures Incent. (Lei 12.431)     AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN AEGPA8_012031   DEBN AEGPA8 I464511                      351.142,84       0,02 10440 - Títulos Privados-Debêntures Incent. (Lei 12.431)     AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN AEGPB7_092028   DEBN AEGPB7 I445418                        7.520,74       0,00 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN AEGPB7_092028   DEBN AEGPB7 I445418                       16.115,87       0,00 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN AEGPA0_052029   DEBN AEGPA0 H750651                      281.313,97       0,01 10440 - Títulos Privados-Debêntures Incent. (Lei 12.431)     AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN AEGPB7_092028   DEBN AEGPB7 I445418                      335.210,13       0,02 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN AEGPB7_092028   DEBN AEGPB7 I445418                    3.429.457,46       0,18 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN AEGPB7_092028   DEBN AEGPB7 I445418                    1.019.597,47       0,05 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN AEGPB7_092028   DEBN AEGPB7 I445418                    6.598.912,21       0,35 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN AEGPB7_092028   DEBN AEGPB7 I445418                    1.019.597,47       0,05 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN BRKPA0_042027   DEBN BRKPA0 H752145                      351.200,59       0,02 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN BRKPA0_042027   DEBN BRKPA0 H752145                      244.586,13       0,01 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN BRKPA0_042027   DEBN BRKPA0 H752145                    4.340.881,11       0,23 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN BRKPA0_042027   DEBN BRKPA0 H752145                    7.359.533,81       0,39 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN BRKPA0_042027   DEBN BRKPA0 H752145                      969.982,58       0,05 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN AEGPA0_052029   DEBN AEGPA0 H750651                       94.116,07       0,00 10440 - Títulos Privados-Debêntures Incent. (Lei 12.431)     AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN BRKPA0_042027   DEBN BRKPA0 H752145                    1.334.771,29       0,07 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN BRKPA0_042027   DEBN BRKPA0 H752145                    5.673.561,93       0,30 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN BRKPA0_042027   DEBN BRKPA0 H752145                    6.404.184,59       0,34 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN BRKPA0_042027   DEBN BRKPA0 H752145                    2.270.260,96       0,12 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN BRKPA0_042027   DEBN BRKPA0 H752145                    4.831.098,61       0,26 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN BRKPA0_042027   DEBN BRKPA0 H752145                       79.438,23       0,00 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN BRKPA0_042027   DEBN BRKPA0 H752145                    4.807.058,09       0,26 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN BRKPA0_042027   DEBN BRKPA0 H752145                   16.582.730,29       0,88 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN BRKPA0_042027   DEBN BRKPA0 H752145                    1.602.352,70       0,09 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN BRKPA0_042027   DEBN BRKPA0 H752145                       35.538,16       0,00 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN AEGPA0_052029   DEBN AEGPA0 H750651                    1.925.759,58       0,10 10440 - Títulos Privados-Debêntures Incent. (Lei 12.431)     AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN BRKPA1_032028   DEBN BRKPA1 I128038                    1.646.767,87       0,09 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN BRKPA1_032028   DEBN BRKPA1 I128038                       13.043,71       0,00 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN BRKPA1_032028   DEBN BRKPA1 I128038                       29.348,34       0,00 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN BRKPA1_032028   DEBN BRKPA1 I128038                    1.480.460,62       0,08 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN BRKPA1_032028   DEBN BRKPA1 I128038                      553.270,52       0,03 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN BRKPA1_032028   DEBN BRKPA1 I128038                    6.313.153,66       0,34 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN BRKPA1_032028   DEBN BRKPA1 I128038                       95.653,85       0,01 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN BRKPA1_032028   DEBN BRKPA1 I128038                    2.147.863,57       0,11 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN BRKPA1_032028   DEBN BRKPA1 I128038                      853.275,76       0,05 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN BRKPA1_032028   DEBN BRKPA1 I128038                    2.508.739,44       0,13 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN AEGPA0_052029   DEBN AEGPA0 H750651                        2.068,49       0,00 10440 - Títulos Privados-Debêntures Incent. (Lei 12.431)     AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN BRKPA1_032028   DEBN BRKPA1 I128038                    1.934.816,38       0,10 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN BRKPA1_032028   DEBN BRKPA1 I128038                    1.086.975,49       0,06 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN BRKPA1_032028   DEBN BRKPA1 I128038                      331.527,53       0,02 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN BRKPA1_032028   DEBN BRKPA1 I128038                      455.442,73       0,02 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN BRKPA1_032028   DEBN BRKPA1 I128038                    1.640.246,02       0,09 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN BVPL11_092028   DEBN BVPL11 I636945                       46.665,52       0,00 10403 - Títulos Privados-Debêntures simples                  BVPL - BORRACHAS VIPAL SA                                   
DEBN BVPL11_092028   DEBN BVPL11 I636945                      107.971,20       0,01 10403 - Títulos Privados-Debêntures simples                  BVPL - BORRACHAS VIPAL SA                                   
DEBN BVPL11_092028   DEBN BVPL11 I636945                   12.163.230,72       0,65 10403 - Títulos Privados-Debêntures simples                  BVPL - BORRACHAS VIPAL SA                                   
DEBN CEAB11_052025   DEBN CEAB11 I156897                       28.906,72       0,00 10403 - Títulos Privados-Debêntures simples                  CEAB - C&A MODAS S.A.                                       
DEBN CEAB11_052025   DEBN CEAB11 I156897                    4.049.005,84       0,21 10403 - Títulos Privados-Debêntures simples                  CEAB - C&A MODAS S.A.                                       
DEBN AEGPA0_052029   DEBN AEGPA0 H750651                      992.872,83       0,05 10440 - Títulos Privados-Debêntures Incent. (Lei 12.431)     AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN CEAB11_052025   DEBN CEAB11 I156897                   11.471.322,89       0,61 10403 - Títulos Privados-Debêntures simples                  CEAB - C&A MODAS S.A.                                       
DEBN CEAB11_052025   DEBN CEAB11 I156897                      955.470,40       0,05 10403 - Títulos Privados-Debêntures simples                  CEAB - C&A MODAS S.A.                                       
DEBN CEAB11_052025   DEBN CEAB11 I156897                      897.656,95       0,05 10403 - Títulos Privados-Debêntures simples                  CEAB - C&A MODAS S.A.                                       
DEBN CEAB11_052025   DEBN CEAB11 I156897                    9.925.845,64       0,53 10403 - Títulos Privados-Debêntures simples                  CEAB - C&A MODAS S.A.                                       
DEBN CEAB11_052025   DEBN CEAB11 I156897                   12.991.506,73       0,69 10403 - Títulos Privados-Debêntures simples                  CEAB - C&A MODAS S.A.                                       
DEBN CEAB11_052025   DEBN CEAB11 I156897                    1.327.644,44       0,07 10403 - Títulos Privados-Debêntures simples                  CEAB - C&A MODAS S.A.                                       
DEBN CEAB11_052025   DEBN CEAB11 I156897                      163.632,69       0,01 10403 - Títulos Privados-Debêntures simples                  CEAB - C&A MODAS S.A.                                       
DEBN CEAB11_052025   DEBN CEAB11 I156897                    4.082.558,28       0,22 10403 - Títulos Privados-Debêntures simples                  CEAB - C&A MODAS S.A.                                       
DEBN CEAB11_052025   DEBN CEAB11 I156897                       62.975,36       0,00 10403 - Títulos Privados-Debêntures simples                  CEAB - C&A MODAS S.A.                                       
DEBN CEAB11_052025   DEBN CEAB11 I156897                    1.385.457,89       0,07 10403 - Títulos Privados-Debêntures simples                  CEAB - C&A MODAS S.A.                                       
DEBN AEGPA3_032026   DEBN AEGPA3 I109165                    5.377.865,57       0,29 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN CEAB12_112025   DEBN CEAB12 I590347                        9.303,09       0,00 10403 - Títulos Privados-Debêntures simples                  CEAB - C&A MODAS S.A.                                       
DEBN CEAB12_112025   DEBN CEAB12 I590347                       19.639,85       0,00 10403 - Títulos Privados-Debêntures simples                  CEAB - C&A MODAS S.A.                                       
DEBN CEAB12_112025   DEBN CEAB12 I590347                    1.143.246,11       0,06 10403 - Títulos Privados-Debêntures simples                  CEAB - C&A MODAS S.A.                                       
DEBN CEAB12_112025   DEBN CEAB12 I590347                      381.426,59       0,02 10403 - Títulos Privados-Debêntures simples                  CEAB - C&A MODAS S.A.                                       
DEBN CEAB12_112025   DEBN CEAB12 I590347                    4.330.070,51       0,23 10403 - Títulos Privados-Debêntures simples                  CEAB - C&A MODAS S.A.                                       
DEBN CEAB12_112025   DEBN CEAB12 I590347                    3.293.293,06       0,17 10403 - Títulos Privados-Debêntures simples                  CEAB - C&A MODAS S.A.                                       
DEBN CEAB12_112025   DEBN CEAB12 I590347                    3.336.707,46       0,18 10403 - Títulos Privados-Debêntures simples                  CEAB - C&A MODAS S.A.                                       
DEBN CEAB12_112025   DEBN CEAB12 I590347                    1.172.189,05       0,06 10403 - Títulos Privados-Debêntures simples                  CEAB - C&A MODAS S.A.                                       
DEBN CEAB22_052028   DEBN CEAB22 I514841                       14.561,06       0,00 10403 - Títulos Privados-Debêntures simples                  CEAB - C&A MODAS S.A.                                       
DEBN CEAB22_052028   DEBN CEAB22 I514841                        6.240,45       0,00 10403 - Títulos Privados-Debêntures simples                  CEAB - C&A MODAS S.A.                                       
DEBN AEGPA3_032026   DEBN AEGPA3 I109165                   35.869.820,54       1,90 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN CEAB22_052028   DEBN CEAB22 I514841                    2.330.809,41       0,12 10403 - Títulos Privados-Debêntures simples                  CEAB - C&A MODAS S.A.                                       
DEBN CEDO13_072029   DEBN CEDO13 I894317                      264.029,46       0,01 10403 - Títulos Privados-Debêntures simples                  CEDO - CIA FIACAO TECIDOS CEDRO CACHOEIRA                   
DEBN CEDO13_072029   DEBN CEDO13 I894317                   26.794.989,92       1,42 10403 - Títulos Privados-Debêntures simples                  CEDO - CIA FIACAO TECIDOS CEDRO CACHOEIRA                   
DEBN CEDO13_072029   DEBN CEDO13 I894317                   14.820.653,76       0,79 10403 - Títulos Privados-Debêntures simples                  CEDO - CIA FIACAO TECIDOS CEDRO CACHOEIRA                   
DEBN CEDO13_072029   DEBN CEDO13 I894317                       67.007,48       0,00 10403 - Títulos Privados-Debêntures simples                  CEDO - CIA FIACAO TECIDOS CEDRO CACHOEIRA                   
DEBN CMPH14_112028   DEBN CMPH14 I559118                    3.340.526,93       0,18 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN CMPH14_112028   DEBN CMPH14 I559118                      747.777,06       0,04 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN CMPH14_112028   DEBN CMPH14 I559118                       15.260,76       0,00 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN CMPH14_112028   DEBN CMPH14 I559118                    1.981.793,39       0,11 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN CMPH14_112028   DEBN CMPH14 I559118                      851.971,19       0,05 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
"""
    #display(tabela_texto_memoria_para_df(txt))
    #print(agrupa_ativos(txt))
    df = tabela_texto_memoria_para_df(txt)
    df.display()
    

