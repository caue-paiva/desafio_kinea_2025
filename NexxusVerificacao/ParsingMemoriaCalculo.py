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
CRA_020001E5         CRA020001E5 15052026 H858501           9.418.872,89       0,17 10444 - Títulos Privados-Certif.Receb. Agronegócio (CRA)     VIRGO - VIRGO CIA SECURITIZACAO (NOVA DEN: ISEC SECURITIZA  
DEBN AEGPA0_052029   DEBN AEGPA0 H750651                        4.134,06       0,00 10440 - Títulos Privados-Debêntures Incent. (Lei 12.431)     AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN AEGPA7_092026   DEBN AEGPA7 I445412                       12.773,34       0,00 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN CSAN24_052032   DEBN CSAN24 I373524                       30.350,85       0,00 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN24_052032   DEBN CSAN24 I373524                       85.819,64       0,00 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN24_052032   DEBN CSAN24 I373524                    4.947.188,02       0,09 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN24_052032   DEBN CSAN24 I373524                       11.512,39       0,00 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN24_052032   DEBN CSAN24 I373524                       45.002,98       0,00 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN24_052032   DEBN CSAN24 I373524                      778.656,21       0,01 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN24_052032   DEBN CSAN24 I373524                    2.172.702,00       0,04 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN24_052032   DEBN CSAN24 I373524                      217.688,83       0,00 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN24_052032   DEBN CSAN24 I373524                       19.885,04       0,00 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSANB0_062034   DEBN CSANB0 I904589                       26.222,68       0,00 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN AEGPA7_092026   DEBN AEGPA7 I445412                       12.773,34       0,00 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN CSMGA5_122025   DEBN CSMGA5                                8.185,44       0,00 10403 - Títulos Privados-Debêntures simples                  CSMG - CIA SANEAMENTO MINAS GERAIS COPASA MG                
DEBN CSMGA5_122025   DEBN CSMGA5                              185.431,60       0,00 10403 - Títulos Privados-Debêntures simples                  CSMG - CIA SANEAMENTO MINAS GERAIS COPASA MG                
DEBN CSMGA5_122025   DEBN CSMGA5                                4.722,37       0,00 10403 - Títulos Privados-Debêntures simples                  CSMG - CIA SANEAMENTO MINAS GERAIS COPASA MG                
DEBN CSMGA5_122025   DEBN CSMGA5                               50.686,74       0,00 10403 - Títulos Privados-Debêntures simples                  CSMG - CIA SANEAMENTO MINAS GERAIS COPASA MG                
DEBN CSMGA5_122025   DEBN CSMGA5                               11.333,68       0,00 10403 - Títulos Privados-Debêntures simples                  CSMG - CIA SANEAMENTO MINAS GERAIS COPASA MG                
DEBN CSMGA5_122025   DEBN CSMGA5                               11.018,86       0,00 10403 - Títulos Privados-Debêntures simples                  CSMG - CIA SANEAMENTO MINAS GERAIS COPASA MG                
DEBN CSMGA5_122025   DEBN CSMGA5                                5.981,66       0,00 10403 - Títulos Privados-Debêntures simples                  CSMG - CIA SANEAMENTO MINAS GERAIS COPASA MG                
DEBN CSMGA5_122025   DEBN CSMGA5                                  314,82       0,00 10403 - Títulos Privados-Debêntures simples                  CSMG - CIA SANEAMENTO MINAS GERAIS COPASA MG                
DEBN CSMGA5_122025   DEBN CSMGA5                              214.395,45       0,00 10403 - Títulos Privados-Debêntures simples                  CSMG - CIA SANEAMENTO MINAS GERAIS COPASA MG                
DEBN CSMGA5_122025   DEBN CSMGA5                               25.500,78       0,00 10403 - Títulos Privados-Debêntures simples                  CSMG - CIA SANEAMENTO MINAS GERAIS COPASA MG                
DEBN AEGPA7_092026   DEBN AEGPA7 I445412                      317.204,49       0,01 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN CSMGA5_122025   DEBN CSMGA5                              312.305,85       0,01 10403 - Títulos Privados-Debêntures simples                  CSMG - CIA SANEAMENTO MINAS GERAIS COPASA MG                
DEBN CSMGA5_122025   DEBN CSMGA5                               48.482,96       0,00 10403 - Títulos Privados-Debêntures simples                  CSMG - CIA SANEAMENTO MINAS GERAIS COPASA MG                
DEBN CSMGA5_122025   DEBN CSMGA5                                5.981,66       0,00 10403 - Títulos Privados-Debêntures simples                  CSMG - CIA SANEAMENTO MINAS GERAIS COPASA MG                
DEBN CSMGA5_122025   DEBN CSMGA5                               12.278,15       0,00 10403 - Títulos Privados-Debêntures simples                  CSMG - CIA SANEAMENTO MINAS GERAIS COPASA MG                
DEBN CSMGA5_122025   DEBN CSMGA5                               15.426,40       0,00 10403 - Títulos Privados-Debêntures simples                  CSMG - CIA SANEAMENTO MINAS GERAIS COPASA MG                
DEBN CSMGA5_122025   DEBN CSMGA5                                8.500,26       0,00 10403 - Títulos Privados-Debêntures simples                  CSMG - CIA SANEAMENTO MINAS GERAIS COPASA MG                
DEBN CSMGA5_122025   DEBN CSMGA5                               11.333,68       0,00 10403 - Títulos Privados-Debêntures simples                  CSMG - CIA SANEAMENTO MINAS GERAIS COPASA MG                
DEBN CSMGA5_122025   DEBN CSMGA5                                2.833,42       0,00 10403 - Títulos Privados-Debêntures simples                  CSMG - CIA SANEAMENTO MINAS GERAIS COPASA MG                
DEBN CSMGA5_122025   DEBN CSMGA5                               10.389,21       0,00 10403 - Títulos Privados-Debêntures simples                  CSMG - CIA SANEAMENTO MINAS GERAIS COPASA MG                
DEBN CSMGA5_122025   DEBN CSMGA5                                7.870,61       0,00 10403 - Títulos Privados-Debêntures simples                  CSMG - CIA SANEAMENTO MINAS GERAIS COPASA MG                
DEBN AEGPA7_092026   DEBN AEGPA7 I445412                       67.060,01       0,00 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN CSMGA5_122025   DEBN CSMGA5                               18.889,47       0,00 10403 - Títulos Privados-Debêntures simples                  CSMG - CIA SANEAMENTO MINAS GERAIS COPASA MG                
DEBN CSMGA5_122025   DEBN CSMGA5                               14.796,75       0,00 10403 - Títulos Privados-Debêntures simples                  CSMG - CIA SANEAMENTO MINAS GERAIS COPASA MG                
DEBN CSMGA5_122025   DEBN CSMGA5                                2.833,42       0,00 10403 - Títulos Privados-Debêntures simples                  CSMG - CIA SANEAMENTO MINAS GERAIS COPASA MG                
DEBN CSMGA5_122025   DEBN CSMGA5                               19.519,11       0,00 10403 - Títulos Privados-Debêntures simples                  CSMG - CIA SANEAMENTO MINAS GERAIS COPASA MG                
DEBN CSMGA5_122025   DEBN CSMGA5                                5.037,19       0,00 10403 - Títulos Privados-Debêntures simples                  CSMG - CIA SANEAMENTO MINAS GERAIS COPASA MG                
DEBN CSMGA5_122025   DEBN CSMGA5                                3.148,24       0,00 10403 - Títulos Privados-Debêntures simples                  CSMG - CIA SANEAMENTO MINAS GERAIS COPASA MG                
DEBN CSMGA5_122025   DEBN CSMGA5                                8.185,44       0,00 10403 - Títulos Privados-Debêntures simples                  CSMG - CIA SANEAMENTO MINAS GERAIS COPASA MG                
DEBN CSMGA5_122025   DEBN CSMGA5                               10.389,21       0,00 10403 - Títulos Privados-Debêntures simples                  CSMG - CIA SANEAMENTO MINAS GERAIS COPASA MG                
DEBN CSMGA5_122025   DEBN CSMGA5                                2.833,42       0,00 10403 - Títulos Privados-Debêntures simples                  CSMG - CIA SANEAMENTO MINAS GERAIS COPASA MG                
DEBN CSMGA5_122025   DEBN CSMGA5                                9.129,91       0,00 10403 - Títulos Privados-Debêntures simples                  CSMG - CIA SANEAMENTO MINAS GERAIS COPASA MG                
DEBN AEGPA7_092026   DEBN AEGPA7 I445412                       13.837,78       0,00 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN CSMGA5_122025   DEBN CSMGA5                            1.938.059,30       0,03 10403 - Títulos Privados-Debêntures simples                  CSMG - CIA SANEAMENTO MINAS GERAIS COPASA MG                
DEBN CSMGA5_122025   DEBN CSMGA5                                3.777,89       0,00 10403 - Títulos Privados-Debêntures simples                  CSMG - CIA SANEAMENTO MINAS GERAIS COPASA MG                
DEBN CSMGA7_122029   DEBN CSMGA7 I184539A                       8.244,65       0,00 10403 - Títulos Privados-Debêntures simples                  CSMG - CIA SANEAMENTO MINAS GERAIS COPASA MG                
DEBN CSMGA7_122029   DEBN CSMGA7 I184539A                      10.305,81       0,00 10403 - Títulos Privados-Debêntures simples                  CSMG - CIA SANEAMENTO MINAS GERAIS COPASA MG                
DEBN CSMGA7_122029   DEBN CSMGA7 I184539A                       2.061,16       0,00 10403 - Títulos Privados-Debêntures simples                  CSMG - CIA SANEAMENTO MINAS GERAIS COPASA MG                
DEBN CSMGA7_122029   DEBN CSMGA7 I184539A                       5.152,91       0,00 10403 - Títulos Privados-Debêntures simples                  CSMG - CIA SANEAMENTO MINAS GERAIS COPASA MG                
DEBN CSMGA7_122029   DEBN CSMGA7 I184539A                       9.275,23       0,00 10403 - Títulos Privados-Debêntures simples                  CSMG - CIA SANEAMENTO MINAS GERAIS COPASA MG                
DEBN CSMGA7_122029   DEBN CSMGA7 I184539A                      10.305,81       0,00 10403 - Títulos Privados-Debêntures simples                  CSMG - CIA SANEAMENTO MINAS GERAIS COPASA MG                
DEBN CSMGA7_122029   DEBN CSMGA7 I184539A                       8.244,65       0,00 10403 - Títulos Privados-Debêntures simples                  CSMG - CIA SANEAMENTO MINAS GERAIS COPASA MG                
DEBN CSMGA7_122029   DEBN CSMGA7 I184539A                      18.550,46       0,00 10403 - Títulos Privados-Debêntures simples                  CSMG - CIA SANEAMENTO MINAS GERAIS COPASA MG                
DEBN AEGPA7_092026   DEBN AEGPA7 I445412                       14.902,22       0,00 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN CSMGA7_122029   DEBN CSMGA7 I184539A                       6.183,49       0,00 10403 - Títulos Privados-Debêntures simples                  CSMG - CIA SANEAMENTO MINAS GERAIS COPASA MG                
DEBN CSMGA7_122029   DEBN CSMGA7 I184539A                       4.122,32       0,00 10403 - Títulos Privados-Debêntures simples                  CSMG - CIA SANEAMENTO MINAS GERAIS COPASA MG                
DEBN CSMGA7_122029   DEBN CSMGA7 I184539A                       8.244,65       0,00 10403 - Títulos Privados-Debêntures simples                  CSMG - CIA SANEAMENTO MINAS GERAIS COPASA MG                
DEBN CSMGA7_122029   DEBN CSMGA7 I184539A                       3.091,74       0,00 10403 - Títulos Privados-Debêntures simples                  CSMG - CIA SANEAMENTO MINAS GERAIS COPASA MG                
DEBN CSMGA7_122029   DEBN CSMGA7 I184539A                      10.305,81       0,00 10403 - Títulos Privados-Debêntures simples                  CSMG - CIA SANEAMENTO MINAS GERAIS COPASA MG                
DEBN CSMGA7_122029   DEBN CSMGA7 I184539A                      19.581,04       0,00 10403 - Títulos Privados-Debêntures simples                  CSMG - CIA SANEAMENTO MINAS GERAIS COPASA MG                
DEBN CSMGA7_122029   DEBN CSMGA7 I184539A                     189.626,94       0,00 10403 - Títulos Privados-Debêntures simples                  CSMG - CIA SANEAMENTO MINAS GERAIS COPASA MG                
DEBN CSMGA7_122029   DEBN CSMGA7 I184539A                       4.122,32       0,00 10403 - Títulos Privados-Debêntures simples                  CSMG - CIA SANEAMENTO MINAS GERAIS COPASA MG                
DEBN CSMGA7_122029   DEBN CSMGA7 I184539A                      45.345,57       0,00 10403 - Títulos Privados-Debêntures simples                  CSMG - CIA SANEAMENTO MINAS GERAIS COPASA MG                
DEBN CSMGA7_122029   DEBN CSMGA7 I184539A                       4.122,32       0,00 10403 - Títulos Privados-Debêntures simples                  CSMG - CIA SANEAMENTO MINAS GERAIS COPASA MG                
DEBN AEGPA7_092026   DEBN AEGPA7 I445412                       12.773,34       0,00 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN CSMGA7_122029   DEBN CSMGA7 I184539A                     233.941,93       0,00 10403 - Títulos Privados-Debêntures simples                  CSMG - CIA SANEAMENTO MINAS GERAIS COPASA MG                
DEBN CSMGA7_122029   DEBN CSMGA7 I184539A                      11.336,39       0,00 10403 - Títulos Privados-Debêntures simples                  CSMG - CIA SANEAMENTO MINAS GERAIS COPASA MG                
DEBN CSMGA7_122029   DEBN CSMGA7 I184539A                   1.668.510,98       0,03 10403 - Títulos Privados-Debêntures simples                  CSMG - CIA SANEAMENTO MINAS GERAIS COPASA MG                
DEBN CSMGA7_122029   DEBN CSMGA7 I184539A                     671.938,95       0,01 10403 - Títulos Privados-Debêntures simples                  CSMG - CIA SANEAMENTO MINAS GERAIS COPASA MG                
DEBN CSMGA7_122029   DEBN CSMGA7 I184539A                       7.214,07       0,00 10403 - Títulos Privados-Debêntures simples                  CSMG - CIA SANEAMENTO MINAS GERAIS COPASA MG                
DEBN CSMGA7_122029   DEBN CSMGA7 I184539A                       8.244,65       0,00 10403 - Títulos Privados-Debêntures simples                  CSMG - CIA SANEAMENTO MINAS GERAIS COPASA MG                
DEBN CSMGA7_122029   DEBN CSMGA7 I184539A                       2.061,16       0,00 10403 - Títulos Privados-Debêntures simples                  CSMG - CIA SANEAMENTO MINAS GERAIS COPASA MG                
DEBN CSMGA7_122029   DEBN CSMGA7 I184539A                      14.428,14       0,00 10403 - Títulos Privados-Debêntures simples                  CSMG - CIA SANEAMENTO MINAS GERAIS COPASA MG                
DEBN CSMGA7_122029   DEBN CSMGA7 I184539A                       4.122,32       0,00 10403 - Títulos Privados-Debêntures simples                  CSMG - CIA SANEAMENTO MINAS GERAIS COPASA MG                
DEBN CSMGA7_122029   DEBN CSMGA7 I184539A                      13.397,55       0,00 10403 - Títulos Privados-Debêntures simples                  CSMG - CIA SANEAMENTO MINAS GERAIS COPASA MG                
DEBN AEGPA7_092026   DEBN AEGPA7 I445412                        6.386,67       0,00 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN CSMGA7_122029   DEBN CSMGA7 I184539A                       5.152,91       0,00 10403 - Títulos Privados-Debêntures simples                  CSMG - CIA SANEAMENTO MINAS GERAIS COPASA MG                
DEBN CSMGA7_122029   DEBN CSMGA7 I184539A                      13.397,56       0,00 10403 - Títulos Privados-Debêntures simples                  CSMG - CIA SANEAMENTO MINAS GERAIS COPASA MG                
DEBN CSMGA7_122029   DEBN CSMGA7 I184539A                      22.672,79       0,00 10403 - Títulos Privados-Debêntures simples                  CSMG - CIA SANEAMENTO MINAS GERAIS COPASA MG                
DEBN CSMGB6_092026   DEBN CSMGB6 I48493                         6.057,35       0,00 10403 - Títulos Privados-Debêntures simples                  CSMG - CIA SANEAMENTO MINAS GERAIS COPASA MG                
DEBN CSMGB6_092026   DEBN CSMGB6 I48493                       899.240,43       0,02 10403 - Títulos Privados-Debêntures simples                  CSMG - CIA SANEAMENTO MINAS GERAIS COPASA MG                
DEBN CSMGB6_092026   DEBN CSMGB6 I48493                         2.202,67       0,00 10403 - Títulos Privados-Debêntures simples                  CSMG - CIA SANEAMENTO MINAS GERAIS COPASA MG                
DEBN CSMGB6_092026   DEBN CSMGB6 I48493                           550,67       0,00 10403 - Títulos Privados-Debêntures simples                  CSMG - CIA SANEAMENTO MINAS GERAIS COPASA MG                
DEBN CSMGB6_092026   DEBN CSMGB6 I48493                        43.502,75       0,00 10403 - Títulos Privados-Debêntures simples                  CSMG - CIA SANEAMENTO MINAS GERAIS COPASA MG                
DEBN CSMGB6_092026   DEBN CSMGB6 I48493                         2.202,67       0,00 10403 - Títulos Privados-Debêntures simples                  CSMG - CIA SANEAMENTO MINAS GERAIS COPASA MG                
DEBN CSMGB6_092026   DEBN CSMGB6 I48493                         4.405,34       0,00 10403 - Títulos Privados-Debêntures simples                  CSMG - CIA SANEAMENTO MINAS GERAIS COPASA MG                
DEBN AEGPA7_092026   DEBN AEGPA7 I445412                      395.973,40       0,01 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN CSMGB6_092026   DEBN CSMGB6 I48493                         4.956,01       0,00 10403 - Títulos Privados-Debêntures simples                  CSMG - CIA SANEAMENTO MINAS GERAIS COPASA MG                
DEBN CSMGB6_092026   DEBN CSMGB6 I48493                         3.304,01       0,00 10403 - Títulos Privados-Debêntures simples                  CSMG - CIA SANEAMENTO MINAS GERAIS COPASA MG                
DEBN CSMGB6_092026   DEBN CSMGB6 I48493                         1.101,34       0,00 10403 - Títulos Privados-Debêntures simples                  CSMG - CIA SANEAMENTO MINAS GERAIS COPASA MG                
DEBN CSMGB6_092026   DEBN CSMGB6 I48493                         2.753,34       0,00 10403 - Títulos Privados-Debêntures simples                  CSMG - CIA SANEAMENTO MINAS GERAIS COPASA MG                
DEBN CSMGB6_092026   DEBN CSMGB6 I48493                         1.652,00       0,00 10403 - Títulos Privados-Debêntures simples                  CSMG - CIA SANEAMENTO MINAS GERAIS COPASA MG                
DEBN CSMGB6_092026   DEBN CSMGB6 I48493                         1.652,00       0,00 10403 - Títulos Privados-Debêntures simples                  CSMG - CIA SANEAMENTO MINAS GERAIS COPASA MG                
DEBN CSMGB6_092026   DEBN CSMGB6 I48493                         2.202,67       0,00 10403 - Títulos Privados-Debêntures simples                  CSMG - CIA SANEAMENTO MINAS GERAIS COPASA MG                
DEBN CSMGB6_092026   DEBN CSMGB6 I48493                         1.101,34       0,00 10403 - Títulos Privados-Debêntures simples                  CSMG - CIA SANEAMENTO MINAS GERAIS COPASA MG                
DEBN CSMGB6_092026   DEBN CSMGB6 I48493                         1.101,34       0,00 10403 - Títulos Privados-Debêntures simples                  CSMG - CIA SANEAMENTO MINAS GERAIS COPASA MG                
DEBN CSMGB6_092026   DEBN CSMGB6 I48493                         2.202,67       0,00 10403 - Títulos Privados-Debêntures simples                  CSMG - CIA SANEAMENTO MINAS GERAIS COPASA MG                
DEBN AEGPA7_092026   DEBN AEGPA7 I445412                      487.515,64       0,01 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN CSMGB6_092026   DEBN CSMGB6 I48493                         2.202,67       0,00 10403 - Títulos Privados-Debêntures simples                  CSMG - CIA SANEAMENTO MINAS GERAIS COPASA MG                
DEBN CSMGB6_092026   DEBN CSMGB6 I48493                         1.652,00       0,00 10403 - Títulos Privados-Debêntures simples                  CSMG - CIA SANEAMENTO MINAS GERAIS COPASA MG                
DEBN CSMGB6_092026   DEBN CSMGB6 I48493                         2.753,34       0,00 10403 - Títulos Privados-Debêntures simples                  CSMG - CIA SANEAMENTO MINAS GERAIS COPASA MG                
DEBN CSMGB6_092026   DEBN CSMGB6 I48493                         5.506,67       0,00 10403 - Títulos Privados-Debêntures simples                  CSMG - CIA SANEAMENTO MINAS GERAIS COPASA MG                
DEBN CSMGB6_092026   DEBN CSMGB6 I48493                         2.202,67       0,00 10403 - Títulos Privados-Debêntures simples                  CSMG - CIA SANEAMENTO MINAS GERAIS COPASA MG                
DEBN CSMGB6_092026   DEBN CSMGB6 I48493                         2.753,34       0,00 10403 - Títulos Privados-Debêntures simples                  CSMG - CIA SANEAMENTO MINAS GERAIS COPASA MG                
DEBN CSMGB6_092026   DEBN CSMGB6 I48493                           550,67       0,00 10403 - Títulos Privados-Debêntures simples                  CSMG - CIA SANEAMENTO MINAS GERAIS COPASA MG                
DEBN CSMGB6_092026   DEBN CSMGB6 I48493                           550,67       0,00 10403 - Títulos Privados-Debêntures simples                  CSMG - CIA SANEAMENTO MINAS GERAIS COPASA MG                
DEBN CSMGB6_092026   DEBN CSMGB6 I48493                         1.101,34       0,00 10403 - Títulos Privados-Debêntures simples                  CSMG - CIA SANEAMENTO MINAS GERAIS COPASA MG                
DEBN CSMGB6_092026   DEBN CSMGB6 I48493                           550,67       0,00 10403 - Títulos Privados-Debêntures simples                  CSMG - CIA SANEAMENTO MINAS GERAIS COPASA MG                
DEBN AEGPA0_052029   DEBN AEGPA0 H750651                        4.134,06       0,00 10440 - Títulos Privados-Debêntures Incent. (Lei 12.431)     AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN AEGPA7_092026   DEBN AEGPA7 I445412                      147.957,80       0,00 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN CTOL18_022031   DEBN CTOL18 I60163                       224.741,46       0,00 10448 - Titulos Privados-Debêntures SPE                      CTOL - CONCESSIONARIA VIARIO S.A                            
DEBN CTOL18_022031   DEBN CTOL18 I60163                       123.607,80       0,00 10448 - Titulos Privados-Debêntures SPE                      CTOL - CONCESSIONARIA VIARIO S.A                            
DEBN CTOL18_022031   DEBN CTOL18 I60163                       235.978,53       0,00 10448 - Titulos Privados-Debêntures SPE                      CTOL - CONCESSIONARIA VIARIO S.A                            
DEBN CTOL18_022031   DEBN CTOL18 I60163                        79.681,06       0,00 10448 - Titulos Privados-Debêntures SPE                      CTOL - CONCESSIONARIA VIARIO S.A                            
DEBN CTOL18_022031   DEBN CTOL18 I60163                       102.155,21       0,00 10448 - Titulos Privados-Debêntures SPE                      CTOL - CONCESSIONARIA VIARIO S.A                            
DEBN CTOL18_022031   DEBN CTOL18 I60163                        18.387,94       0,00 10448 - Titulos Privados-Debêntures SPE                      CTOL - CONCESSIONARIA VIARIO S.A                            
DEBN CTOL18_022031   DEBN CTOL18 I60163                       229.849,22       0,00 10448 - Titulos Privados-Debêntures SPE                      CTOL - CONCESSIONARIA VIARIO S.A                            
DEBN CTOL18_022031   DEBN CTOL18 I60163                        15.323,28       0,00 10448 - Titulos Privados-Debêntures SPE                      CTOL - CONCESSIONARIA VIARIO S.A                            
DEBN CTOL18_022031   DEBN CTOL18 I60163                       254.366,47       0,00 10448 - Titulos Privados-Debêntures SPE                      CTOL - CONCESSIONARIA VIARIO S.A                            
DEBN CTOL18_022031   DEBN CTOL18 I60163                         7.150,86       0,00 10448 - Titulos Privados-Debêntures SPE                      CTOL - CONCESSIONARIA VIARIO S.A                            
DEBN AEGPA7_092026   DEBN AEGPA7 I445412                       15.966,67       0,00 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN CTOL18_022031   DEBN CTOL18 I60163                        21.452,59       0,00 10448 - Titulos Privados-Debêntures SPE                      CTOL - CONCESSIONARIA VIARIO S.A                            
DEBN CTOL18_022031   DEBN CTOL18 I60163                       476.043,27       0,01 10448 - Titulos Privados-Debêntures SPE                      CTOL - CONCESSIONARIA VIARIO S.A                            
DEBN CTOL18_022031   DEBN CTOL18 I60163                       794.767,52       0,01 10448 - Titulos Privados-Debêntures SPE                      CTOL - CONCESSIONARIA VIARIO S.A                            
DEBN CTOL18_022031   DEBN CTOL18 I60163                         7.150,86       0,00 10448 - Titulos Privados-Debêntures SPE                      CTOL - CONCESSIONARIA VIARIO S.A                            
DEBN CTOL18_022031   DEBN CTOL18 I60163                        87.853,48       0,00 10448 - Titulos Privados-Debêntures SPE                      CTOL - CONCESSIONARIA VIARIO S.A                            
DEBN CTOL18_022031   DEBN CTOL18 I60163                        30.646,56       0,00 10448 - Titulos Privados-Debêntures SPE                      CTOL - CONCESSIONARIA VIARIO S.A                            
DEBN CTOL18_022031   DEBN CTOL18 I60163                        14.301,73       0,00 10448 - Titulos Privados-Debêntures SPE                      CTOL - CONCESSIONARIA VIARIO S.A                            
DEBN CTOL18_022031   DEBN CTOL18 I60163                        17.366,39       0,00 10448 - Titulos Privados-Debêntures SPE                      CTOL - CONCESSIONARIA VIARIO S.A                            
DEBN CTOL18_022031   DEBN CTOL18 I60163                       489.323,44       0,01 10448 - Titulos Privados-Debêntures SPE                      CTOL - CONCESSIONARIA VIARIO S.A                            
DEBN CTOL18_022031   DEBN CTOL18 I60163                        21.452,59       0,00 10448 - Titulos Privados-Debêntures SPE                      CTOL - CONCESSIONARIA VIARIO S.A                            
DEBN AEGPA8_012031   DEBN AEGPA8 I464511                       28.566,59       0,00 10440 - Títulos Privados-Debêntures Incent. (Lei 12.431)     AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN CTOL18_022031   DEBN CTOL18 I60163                       261.517,33       0,00 10448 - Titulos Privados-Debêntures SPE                      CTOL - CONCESSIONARIA VIARIO S.A                            
DEBN CTOL18_022031   DEBN CTOL18 I60163                        14.301,73       0,00 10448 - Titulos Privados-Debêntures SPE                      CTOL - CONCESSIONARIA VIARIO S.A                            
DEBN CTOL18_022031   DEBN CTOL18 I60163                     5.859.622,71       0,10 10448 - Titulos Privados-Debêntures SPE                      CTOL - CONCESSIONARIA VIARIO S.A                            
DEBN CTOL18_022031   DEBN CTOL18 I60163                       784.551,99       0,01 10448 - Titulos Privados-Debêntures SPE                      CTOL - CONCESSIONARIA VIARIO S.A                            
DEBN CTOL18_022031   DEBN CTOL18 I60163                         9.193,97       0,00 10448 - Titulos Privados-Debêntures SPE                      CTOL - CONCESSIONARIA VIARIO S.A                            
DEBN CTOL18_022031   DEBN CTOL18 I60163                        14.301,73       0,00 10448 - Titulos Privados-Debêntures SPE                      CTOL - CONCESSIONARIA VIARIO S.A                            
DEBN CTOL18_022031   DEBN CTOL18 I60163                       839.715,81       0,02 10448 - Titulos Privados-Debêntures SPE                      CTOL - CONCESSIONARIA VIARIO S.A                            
DEBN CTOL18_022031   DEBN CTOL18 I60163                       276.840,61       0,00 10448 - Titulos Privados-Debêntures SPE                      CTOL - CONCESSIONARIA VIARIO S.A                            
DEBN CTOL18_022031   DEBN CTOL18 I60163                     4.622.523,15       0,08 10448 - Titulos Privados-Debêntures SPE                      CTOL - CONCESSIONARIA VIARIO S.A                            
DEBN CTOL18_022031   DEBN CTOL18 I60163                       403.513,07       0,01 10448 - Titulos Privados-Debêntures SPE                      CTOL - CONCESSIONARIA VIARIO S.A                            
DEBN AEGPA8_012031   DEBN AEGPA8 I464511                        8.865,49       0,00 10440 - Títulos Privados-Debêntures Incent. (Lei 12.431)     AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN CTOL18_022031   DEBN CTOL18 I60163                       696.698,52       0,01 10448 - Titulos Privados-Debêntures SPE                      CTOL - CONCESSIONARIA VIARIO S.A                            
DEBN CTOL18_022031   DEBN CTOL18 I60163                     1.552.759,15       0,03 10448 - Titulos Privados-Debêntures SPE                      CTOL - CONCESSIONARIA VIARIO S.A                            
DEBN CTOL18_022031   DEBN CTOL18 I60163                     4.377.350,65       0,08 10448 - Titulos Privados-Debêntures SPE                      CTOL - CONCESSIONARIA VIARIO S.A                            
DEBN CTOL18_022031   DEBN CTOL18 I60163                       134.844,87       0,00 10448 - Titulos Privados-Debêntures SPE                      CTOL - CONCESSIONARIA VIARIO S.A                            
DEBN CTOL18_022031   DEBN CTOL18 I60163                     1.224.840,94       0,02 10448 - Titulos Privados-Debêntures SPE                      CTOL - CONCESSIONARIA VIARIO S.A                            
DEBN CTOL18_022031   DEBN CTOL18 I60163                     1.122.685,72       0,02 10448 - Titulos Privados-Debêntures SPE                      CTOL - CONCESSIONARIA VIARIO S.A                            
DEBN CTOL18_022031   DEBN CTOL18 I60163                     4.338.531,67       0,08 10448 - Titulos Privados-Debêntures SPE                      CTOL - CONCESSIONARIA VIARIO S.A                            
DEBN CTOL18_022031   DEBN CTOL18 I60163                       347.327,71       0,01 10448 - Titulos Privados-Debêntures SPE                      CTOL - CONCESSIONARIA VIARIO S.A                            
DEBN CTOL18_022031   DEBN CTOL18 I60163                     4.026.958,29       0,07 10448 - Titulos Privados-Debêntures SPE                      CTOL - CONCESSIONARIA VIARIO S.A                            
DEBN CTOL18_022031   DEBN CTOL18 I60163                     2.002.242,07       0,04 10448 - Titulos Privados-Debêntures SPE                      CTOL - CONCESSIONARIA VIARIO S.A                            
DEBN AEGPA8_012031   DEBN AEGPA8 I464511                       20.686,15       0,00 10440 - Títulos Privados-Debêntures Incent. (Lei 12.431)     AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN CTOL18_022031   DEBN CTOL18 I60163                     2.345.483,58       0,04 10448 - Titulos Privados-Debêntures SPE                      CTOL - CONCESSIONARIA VIARIO S.A                            
DEBN CTOL18_022031   DEBN CTOL18 I60163                        13.280,18       0,00 10448 - Titulos Privados-Debêntures SPE                      CTOL - CONCESSIONARIA VIARIO S.A                            
DEBN CTOL18_022031   DEBN CTOL18 I60163                       378.995,82       0,01 10448 - Titulos Privados-Debêntures SPE                      CTOL - CONCESSIONARIA VIARIO S.A                            
DEBN CTOL18_022031   DEBN CTOL18 I60163                       774.336,47       0,01 10448 - Titulos Privados-Debêntures SPE                      CTOL - CONCESSIONARIA VIARIO S.A                            
DEBN CTOL18_022031   DEBN CTOL18 I60163                       594.543,31       0,01 10448 - Titulos Privados-Debêntures SPE                      CTOL - CONCESSIONARIA VIARIO S.A                            
DEBN CTOL18_022031   DEBN CTOL18 I60163                        82.745,72       0,00 10448 - Titulos Privados-Debêntures SPE                      CTOL - CONCESSIONARIA VIARIO S.A                            
DEBN CTOL18_022031   DEBN CTOL18 I60163                       120.543,15       0,00 10448 - Titulos Privados-Debêntures SPE                      CTOL - CONCESSIONARIA VIARIO S.A                            
DEBN CTOL18_022031   DEBN CTOL18 I60163                       287.056,13       0,01 10448 - Titulos Privados-Debêntures SPE                      CTOL - CONCESSIONARIA VIARIO S.A                            
DEBN CTOL18_022031   DEBN CTOL18 I60163                       754.926,98       0,01 10448 - Titulos Privados-Debêntures SPE                      CTOL - CONCESSIONARIA VIARIO S.A                            
DEBN CTOL18_022031   DEBN CTOL18 I60163                       378.995,82       0,01 10448 - Titulos Privados-Debêntures SPE                      CTOL - CONCESSIONARIA VIARIO S.A                            
DEBN AEGPA8_012031   DEBN AEGPA8 I464511                        3.940,22       0,00 10440 - Títulos Privados-Debêntures Incent. (Lei 12.431)     AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN CTOL28_022034   DEBN CTOL28 I60112                        19.534,36       0,00 10448 - Titulos Privados-Debêntures SPE                      CTOL - CONCESSIONARIA VIARIO S.A                            
DEBN CTOL28_022034   DEBN CTOL28 I60112                        25.703,11       0,00 10448 - Titulos Privados-Debêntures SPE                      CTOL - CONCESSIONARIA VIARIO S.A                            
DEBN CTOL28_022034   DEBN CTOL28 I60112                       384.518,50       0,01 10448 - Titulos Privados-Debêntures SPE                      CTOL - CONCESSIONARIA VIARIO S.A                            
DEBN CTOL28_022034   DEBN CTOL28 I60112                       782.402,62       0,01 10448 - Titulos Privados-Debêntures SPE                      CTOL - CONCESSIONARIA VIARIO S.A                            
DEBN CTOL28_022034   DEBN CTOL28 I60112                     2.017.179,93       0,04 10448 - Titulos Privados-Debêntures SPE                      CTOL - CONCESSIONARIA VIARIO S.A                            
DEBN CTOL28_022034   DEBN CTOL28 I60112                       367.040,39       0,01 10448 - Titulos Privados-Debêntures SPE                      CTOL - CONCESSIONARIA VIARIO S.A                            
DEBN CTOL28_022034   DEBN CTOL28 I60112                        30.843,73       0,00 10448 - Titulos Privados-Debêntures SPE                      CTOL - CONCESSIONARIA VIARIO S.A                            
DEBN CTOL28_022034   DEBN CTOL28 I60112                       359.843,51       0,01 10448 - Titulos Privados-Debêntures SPE                      CTOL - CONCESSIONARIA VIARIO S.A                            
DEBN CTOL28_022034   DEBN CTOL28 I60112                        46.265,59       0,00 10448 - Titulos Privados-Debêntures SPE                      CTOL - CONCESSIONARIA VIARIO S.A                            
DEBN CTOL28_022034   DEBN CTOL28 I60112                       334.140,40       0,01 10448 - Titulos Privados-Debêntures SPE                      CTOL - CONCESSIONARIA VIARIO S.A                            
DEBN AEGPA8_012031   DEBN AEGPA8 I464511                        5.910,33       0,00 10440 - Títulos Privados-Debêntures Incent. (Lei 12.431)     AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN CTOL28_022034   DEBN CTOL28 I60112                       303.296,68       0,01 10448 - Titulos Privados-Debêntures SPE                      CTOL - CONCESSIONARIA VIARIO S.A                            
DEBN CTOL28_022034   DEBN CTOL28 I60112                       265.256,07       0,00 10448 - Titulos Privados-Debêntures SPE                      CTOL - CONCESSIONARIA VIARIO S.A                            
DEBN CTOL28_022034   DEBN CTOL28 I60112                        41.124,97       0,00 10448 - Titulos Privados-Debêntures SPE                      CTOL - CONCESSIONARIA VIARIO S.A                            
DEBN CTOL28_022034   DEBN CTOL28 I60112                        20.562,49       0,00 10448 - Titulos Privados-Debêntures SPE                      CTOL - CONCESSIONARIA VIARIO S.A                            
DEBN CTOL28_022034   DEBN CTOL28 I60112                         6.168,75       0,00 10448 - Titulos Privados-Debêntures SPE                      CTOL - CONCESSIONARIA VIARIO S.A                            
DEBN CTOL28_022034   DEBN CTOL28 I60112                        89.446,82       0,00 10448 - Titulos Privados-Debêntures SPE                      CTOL - CONCESSIONARIA VIARIO S.A                            
DEBN CTOL28_022034   DEBN CTOL28 I60112                       132.628,04       0,00 10448 - Titulos Privados-Debêntures SPE                      CTOL - CONCESSIONARIA VIARIO S.A                            
DEBN CTOL28_022034   DEBN CTOL28 I60112                       108.981,18       0,00 10448 - Titulos Privados-Debêntures SPE                      CTOL - CONCESSIONARIA VIARIO S.A                            
DEBN CTOL28_022034   DEBN CTOL28 I60112                       295.071,68       0,01 10448 - Titulos Privados-Debêntures SPE                      CTOL - CONCESSIONARIA VIARIO S.A                            
DEBN CTOL28_022034   DEBN CTOL28 I60112                       227.215,48       0,00 10448 - Titulos Privados-Debêntures SPE                      CTOL - CONCESSIONARIA VIARIO S.A                            
DEBN AEGPA8_012031   DEBN AEGPA8 I464511                        3.940,22       0,00 10440 - Títulos Privados-Debêntures Incent. (Lei 12.431)     AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN CTOL28_022034   DEBN CTOL28 I60112                        30.843,73       0,00 10448 - Titulos Privados-Debêntures SPE                      CTOL - CONCESSIONARIA VIARIO S.A                            
DEBN CTOL28_022034   DEBN CTOL28 I60112                       210.765,49       0,00 10448 - Titulos Privados-Debêntures SPE                      CTOL - CONCESSIONARIA VIARIO S.A                            
DEBN CTOL28_022034   DEBN CTOL28 I60112                        78.137,45       0,00 10448 - Titulos Privados-Debêntures SPE                      CTOL - CONCESSIONARIA VIARIO S.A                            
DEBN CTOL28_022034   DEBN CTOL28 I60112                        22.618,74       0,00 10448 - Titulos Privados-Debêntures SPE                      CTOL - CONCESSIONARIA VIARIO S.A                            
DEBN CTOL28_022034   DEBN CTOL28 I60112                         9.253,12       0,00 10448 - Titulos Privados-Debêntures SPE                      CTOL - CONCESSIONARIA VIARIO S.A                            
DEBN CTOL28_022034   DEBN CTOL28 I60112                       425.643,48       0,01 10448 - Titulos Privados-Debêntures SPE                      CTOL - CONCESSIONARIA VIARIO S.A                            
DEBN CTOL28_022034   DEBN CTOL28 I60112                       464.712,20       0,01 10448 - Titulos Privados-Debêntures SPE                      CTOL - CONCESSIONARIA VIARIO S.A                            
DEBN CTOL28_022034   DEBN CTOL28 I60112                     2.900.338,73       0,05 10448 - Titulos Privados-Debêntures SPE                      CTOL - CONCESSIONARIA VIARIO S.A                            
DEBN CTOL28_022034   DEBN CTOL28 I60112                       761.840,13       0,01 10448 - Titulos Privados-Debêntures SPE                      CTOL - CONCESSIONARIA VIARIO S.A                            
DEBN CTOL28_022034   DEBN CTOL28 I60112                        47.293,72       0,00 10448 - Titulos Privados-Debêntures SPE                      CTOL - CONCESSIONARIA VIARIO S.A                            
DEBN AEGPA8_012031   DEBN AEGPA8 I464511                        3.940,22       0,00 10440 - Títulos Privados-Debêntures Incent. (Lei 12.431)     AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN CTOL28_022034   DEBN CTOL28 I60112                     1.649.111,41       0,03 10448 - Titulos Privados-Debêntures SPE                      CTOL - CONCESSIONARIA VIARIO S.A                            
DEBN CTOL28_022034   DEBN CTOL28 I60112                        28.787,48       0,00 10448 - Titulos Privados-Debêntures SPE                      CTOL - CONCESSIONARIA VIARIO S.A                            
DEBN CTOL28_022034   DEBN CTOL28 I60112                        19.534,36       0,00 10448 - Titulos Privados-Debêntures SPE                      CTOL - CONCESSIONARIA VIARIO S.A                            
DEBN CTOL28_022034   DEBN CTOL28 I60112                        15.421,86       0,00 10448 - Titulos Privados-Debêntures SPE                      CTOL - CONCESSIONARIA VIARIO S.A                            
DEBN CTOL28_022034   DEBN CTOL28 I60112                       810.161,98       0,01 10448 - Titulos Privados-Debêntures SPE                      CTOL - CONCESSIONARIA VIARIO S.A                            
DEBN CTOL28_022034   DEBN CTOL28 I60112                        20.562,49       0,00 10448 - Titulos Privados-Debêntures SPE                      CTOL - CONCESSIONARIA VIARIO S.A                            
DEBN CTOL28_022034   DEBN CTOL28 I60112                        13.365,62       0,00 10448 - Titulos Privados-Debêntures SPE                      CTOL - CONCESSIONARIA VIARIO S.A                            
DEBN CTOL28_022034   DEBN CTOL28 I60112                        30.843,73       0,00 10448 - Titulos Privados-Debêntures SPE                      CTOL - CONCESSIONARIA VIARIO S.A                            
DEBN CTOL28_022034   DEBN CTOL28 I60112                        27.759,36       0,00 10448 - Titulos Privados-Debêntures SPE                      CTOL - CONCESSIONARIA VIARIO S.A                            
DEBN CTOL28_022034   DEBN CTOL28 I60112                       683.702,69       0,01 10448 - Titulos Privados-Debêntures SPE                      CTOL - CONCESSIONARIA VIARIO S.A                            
DEBN AEGPA8_012031   DEBN AEGPA8 I464511                        4.925,27       0,00 10440 - Títulos Privados-Debêntures Incent. (Lei 12.431)     AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN CTOL28_022034   DEBN CTOL28 I60112                        85.334,32       0,00 10448 - Titulos Privados-Debêntures SPE                      CTOL - CONCESSIONARIA VIARIO S.A                            
DEBN CTOL28_022034   DEBN CTOL28 I60112                        87.390,57       0,00 10448 - Titulos Privados-Debêntures SPE                      CTOL - CONCESSIONARIA VIARIO S.A                            
DEBN CTOL28_022034   DEBN CTOL28 I60112                       133.656,16       0,00 10448 - Titulos Privados-Debêntures SPE                      CTOL - CONCESSIONARIA VIARIO S.A                            
DEBN CTOL28_022034   DEBN CTOL28 I60112                       180.949,89       0,00 10448 - Titulos Privados-Debêntures SPE                      CTOL - CONCESSIONARIA VIARIO S.A                            
DEBN CTOL28_022034   DEBN CTOL28 I60112                       591.171,49       0,01 10448 - Titulos Privados-Debêntures SPE                      CTOL - CONCESSIONARIA VIARIO S.A                            
DEBN CTOL28_022034   DEBN CTOL28 I60112                       885.215,05       0,02 10448 - Titulos Privados-Debêntures SPE                      CTOL - CONCESSIONARIA VIARIO S.A                            
DEBN CTOL28_022034   DEBN CTOL28 I60112                       163.471,77       0,00 10448 - Titulos Privados-Debêntures SPE                      CTOL - CONCESSIONARIA VIARIO S.A                            
DEBN CTOL28_022034   DEBN CTOL28 I60112                     2.231.029,80       0,04 10448 - Titulos Privados-Debêntures SPE                      CTOL - CONCESSIONARIA VIARIO S.A                            
DEBN CTOL28_022034   DEBN CTOL28 I60112                        39.068,72       0,00 10448 - Titulos Privados-Debêntures SPE                      CTOL - CONCESSIONARIA VIARIO S.A                            
DEBN CTOL28_022034   DEBN CTOL28 I60112                       139.824,91       0,00 10448 - Titulos Privados-Debêntures SPE                      CTOL - CONCESSIONARIA VIARIO S.A                            
DEBN AEGPA0_052029   DEBN AEGPA0 H750651                        5.167,58       0,00 10440 - Títulos Privados-Debêntures Incent. (Lei 12.431)     AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN AEGPA8_012031   DEBN AEGPA8 I464511                        4.925,27       0,00 10440 - Títulos Privados-Debêntures Incent. (Lei 12.431)     AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN CTOL28_022034   DEBN CTOL28 I60112                       240.581,09       0,00 10448 - Titulos Privados-Debêntures SPE                      CTOL - CONCESSIONARIA VIARIO S.A                            
DEBN CTOL28_022034   DEBN CTOL28 I60112                       155.246,77       0,00 10448 - Titulos Privados-Debêntures SPE                      CTOL - CONCESSIONARIA VIARIO S.A                            
DEBN CTOL28_022034   DEBN CTOL28 I60112                        51.406,22       0,00 10448 - Titulos Privados-Debêntures SPE                      CTOL - CONCESSIONARIA VIARIO S.A                            
DEBN CTOL28_022034   DEBN CTOL28 I60112                        78.137,45       0,00 10448 - Titulos Privados-Debêntures SPE                      CTOL - CONCESSIONARIA VIARIO S.A                            
DEBN CTOL28_022034   DEBN CTOL28 I60112                        16.449,99       0,00 10448 - Titulos Privados-Debêntures SPE                      CTOL - CONCESSIONARIA VIARIO S.A                            
DEBN CTOL28_022034   DEBN CTOL28 I60112                       143.937,41       0,00 10448 - Titulos Privados-Debêntures SPE                      CTOL - CONCESSIONARIA VIARIO S.A                            
DEBN CTOL28_022034   DEBN CTOL28 I60112                       156.274,90       0,00 10448 - Titulos Privados-Debêntures SPE                      CTOL - CONCESSIONARIA VIARIO S.A                            
DEBN CTOL28_022034   DEBN CTOL28 I60112                       105.896,81       0,00 10448 - Titulos Privados-Debêntures SPE                      CTOL - CONCESSIONARIA VIARIO S.A                            
DEBN CTOL28_022034   DEBN CTOL28 I60112                       223.102,98       0,00 10448 - Titulos Privados-Debêntures SPE                      CTOL - CONCESSIONARIA VIARIO S.A                            
DEBN CTOL28_022034   DEBN CTOL28 I60112                       147.021,78       0,00 10448 - Titulos Privados-Debêntures SPE                      CTOL - CONCESSIONARIA VIARIO S.A                            
DEBN AEGPA8_012031   DEBN AEGPA8 I464511                        1.970,11       0,00 10440 - Títulos Privados-Debêntures Incent. (Lei 12.431)     AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN CTOL28_022034   DEBN CTOL28 I60112                        94.587,44       0,00 10448 - Titulos Privados-Debêntures SPE                      CTOL - CONCESSIONARIA VIARIO S.A                            
DEBN DASAA4_102025   DEBN DASAA4                               55.705,12       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAA4_102025   DEBN DASAA4                               68.365,37       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAA4_102025   DEBN DASAA4                               49.121,79       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAA4_102025   DEBN DASAA4                               61.275,63       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAA4_102025   DEBN DASAA4                            7.495.883,49       0,13 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAA4_102025   DEBN DASAA4                              125.589,72       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAA4_102025   DEBN DASAA4                              152.429,46       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAA4_102025   DEBN DASAA4                               49.121,79       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAA4_102025   DEBN DASAA4                               26.839,74       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN AEGPA8_012031   DEBN AEGPA8 I464511                        2.955,16       0,00 10440 - Títulos Privados-Debêntures Incent. (Lei 12.431)     AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN DASAA4_102025   DEBN DASAA4                            1.414.910,06       0,03 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAA4_102025   DEBN DASAA4                            1.758.256,14       0,03 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAA4_102025   DEBN DASAA4                              534.769,15       0,01 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAA4_102025   DEBN DASAA4                               15.698,72       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAA4_102025   DEBN DASAA4                              821.903,72       0,01 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAA4_102025   DEBN DASAA4                            5.880.941,42       0,11 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAA4_102025   DEBN DASAA4                            4.022.416,06       0,07 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAA4_102025   DEBN DASAA4                               50.641,02       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAA4_102025   DEBN DASAA4                               64.314,09       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAA4_102025   DEBN DASAA4                                8.102,56       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN AEGPA8_012031   DEBN AEGPA8 I464511                        8.865,49       0,00 10440 - Títulos Privados-Debêntures Incent. (Lei 12.431)     AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN DASAA4_102025   DEBN DASAA4                               73.429,48       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAA4_102025   DEBN DASAA4                               80.519,22       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAA4_102025   DEBN DASAA4                               69.378,19       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAA4_102025   DEBN DASAA4                               37.474,35       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAA4_102025   DEBN DASAA4                                2.532,05       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAA4_102025   DEBN DASAA4                               43.551,28       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAA4_102025   DEBN DASAA4                               64.820,50       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAA4_102025   DEBN DASAA4                               51.147,43       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAA4_102025   DEBN DASAA4                               95.711,52       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAA4_102025   DEBN DASAA4                                  506,41       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN AEGPA8_012031   DEBN AEGPA8 I464511                       10.835,60       0,00 10440 - Títulos Privados-Debêntures Incent. (Lei 12.431)     AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN DASAA4_102025   DEBN DASAA4                            1.512.647,21       0,03 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAA4_102025   DEBN DASAA4                              293.211,49       0,01 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAA4_102025   DEBN DASAA4                              653.775,54       0,01 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAA4_102025   DEBN DASAA4                               98.243,58       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAA4_102025   DEBN DASAA4                               32.916,66       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAA4_102025   DEBN DASAA4                            2.544.711,15       0,05 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAA5_102026   DEBN DASAA5 I282509                    3.085.652,60       0,06 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAA6_042027   DEBN DASAA6 H979858                       59.642,01       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAA6_042027   DEBN DASAA6 H979858                    5.331.225,86       0,10 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAA6_042027   DEBN DASAA6 H979858                      490.603,61       0,01 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN AEGPA8_012031   DEBN AEGPA8 I464511                          985,05       0,00 10440 - Títulos Privados-Debêntures Incent. (Lei 12.431)     AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN DASAA6_042027   DEBN DASAA6 H979858                       47.136,42       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAA6_042027   DEBN DASAA6 H979858                       53.870,20       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAA6_042027   DEBN DASAA6 H979858                       31.744,94       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAA6_042027   DEBN DASAA6 H979858                       62.527,91       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAA6_042027   DEBN DASAA6 H979858                       35.592,81       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAA6_042027   DEBN DASAA6 H979858                       25.973,13       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAA6_042027   DEBN DASAA6 H979858                    1.361.184,51       0,02 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAA6_042027   DEBN DASAA6 H979858                    1.452.571,46       0,03 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAA6_042027   DEBN DASAA6 H979858                       66.375,78       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAA6_042027   DEBN DASAA6 H979858                        2.885,90       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN AEGPA8_012031   DEBN AEGPA8 I464511                        5.910,33       0,00 10440 - Títulos Privados-Debêntures Incent. (Lei 12.431)     AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN DASAA6_042027   DEBN DASAA6 H979858                       47.136,42       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAA6_042027   DEBN DASAA6 H979858                      148.143,05       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAA6_042027   DEBN DASAA6 H979858                      121.207,95       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAA6_042027   DEBN DASAA6 H979858                    8.916.178,19       0,16 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAA6_042027   DEBN DASAA6 H979858                    2.628.096,18       0,05 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAA6_042027   DEBN DASAA6 H979858                    3.690.108,70       0,07 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAA6_042027   DEBN DASAA6 H979858                       49.060,36       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAA6_042027   DEBN DASAA6 H979858                       72.147,59       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAA6_042027   DEBN DASAA6 H979858                    2.046.105,63       0,04 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAA6_042027   DEBN DASAA6 H979858                      267.427,06       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN AEGPA8_012031   DEBN AEGPA8 I464511                        6.895,38       0,00 10440 - Títulos Privados-Debêntures Incent. (Lei 12.431)     AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN DASAA6_042027   DEBN DASAA6 H979858                          961,97       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAA6_042027   DEBN DASAA6 H979858                       40.402,65       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAA6_042027   DEBN DASAA6 H979858                       69.261,69       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAA6_042027   DEBN DASAA6 H979858                    1.606.486,32       0,03 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAA6_042027   DEBN DASAA6 H979858                      272.236,91       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAA6_042027   DEBN DASAA6 H979858                       93.310,88       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAA6_042027   DEBN DASAA6 H979858                        7.695,74       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAA6_042027   DEBN DASAA6 H979858                       76.957,43       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAA6_042027   DEBN DASAA6 H979858                       71.185,62       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAA6_042027   DEBN DASAA6 H979858                       49.060,36       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN AEGPA8_012031   DEBN AEGPA8 I464511                       12.805,71       0,00 10440 - Títulos Privados-Debêntures Incent. (Lei 12.431)     AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN DASAA6_042027   DEBN DASAA6 H979858                       96.196,78       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAA6_042027   DEBN DASAA6 H979858                    7.304.221,93       0,13 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAA6_042027   DEBN DASAA6 H979858                    5.467.825,29       0,10 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAA6_042027   DEBN DASAA6 H979858                      757.068,70       0,01 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAA6_042027   DEBN DASAA6 H979858                       12.505,58       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAA8_102027   DEBN DASAA8 I338851                      101.764,23       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAA8_102027   DEBN DASAA8 I338851                      129.772,73       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAA8_102027   DEBN DASAA8 I338851                   11.638.466,93       0,21 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAA8_102027   DEBN DASAA8 I338851                    3.700.856,96       0,07 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAA8_102027   DEBN DASAA8 I338851                    1.188.494,18       0,02 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN AEGPA8_012031   DEBN AEGPA8 I464511                        5.910,33       0,00 10440 - Títulos Privados-Debêntures Incent. (Lei 12.431)     AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN DASAA8_102027   DEBN DASAA8 I338851                       24.274,04       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAA8_102027   DEBN DASAA8 I338851                        5.601,70       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAA8_102027   DEBN DASAA8 I338851                    2.300.431,77       0,04 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAA8_102027   DEBN DASAA8 I338851                      191.391,44       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAA8_102027   DEBN DASAA8 I338851                      101.764,23       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAA8_102027   DEBN DASAA8 I338851                       84.025,51       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAA8_102027   DEBN DASAA8 I338851                    1.555.405,58       0,03 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAA8_102027   DEBN DASAA8 I338851                   10.661.903,77       0,19 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAA8_102027   DEBN DASAA8 I338851                    7.771.426,18       0,14 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAA8_102027   DEBN DASAA8 I338851                      256.744,61       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN AEGPA0_052029   DEBN AEGPA0 H750651                       44.441,18       0,00 10440 - Títulos Privados-Debêntures Incent. (Lei 12.431)     AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN AEGPA8_012031   DEBN AEGPA8 I464511                      119.191,61       0,00 10440 - Títulos Privados-Debêntures Incent. (Lei 12.431)     AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN DASAA8_102027   DEBN DASAA8 I338851                       54.149,77       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAA8_102027   DEBN DASAA8 I338851                       67.220,41       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAA8_102027   DEBN DASAA8 I338851                      112.034,02       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAA8_102027   DEBN DASAA8 I338851                    1.096.999,73       0,02 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAA8_102027   DEBN DASAA8 I338851                       99.897,00       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAA8_102027   DEBN DASAA8 I338851                       16.805,10       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAA8_102027   DEBN DASAA8 I338851                    2.888.610,36       0,05 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAA8_102027   DEBN DASAA8 I338851                      201.661,23       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAA8_102027   DEBN DASAA8 I338851                   15.165.671,18       0,27 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAA8_102027   DEBN DASAA8 I338851                       98.029,76       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN AEGPA8_012031   DEBN AEGPA8 I464511                        8.865,49       0,00 10440 - Títulos Privados-Debêntures Incent. (Lei 12.431)     AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN DASAA8_102027   DEBN DASAA8 I338851                      284.753,12       0,01 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAA8_102027   DEBN DASAA8 I338851                      132.573,58       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAA8_102027   DEBN DASAA8 I338851                      125.104,65       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAA8_102027   DEBN DASAA8 I338851                      147.511,45       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAA8_102027   DEBN DASAA8 I338851                      718.884,93       0,01 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAA8_102027   DEBN DASAA8 I338851                       75.622,96       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAA8_102027   DEBN DASAA8 I338851                      128.839,12       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAA8_102027   DEBN DASAA8 I338851                      100.830,61       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAB4_102027   DEBN DASAB4                            1.608.561,72       0,03 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAB4_102027   DEBN DASAB4                              226.761,85       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN AEGPA8_012031   DEBN AEGPA8 I464511                        3.940,22       0,00 10440 - Títulos Privados-Debêntures Incent. (Lei 12.431)     AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN DASAB4_102027   DEBN DASAB4                            1.116.440,26       0,02 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAB4_102027   DEBN DASAB4                              501.770,90       0,01 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAB4_102027   DEBN DASAB4                               28.948,33       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAB4_102027   DEBN DASAB4                                  964,94       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAB4_102027   DEBN DASAB4                               27.983,38       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAB4_102027   DEBN DASAB4                               41.492,59       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAB4_102027   DEBN DASAB4                               14.474,16       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAB4_102027   DEBN DASAB4                               15.439,10       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAB4_102027   DEBN DASAB4                               37.632,82       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAB4_102027   DEBN DASAB4                            2.225.160,96       0,04 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN AEGPA8_012031   DEBN AEGPA8 I464511                        5.910,33       0,00 10440 - Títulos Privados-Debêntures Incent. (Lei 12.431)     AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN DASAB4_102027   DEBN DASAB4                               19.298,88       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAB4_102027   DEBN DASAB4                               14.474,16       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAB4_102027   DEBN DASAB4                              334.835,59       0,01 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAB4_102027   DEBN DASAB4                               12.544,27       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAB4_102027   DEBN DASAB4                              150.531,27       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAB4_102027   DEBN DASAB4                              150.531,27       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAB4_102027   DEBN DASAB4                              103.249,01       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAB4_102027   DEBN DASAB4                            1.496.628,21       0,03 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAB4_102027   DEBN DASAB4                                6.754,61       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAB4_102027   DEBN DASAB4                              150.531,27       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN AEGPA8_012031   DEBN AEGPA8 I464511                        3.940,22       0,00 10440 - Títulos Privados-Debêntures Incent. (Lei 12.431)     AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN DASAB4_102027   DEBN DASAB4                                2.894,83       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAB4_102027   DEBN DASAB4                              424.575,37       0,01 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAB4_102027   DEBN DASAB4                               19.298,88       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAB4_102027   DEBN DASAB4                                7.719,55       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAB4_102027   DEBN DASAB4                               14.474,16       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAB4_102027   DEBN DASAB4                                9.649,44       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAB4_102027   DEBN DASAB4                               16.404,05       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAB4_102027   DEBN DASAB4                               14.474,16       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAB4_102027   DEBN DASAB4                               10.614,38       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAB4_102027   DEBN DASAB4                               18.333,94       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN AEGPA8_012031   DEBN AEGPA8 I464511                      215.726,96       0,00 10440 - Títulos Privados-Debêntures Incent. (Lei 12.431)     AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN DASAB4_102027   DEBN DASAB4                               18.333,94       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAB4_102027   DEBN DASAB4                               22.193,71       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAB5_102028   DEBN DASAB5 H911988                        7.279,10       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAB5_102028   DEBN DASAB5 H911988                       79.160,17       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAB5_102028   DEBN DASAB5 H911988                       43.674,58       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAB5_102028   DEBN DASAB5 H911988                       80.070,06       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAB5_102028   DEBN DASAB5 H911988                       54.593,22       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAB5_102028   DEBN DASAB5 H911988                        6.369,21       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAB5_102028   DEBN DASAB5 H911988                       19.107,63       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAB5_102028   DEBN DASAB5 H911988                       23.657,06       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN AEGPA8_012031   DEBN AEGPA8 I464511                      373.335,70       0,01 10440 - Títulos Privados-Debêntures Incent. (Lei 12.431)     AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN DASAB5_102028   DEBN DASAB5 H911988                      615.083,61       0,01 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAB5_102028   DEBN DASAB5 H911988                       10.918,64       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAB5_102028   DEBN DASAB5 H911988                      230.201,41       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAB5_102028   DEBN DASAB5 H911988                        8.188,98       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAB5_102028   DEBN DASAB5 H911988                       10.008,76       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAB5_102028   DEBN DASAB5 H911988                      266.596,89       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAB5_102028   DEBN DASAB5 H911988                        7.279,10       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAB5_102028   DEBN DASAB5 H911988                      747.017,23       0,01 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAB5_102028   DEBN DASAB5 H911988                       11.828,53       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAB5_102028   DEBN DASAB5 H911988                        4.549,43       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN AEGPA8_012031   DEBN AEGPA8 I464511                       42.357,35       0,00 10440 - Títulos Privados-Debêntures Incent. (Lei 12.431)     AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN DASAB5_102028   DEBN DASAB5 H911988                       10.008,76       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAB5_102028   DEBN DASAB5 H911988                      214.733,33       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAB5_102028   DEBN DASAB5 H911988                        4.549,43       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAB5_102028   DEBN DASAB5 H911988                        9.098,87       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAB5_102028   DEBN DASAB5 H911988                      815.258,75       0,01 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAB5_102028   DEBN DASAB5 H911988                        7.279,10       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAB5_102028   DEBN DASAB5 H911988                        9.098,87       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAB5_102028   DEBN DASAB5 H911988                       15.468,08       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAB5_102028   DEBN DASAB5 H911988                      841.645,47       0,02 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAB5_102028   DEBN DASAB5 H911988                          909,89       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN AEGPA8_012031   DEBN AEGPA8 I464511                       76.834,26       0,00 10440 - Títulos Privados-Debêntures Incent. (Lei 12.431)     AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN DASAB5_102028   DEBN DASAB5 H911988                        2.729,66       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAB5_102028   DEBN DASAB5 H911988                       14.558,19       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAB5_102028   DEBN DASAB5 H911988                        5.459,32       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAB5_102028   DEBN DASAB5 H911988                      123.744,63       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAB5_102028   DEBN DASAB5 H911988                    1.140.088,40       0,02 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAB5_102028   DEBN DASAB5 H911988                       11.828,53       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAB5_102028   DEBN DASAB5 H911988                       10.918,64       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAC5_102031   DEBN DASAC5 H910152                       20.710,04       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAC5_102031   DEBN DASAC5 H910152                       25.024,64       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAC5_102031   DEBN DASAC5 H910152                       15.532,53       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN AEGPA8_012031   DEBN AEGPA8 I464511                        1.970,11       0,00 10440 - Títulos Privados-Debêntures Incent. (Lei 12.431)     AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN DASAC5_102031   DEBN DASAC5 H910152                        8.629,19       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAC5_102031   DEBN DASAC5 H910152                        1.725,84       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAC5_102031   DEBN DASAC5 H910152                      235.576,77       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAC5_102031   DEBN DASAC5 H910152                       46.597,61       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAC5_102031   DEBN DASAC5 H910152                      511.710,71       0,01 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAC5_102031   DEBN DASAC5 H910152                      620.438,45       0,01 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAC5_102031   DEBN DASAC5 H910152                      928.500,39       0,02 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAC5_102031   DEBN DASAC5 H910152                      128.574,87       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAC5_102031   DEBN DASAC5 H910152                        1.725,84       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAC5_102031   DEBN DASAC5 H910152                       16.395,46       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN AEGPA0_052029   DEBN AEGPA0 H750651                       60.977,43       0,00 10440 - Títulos Privados-Debêntures Incent. (Lei 12.431)     AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN AEGPA8_012031   DEBN AEGPA8 I464511                       51.222,84       0,00 10440 - Títulos Privados-Debêntures Incent. (Lei 12.431)     AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN DASAC5_102031   DEBN DASAC5 H910152                          862,92       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAC5_102031   DEBN DASAC5 H910152                       11.217,94       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAC5_102031   DEBN DASAC5 H910152                        6.040,43       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAC5_102031   DEBN DASAC5 H910152                       10.355,02       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAC5_102031   DEBN DASAC5 H910152                        8.629,19       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAC5_102031   DEBN DASAC5 H910152                       13.806,70       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAC5_102031   DEBN DASAC5 H910152                        9.492,10       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAC5_102031   DEBN DASAC5 H910152                        7.766,27       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAC5_102031   DEBN DASAC5 H910152                   15.775.877,37       0,28 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAC5_102031   DEBN DASAC5 H910152                        4.314,59       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN AEGPA8_012031   DEBN AEGPA8 I464511                      165.489,18       0,00 10440 - Títulos Privados-Debêntures Incent. (Lei 12.431)     AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN DASAC5_102031   DEBN DASAC5 H910152                      233.850,93       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAC5_102031   DEBN DASAC5 H910152                        5.177,51       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAC5_102031   DEBN DASAC5 H910152                      477.193,97       0,01 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAC5_102031   DEBN DASAC5 H910152                      248.520,55       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAC5_102031   DEBN DASAC5 H910152                    1.256.409,44       0,02 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAC5_102031   DEBN DASAC5 H910152                        8.629,19       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAC5_102031   DEBN DASAC5 H910152                       12.943,78       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAC5_102031   DEBN DASAC5 H910152                       12.080,86       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAC5_102031   DEBN DASAC5 H910152                        6.903,35       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAC5_102031   DEBN DASAC5 H910152                       45.734,68       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN AEGPA8_012031   DEBN AEGPA8 I464511                       33.491,86       0,00 10440 - Títulos Privados-Debêntures Incent. (Lei 12.431)     AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN DASAC5_102031   DEBN DASAC5 H910152                       12.943,78       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN DASAC5_102031   DEBN DASAC5 H910152                        9.492,10       0,00 10403 - Títulos Privados-Debêntures simples                  DASA - DIAGNOSTICOS AMERICA SA                              
DEBN ELET13_042026   DEBN ELET13                            7.444.935,96       0,13 10403 - Títulos Privados-Debêntures simples                  ELET - CENTRAIS ELETRICAS BRASILEIRA SA ELETROBRAS          
DEBN ELET13_042026   DEBN ELET13                               92.877,00       0,00 10403 - Títulos Privados-Debêntures simples                  ELET - CENTRAIS ELETRICAS BRASILEIRA SA ELETROBRAS          
DEBN ELET13_042026   DEBN ELET13                              229.026,24       0,00 10403 - Títulos Privados-Debêntures simples                  ELET - CENTRAIS ELETRICAS BRASILEIRA SA ELETROBRAS          
DEBN ELET13_042026   DEBN ELET13                               73.879,43       0,00 10403 - Títulos Privados-Debêntures simples                  ELET - CENTRAIS ELETRICAS BRASILEIRA SA ELETROBRAS          
DEBN ELET13_042026   DEBN ELET13                               26.385,51       0,00 10403 - Títulos Privados-Debêntures simples                  ELET - CENTRAIS ELETRICAS BRASILEIRA SA ELETROBRAS          
DEBN ELET13_042026   DEBN ELET13                               58.048,13       0,00 10403 - Títulos Privados-Debêntures simples                  ELET - CENTRAIS ELETRICAS BRASILEIRA SA ELETROBRAS          
DEBN ELET13_042026   DEBN ELET13                                5.277,10       0,00 10403 - Títulos Privados-Debêntures simples                  ELET - CENTRAIS ELETRICAS BRASILEIRA SA ELETROBRAS          
DEBN ELET13_042026   DEBN ELET13                              141.426,34       0,00 10403 - Títulos Privados-Debêntures simples                  ELET - CENTRAIS ELETRICAS BRASILEIRA SA ELETROBRAS          
DEBN AEGPB7_092028   DEBN AEGPB7 I445418                       12.897,47       0,00 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN ELET13_042026   DEBN ELET13                               28.496,35       0,00 10403 - Títulos Privados-Debêntures simples                  ELET - CENTRAIS ELETRICAS BRASILEIRA SA ELETROBRAS          
DEBN ELET13_042026   DEBN ELET13                            2.636.440,32       0,05 10403 - Títulos Privados-Debêntures simples                  ELET - CENTRAIS ELETRICAS BRASILEIRA SA ELETROBRAS          
DEBN ELET13_042026   DEBN ELET13                              268.076,80       0,00 10403 - Títulos Privados-Debêntures simples                  ELET - CENTRAIS ELETRICAS BRASILEIRA SA ELETROBRAS          
DEBN ELET13_042026   DEBN ELET13                               25.330,09       0,00 10403 - Títulos Privados-Debêntures simples                  ELET - CENTRAIS ELETRICAS BRASILEIRA SA ELETROBRAS          
DEBN ELET13_042026   DEBN ELET13                              612.143,87       0,01 10403 - Títulos Privados-Debêntures simples                  ELET - CENTRAIS ELETRICAS BRASILEIRA SA ELETROBRAS          
DEBN ELET13_042026   DEBN ELET13                               44.327,66       0,00 10403 - Títulos Privados-Debêntures simples                  ELET - CENTRAIS ELETRICAS BRASILEIRA SA ELETROBRAS          
DEBN ELET13_042026   DEBN ELET13                            1.800.547,31       0,03 10403 - Títulos Privados-Debêntures simples                  ELET - CENTRAIS ELETRICAS BRASILEIRA SA ELETROBRAS          
DEBN ELET13_042026   DEBN ELET13                               75.990,27       0,00 10403 - Títulos Privados-Debêntures simples                  ELET - CENTRAIS ELETRICAS BRASILEIRA SA ELETROBRAS          
DEBN ELET13_042026   DEBN ELET13                               73.879,43       0,00 10403 - Títulos Privados-Debêntures simples                  ELET - CENTRAIS ELETRICAS BRASILEIRA SA ELETROBRAS          
DEBN ELET13_042026   DEBN ELET13                               55.937,28       0,00 10403 - Títulos Privados-Debêntures simples                  ELET - CENTRAIS ELETRICAS BRASILEIRA SA ELETROBRAS          
DEBN AEGPB7_092028   DEBN AEGPB7 I445418                        2.149,58       0,00 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN ELET13_042026   DEBN ELET13                               99.209,52       0,00 10403 - Títulos Privados-Debêntures simples                  ELET - CENTRAIS ELETRICAS BRASILEIRA SA ELETROBRAS          
DEBN ELET13_042026   DEBN ELET13                                5.277,10       0,00 10403 - Títulos Privados-Debêntures simples                  ELET - CENTRAIS ELETRICAS BRASILEIRA SA ELETROBRAS          
DEBN ELET13_042026   DEBN ELET13                               71.768,59       0,00 10403 - Títulos Privados-Debêntures simples                  ELET - CENTRAIS ELETRICAS BRASILEIRA SA ELETROBRAS          
DEBN ELET13_042026   DEBN ELET13                              935.102,53       0,02 10403 - Títulos Privados-Debêntures simples                  ELET - CENTRAIS ELETRICAS BRASILEIRA SA ELETROBRAS          
DEBN ELET13_042026   DEBN ELET13                              103.431,20       0,00 10403 - Títulos Privados-Debêntures simples                  ELET - CENTRAIS ELETRICAS BRASILEIRA SA ELETROBRAS          
DEBN ELET13_042026   DEBN ELET13                               82.322,80       0,00 10403 - Títulos Privados-Debêntures simples                  ELET - CENTRAIS ELETRICAS BRASILEIRA SA ELETROBRAS          
DEBN ELET13_042026   DEBN ELET13                               94.987,84       0,00 10403 - Títulos Privados-Debêntures simples                  ELET - CENTRAIS ELETRICAS BRASILEIRA SA ELETROBRAS          
DEBN ELET13_042026   DEBN ELET13                               13.720,47       0,00 10403 - Títulos Privados-Debêntures simples                  ELET - CENTRAIS ELETRICAS BRASILEIRA SA ELETROBRAS          
DEBN ELET13_042026   DEBN ELET13                               82.322,80       0,00 10403 - Títulos Privados-Debêntures simples                  ELET - CENTRAIS ELETRICAS BRASILEIRA SA ELETROBRAS          
DEBN ELET13_042026   DEBN ELET13                            7.286.622,89       0,13 10403 - Títulos Privados-Debêntures simples                  ELET - CENTRAIS ELETRICAS BRASILEIRA SA ELETROBRAS          
DEBN AEGPB7_092028   DEBN AEGPB7 I445418                      492.253,59       0,01 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN ELET13_042026   DEBN ELET13                              106.597,47       0,00 10403 - Títulos Privados-Debêntures simples                  ELET - CENTRAIS ELETRICAS BRASILEIRA SA ELETROBRAS          
DEBN ELET13_042026   DEBN ELET13                              229.026,24       0,00 10403 - Títulos Privados-Debêntures simples                  ELET - CENTRAIS ELETRICAS BRASILEIRA SA ELETROBRAS          
DEBN ELET13_042026   DEBN ELET13                              108.708,31       0,00 10403 - Títulos Privados-Debêntures simples                  ELET - CENTRAIS ELETRICAS BRASILEIRA SA ELETROBRAS          
DEBN ELET13_042026   DEBN ELET13                               73.879,43       0,00 10403 - Títulos Privados-Debêntures simples                  ELET - CENTRAIS ELETRICAS BRASILEIRA SA ELETROBRAS          
DEBN ELET13_042026   DEBN ELET13                               33.773,45       0,00 10403 - Títulos Privados-Debêntures simples                  ELET - CENTRAIS ELETRICAS BRASILEIRA SA ELETROBRAS          
DEBN ELET13_042026   DEBN ELET13                               73.879,43       0,00 10403 - Títulos Privados-Debêntures simples                  ELET - CENTRAIS ELETRICAS BRASILEIRA SA ELETROBRAS          
DEBN ELET13_042026   DEBN ELET13                           19.246.647,60       0,34 10403 - Títulos Privados-Debêntures simples                  ELET - CENTRAIS ELETRICAS BRASILEIRA SA ELETROBRAS          
DEBN ELET24_092028   DEBN ELET24 I409779                      224.307,91       0,00 10403 - Títulos Privados-Debêntures simples                  ELET - CENTRAIS ELETRICAS BRASILEIRA SA ELETROBRAS          
DEBN ELET24_092028   DEBN ELET24 I409779                      237.125,51       0,00 10403 - Títulos Privados-Debêntures simples                  ELET - CENTRAIS ELETRICAS BRASILEIRA SA ELETROBRAS          
DEBN ELET24_092028   DEBN ELET24 I409779                      263.828,83       0,00 10403 - Títulos Privados-Debêntures simples                  ELET - CENTRAIS ELETRICAS BRASILEIRA SA ELETROBRAS          
DEBN AEGPB7_092028   DEBN AEGPB7 I445418                      399.821,69       0,01 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN ELET24_092028   DEBN ELET24 I409779                       88.655,03       0,00 10403 - Títulos Privados-Debêntures simples                  ELET - CENTRAIS ELETRICAS BRASILEIRA SA ELETROBRAS          
DEBN ELET24_092028   DEBN ELET24 I409779                    3.148.855,86       0,06 10403 - Títulos Privados-Debêntures simples                  ELET - CENTRAIS ELETRICAS BRASILEIRA SA ELETROBRAS          
DEBN ELET24_092028   DEBN ELET24 I409779                    1.941.865,65       0,03 10403 - Títulos Privados-Debêntures simples                  ELET - CENTRAIS ELETRICAS BRASILEIRA SA ELETROBRAS          
DEBN ELET24_092028   DEBN ELET24 I409779                      107.881,43       0,00 10403 - Títulos Privados-Debêntures simples                  ELET - CENTRAIS ELETRICAS BRASILEIRA SA ELETROBRAS          
DEBN ELET24_092028   DEBN ELET24 I409779                      179.446,33       0,00 10403 - Títulos Privados-Debêntures simples                  ELET - CENTRAIS ELETRICAS BRASILEIRA SA ELETROBRAS          
DEBN ELET24_092028   DEBN ELET24 I409779                      105.745,16       0,00 10403 - Títulos Privados-Debêntures simples                  ELET - CENTRAIS ELETRICAS BRASILEIRA SA ELETROBRAS          
DEBN ELET24_092028   DEBN ELET24 I409779                      143.129,81       0,00 10403 - Títulos Privados-Debêntures simples                  ELET - CENTRAIS ELETRICAS BRASILEIRA SA ELETROBRAS          
DEBN ELET24_092028   DEBN ELET24 I409779                      347.143,20       0,01 10403 - Títulos Privados-Debêntures simples                  ELET - CENTRAIS ELETRICAS BRASILEIRA SA ELETROBRAS          
DEBN ELET24_092028   DEBN ELET24 I409779                   61.916.461,14       1,11 10403 - Títulos Privados-Debêntures simples                  ELET - CENTRAIS ELETRICAS BRASILEIRA SA ELETROBRAS          
DEBN ELET24_092028   DEBN ELET24 I409779                      237.125,51       0,00 10403 - Títulos Privados-Debêntures simples                  ELET - CENTRAIS ELETRICAS BRASILEIRA SA ELETROBRAS          
DEBN AEGPB7_092028   DEBN AEGPB7 I445418                        9.673,11       0,00 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN ELET24_092028   DEBN ELET24 I409779                    5.796.757,37       0,10 10403 - Títulos Privados-Debêntures simples                  ELET - CENTRAIS ELETRICAS BRASILEIRA SA ELETROBRAS          
DEBN ELET24_092028   DEBN ELET24 I409779                      243.534,31       0,00 10403 - Títulos Privados-Debêntures simples                  ELET - CENTRAIS ELETRICAS BRASILEIRA SA ELETROBRAS          
DEBN ELET24_092028   DEBN ELET24 I409779                       99.336,36       0,00 10403 - Títulos Privados-Debêntures simples                  ELET - CENTRAIS ELETRICAS BRASILEIRA SA ELETROBRAS          
DEBN ELET24_092028   DEBN ELET24 I409779                      127.107,82       0,00 10403 - Títulos Privados-Debêntures simples                  ELET - CENTRAIS ELETRICAS BRASILEIRA SA ELETROBRAS          
DEBN ELET24_092028   DEBN ELET24 I409779                    9.223.327,79       0,16 10403 - Títulos Privados-Debêntures simples                  ELET - CENTRAIS ELETRICAS BRASILEIRA SA ELETROBRAS          
DEBN ELET24_092028   DEBN ELET24 I409779                      905.776,72       0,02 10403 - Títulos Privados-Debêntures simples                  ELET - CENTRAIS ELETRICAS BRASILEIRA SA ELETROBRAS          
DEBN ELET24_092028   DEBN ELET24 I409779                      396.277,31       0,01 10403 - Títulos Privados-Debêntures simples                  ELET - CENTRAIS ELETRICAS BRASILEIRA SA ELETROBRAS          
DEBN ELET24_092028   DEBN ELET24 I409779                      304.417,88       0,01 10403 - Títulos Privados-Debêntures simples                  ELET - CENTRAIS ELETRICAS BRASILEIRA SA ELETROBRAS          
DEBN ELET24_092028   DEBN ELET24 I409779                    1.139.697,83       0,02 10403 - Títulos Privados-Debêntures simples                  ELET - CENTRAIS ELETRICAS BRASILEIRA SA ELETROBRAS          
DEBN ELET24_092028   DEBN ELET24 I409779                      299.077,22       0,01 10403 - Títulos Privados-Debêntures simples                  ELET - CENTRAIS ELETRICAS BRASILEIRA SA ELETROBRAS          
DEBN AEGPB7_092028   DEBN AEGPB7 I445418                        6.448,74       0,00 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN ELET24_092028   DEBN ELET24 I409779                      267.033,23       0,00 10403 - Títulos Privados-Debêntures simples                  ELET - CENTRAIS ELETRICAS BRASILEIRA SA ELETROBRAS          
DEBN ELET24_092028   DEBN ELET24 I409779                      330.053,07       0,01 10403 - Títulos Privados-Debêntures simples                  ELET - CENTRAIS ELETRICAS BRASILEIRA SA ELETROBRAS          
DEBN ELET24_092028   DEBN ELET24 I409779                      234.989,24       0,00 10403 - Títulos Privados-Debêntures simples                  ELET - CENTRAIS ELETRICAS BRASILEIRA SA ELETROBRAS          
DEBN ELET24_092028   DEBN ELET24 I409779                      177.310,07       0,00 10403 - Títulos Privados-Debêntures simples                  ELET - CENTRAIS ELETRICAS BRASILEIRA SA ELETROBRAS          
DEBN ELET24_092028   DEBN ELET24 I409779                      228.580,45       0,00 10403 - Títulos Privados-Debêntures simples                  ELET - CENTRAIS ELETRICAS BRASILEIRA SA ELETROBRAS          
DEBN ELET24_092028   DEBN ELET24 I409779                      182.650,73       0,00 10403 - Títulos Privados-Debêntures simples                  ELET - CENTRAIS ELETRICAS BRASILEIRA SA ELETROBRAS          
DEBN ELET24_092028   DEBN ELET24 I409779                       82.246,24       0,00 10403 - Títulos Privados-Debêntures simples                  ELET - CENTRAIS ELETRICAS BRASILEIRA SA ELETROBRAS          
DEBN ELET24_092028   DEBN ELET24 I409779                      453.956,49       0,01 10403 - Títulos Privados-Debêntures simples                  ELET - CENTRAIS ELETRICAS BRASILEIRA SA ELETROBRAS          
DEBN ELET24_092028   DEBN ELET24 I409779                       45.929,72       0,00 10403 - Títulos Privados-Debêntures simples                  ELET - CENTRAIS ELETRICAS BRASILEIRA SA ELETROBRAS          
DEBN ELET24_092028   DEBN ELET24 I409779                      531.930,20       0,01 10403 - Títulos Privados-Debêntures simples                  ELET - CENTRAIS ELETRICAS BRASILEIRA SA ELETROBRAS          
DEBN AEGPB7_092028   DEBN AEGPB7 I445418                       17.196,63       0,00 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN ELET24_092028   DEBN ELET24 I409779                      236.057,38       0,00 10403 - Títulos Privados-Debêntures simples                  ELET - CENTRAIS ELETRICAS BRASILEIRA SA ELETROBRAS          
DEBN ELET24_092028   DEBN ELET24 I409779                       84.382,50       0,00 10403 - Títulos Privados-Debêntures simples                  ELET - CENTRAIS ELETRICAS BRASILEIRA SA ELETROBRAS          
DEBN ELET24_092028   DEBN ELET24 I409779                       18.158,26       0,00 10403 - Títulos Privados-Debêntures simples                  ELET - CENTRAIS ELETRICAS BRASILEIRA SA ELETROBRAS          
DEBN ELET24_092028   DEBN ELET24 I409779                      381.323,45       0,01 10403 - Títulos Privados-Debêntures simples                  ELET - CENTRAIS ELETRICAS BRASILEIRA SA ELETROBRAS          
DEBN ELET24_092028   DEBN ELET24 I409779                      146.334,21       0,00 10403 - Títulos Privados-Debêntures simples                  ELET - CENTRAIS ELETRICAS BRASILEIRA SA ELETROBRAS          
DEBN ELET24_092028   DEBN ELET24 I409779                    4.612.197,96       0,08 10403 - Títulos Privados-Debêntures simples                  ELET - CENTRAIS ELETRICAS BRASILEIRA SA ELETROBRAS          
DEBN ELET24_092028   DEBN ELET24 I409779                      576.791,78       0,01 10403 - Títulos Privados-Debêntures simples                  ELET - CENTRAIS ELETRICAS BRASILEIRA SA ELETROBRAS          
DEBN ELET32_042026   DEBN ELET32 I343577                        1.033,22       0,00 10403 - Títulos Privados-Debêntures simples                  ELET - CENTRAIS ELETRICAS BRASILEIRA SA ELETROBRAS          
DEBN ELET32_042026   DEBN ELET32 I343577                        6.199,31       0,00 10403 - Títulos Privados-Debêntures simples                  ELET - CENTRAIS ELETRICAS BRASILEIRA SA ELETROBRAS          
DEBN ELET32_042026   DEBN ELET32 I343577                       17.564,72       0,00 10403 - Títulos Privados-Debêntures simples                  ELET - CENTRAIS ELETRICAS BRASILEIRA SA ELETROBRAS          
DEBN AEGPA0_052029   DEBN AEGPA0 H750651                        4.134,06       0,00 10440 - Títulos Privados-Debêntures Incent. (Lei 12.431)     AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN AEGPB7_092028   DEBN AEGPB7 I445418                       20.421,00       0,00 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN ELET32_042026   DEBN ELET32 I343577                       16.531,50       0,00 10403 - Títulos Privados-Debêntures simples                  ELET - CENTRAIS ELETRICAS BRASILEIRA SA ELETROBRAS          
DEBN ELET32_042026   DEBN ELET32 I343577                    4.404.610,90       0,08 10403 - Títulos Privados-Debêntures simples                  ELET - CENTRAIS ELETRICAS BRASILEIRA SA ELETROBRAS          
DEBN ELET32_042026   DEBN ELET32 I343577                       24.797,25       0,00 10403 - Títulos Privados-Debêntures simples                  ELET - CENTRAIS ELETRICAS BRASILEIRA SA ELETROBRAS          
DEBN ELET32_042026   DEBN ELET32 I343577                       10.332,19       0,00 10403 - Títulos Privados-Debêntures simples                  ELET - CENTRAIS ELETRICAS BRASILEIRA SA ELETROBRAS          
DEBN ELET32_042026   DEBN ELET32 I343577                      141.550,95       0,00 10403 - Títulos Privados-Debêntures simples                  ELET - CENTRAIS ELETRICAS BRASILEIRA SA ELETROBRAS          
DEBN ELET32_042026   DEBN ELET32 I343577                        3.099,66       0,00 10403 - Títulos Privados-Debêntures simples                  ELET - CENTRAIS ELETRICAS BRASILEIRA SA ELETROBRAS          
DEBN ELET32_042026   DEBN ELET32 I343577                       21.697,59       0,00 10403 - Títulos Privados-Debêntures simples                  ELET - CENTRAIS ELETRICAS BRASILEIRA SA ELETROBRAS          
DEBN ELET32_042026   DEBN ELET32 I343577                       16.531,50       0,00 10403 - Títulos Privados-Debêntures simples                  ELET - CENTRAIS ELETRICAS BRASILEIRA SA ELETROBRAS          
DEBN ELET32_042026   DEBN ELET32 I343577                        7.232,53       0,00 10403 - Títulos Privados-Debêntures simples                  ELET - CENTRAIS ELETRICAS BRASILEIRA SA ELETROBRAS          
DEBN ELET32_042026   DEBN ELET32 I343577                       70.258,87       0,00 10403 - Títulos Privados-Debêntures simples                  ELET - CENTRAIS ELETRICAS BRASILEIRA SA ELETROBRAS          
DEBN AEGPB7_092028   DEBN AEGPB7 I445418                       16.121,84       0,00 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN ELET32_042026   DEBN ELET32 I343577                      414.320,66       0,01 10403 - Títulos Privados-Debêntures simples                  ELET - CENTRAIS ELETRICAS BRASILEIRA SA ELETROBRAS          
DEBN ELET32_042026   DEBN ELET32 I343577                       10.332,19       0,00 10403 - Títulos Privados-Debêntures simples                  ELET - CENTRAIS ELETRICAS BRASILEIRA SA ELETROBRAS          
DEBN ELET32_042026   DEBN ELET32 I343577                       19.631,15       0,00 10403 - Títulos Privados-Debêntures simples                  ELET - CENTRAIS ELETRICAS BRASILEIRA SA ELETROBRAS          
DEBN ELET32_042026   DEBN ELET32 I343577                       16.531,50       0,00 10403 - Títulos Privados-Debêntures simples                  ELET - CENTRAIS ELETRICAS BRASILEIRA SA ELETROBRAS          
DEBN ELET32_042026   DEBN ELET32 I343577                        7.232,53       0,00 10403 - Títulos Privados-Debêntures simples                  ELET - CENTRAIS ELETRICAS BRASILEIRA SA ELETROBRAS          
DEBN ELET32_042026   DEBN ELET32 I343577                       32.029,78       0,00 10403 - Títulos Privados-Debêntures simples                  ELET - CENTRAIS ELETRICAS BRASILEIRA SA ELETROBRAS          
DEBN ELET32_042026   DEBN ELET32 I343577                       26.863,68       0,00 10403 - Títulos Privados-Debêntures simples                  ELET - CENTRAIS ELETRICAS BRASILEIRA SA ELETROBRAS          
DEBN ELET32_042026   DEBN ELET32 I343577                       38.229,09       0,00 10403 - Títulos Privados-Debêntures simples                  ELET - CENTRAIS ELETRICAS BRASILEIRA SA ELETROBRAS          
DEBN ELET32_042026   DEBN ELET32 I343577                       16.531,50       0,00 10403 - Títulos Privados-Debêntures simples                  ELET - CENTRAIS ELETRICAS BRASILEIRA SA ELETROBRAS          
DEBN ELET32_042026   DEBN ELET32 I343577                      655.060,59       0,01 10403 - Títulos Privados-Debêntures simples                  ELET - CENTRAIS ELETRICAS BRASILEIRA SA ELETROBRAS          
DEBN AEGPB7_092028   DEBN AEGPB7 I445418                       12.897,47       0,00 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN ELET32_042026   DEBN ELET32 I343577                      178.746,82       0,00 10403 - Títulos Privados-Debêntures simples                  ELET - CENTRAIS ELETRICAS BRASILEIRA SA ELETROBRAS          
DEBN ELET32_042026   DEBN ELET32 I343577                       14.465,06       0,00 10403 - Títulos Privados-Debêntures simples                  ELET - CENTRAIS ELETRICAS BRASILEIRA SA ELETROBRAS          
DEBN ELET32_042026   DEBN ELET32 I343577                        5.166,09       0,00 10403 - Títulos Privados-Debêntures simples                  ELET - CENTRAIS ELETRICAS BRASILEIRA SA ELETROBRAS          
DEBN ELET32_042026   DEBN ELET32 I343577                       41.328,75       0,00 10403 - Títulos Privados-Debêntures simples                  ELET - CENTRAIS ELETRICAS BRASILEIRA SA ELETROBRAS          
DEBN ELET32_042026   DEBN ELET32 I343577                       12.398,62       0,00 10403 - Títulos Privados-Debêntures simples                  ELET - CENTRAIS ELETRICAS BRASILEIRA SA ELETROBRAS          
DEBN ELET32_042026   DEBN ELET32 I343577                       21.697,59       0,00 10403 - Títulos Privados-Debêntures simples                  ELET - CENTRAIS ELETRICAS BRASILEIRA SA ELETROBRAS          
DEBN ELET32_042026   DEBN ELET32 I343577                       23.764,02       0,00 10403 - Títulos Privados-Debêntures simples                  ELET - CENTRAIS ELETRICAS BRASILEIRA SA ELETROBRAS          
DEBN ELET32_042026   DEBN ELET32 I343577                       19.631,15       0,00 10403 - Títulos Privados-Debêntures simples                  ELET - CENTRAIS ELETRICAS BRASILEIRA SA ELETROBRAS          
DEBN ELET32_042026   DEBN ELET32 I343577                       13.431,84       0,00 10403 - Títulos Privados-Debêntures simples                  ELET - CENTRAIS ELETRICAS BRASILEIRA SA ELETROBRAS          
DEBN ELMD15_052029   DEBN ELMD15_052029 J71475             45.988.690,52       0,82 10403 - Títulos Privados-Debêntures simples                  ELMD - ELETROMIDIA SA                                       
DEBN AEGPB7_092028   DEBN AEGPB7 I445418                       16.121,84       0,00 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN ELMD15_052029   DEBN ELMD15_052029 J71475                380.071,83       0,01 10403 - Títulos Privados-Debêntures simples                  ELMD - ELETROMIDIA SA                                       
DEBN ENGIA7_102027   DEBN ENGIA7 I448524                        1.054,48       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIA7_102027   DEBN ENGIA7 I448524                        1.054,48       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIA7_102027   DEBN ENGIA7 I448524                        2.108,96       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIA7_102027   DEBN ENGIA7 I448524                        1.054,48       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIA7_102027   DEBN ENGIA7 I448524                        1.054,48       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIA7_102027   DEBN ENGIA7 I448524                        1.054,48       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIA7_102027   DEBN ENGIA7 I448524                        1.054,48       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIA7_102027   DEBN ENGIA7 I448524                        7.381,35       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIA7_102027   DEBN ENGIA7 I448524                        1.054,48       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN AEGPB7_092028   DEBN AEGPB7 I445418                        9.673,11       0,00 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN ENGIA7_102027   DEBN ENGIA7 I448524                        1.054,48       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIA7_102027   DEBN ENGIA7 I448524                      210.895,68       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIA7_102027   DEBN ENGIA7 I448524                        1.054,48       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIA7_102027   DEBN ENGIA7 I448524                        1.054,48       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIA7_102027   DEBN ENGIA7 I448524                        2.108,96       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIA7_102027   DEBN ENGIA7 I448524                        1.054,48       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIA7_102027   DEBN ENGIA7 I448524                        1.054,48       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIA7_102027   DEBN ENGIA7 I448524                        1.054,48       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIA7_102027   DEBN ENGIA7 I448524                        1.054,48       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIA7_102027   DEBN ENGIA7 I448524                        1.054,48       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN AEGPB7_092028   DEBN AEGPB7 I445418                       24.720,16       0,00 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN ENGIA7_102027   DEBN ENGIA7 I448524                        3.163,44       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIA7_102027   DEBN ENGIA7 I448524                        2.108,96       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIA7_102027   DEBN ENGIA7 I448524                        1.054,48       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIA7_102027   DEBN ENGIA7 I448524                       10.544,78       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIA7_102027   DEBN ENGIA7 I448524                       30.579,87       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIA7_102027   DEBN ENGIA7 I448524                        2.108,96       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIA7_102027   DEBN ENGIA7 I448524                        1.054,48       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIA7_102027   DEBN ENGIA7 I448524                       20.035,09       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIB1_092029   DEBN ENGIB1_092029 I979541                19.937,71       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIB1_092029   DEBN ENGIB1_092029 I979541                73.454,74       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN AEGPB7_092028   DEBN AEGPB7 I445418                       33.318,48       0,00 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN ENGIB1_092029   DEBN ENGIB1_092029 I979541                93.392,45       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIB1_092029   DEBN ENGIB1_092029 I979541                31.480,60       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIB1_092029   DEBN ENGIB1_092029 I979541                24.135,13       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIB1_092029   DEBN ENGIB1_092029 I979541                55.615,73       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIB1_092029   DEBN ENGIB1_092029 I979541                14.690,95       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIB1_092029   DEBN ENGIB1_092029 I979541                 2.098,71       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIB1_092029   DEBN ENGIB1_092029 I979541                76.602,80       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIB1_092029   DEBN ENGIB1_092029 I979541                31.480,60       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIB1_092029   DEBN ENGIB1_092029 I979541             5.501.759,89       0,10 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIB1_092029   DEBN ENGIB1_092029 I979541             5.575.214,62       0,10 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN AEGPB7_092028   DEBN AEGPB7 I445418                       37.617,63       0,00 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN ENGIB1_092029   DEBN ENGIB1_092029 I979541                11.542,89       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIB1_092029   DEBN ENGIB1_092029 I979541                11.542,89       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIB1_092029   DEBN ENGIB1_092029 I979541                31.480,60       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIB1_092029   DEBN ENGIB1_092029 I979541                40.924,78       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIB1_092029   DEBN ENGIB1_092029 I979541                24.135,13       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIB1_092029   DEBN ENGIB1_092029 I979541                40.924,78       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIB1_092029   DEBN ENGIB1_092029 I979541                14.690,95       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIB1_092029   DEBN ENGIB1_092029 I979541                35.678,02       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIB1_092029   DEBN ENGIB1_092029 I979541                44.072,84       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIB1_092029   DEBN ENGIB1_092029 I979541                40.924,78       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN AEGPB7_092028   DEBN AEGPB7 I445418                    1.079.088,65       0,02 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN ENGIB8_062028   DEBN ENGIB8 I263178                       64.375,83       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIB8_062028   DEBN ENGIB8 I263178                      121.364,27       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIB8_062028   DEBN ENGIB8 I263178                      890.708,23       0,02 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIB8_062028   DEBN ENGIB8 I263178                    2.630.966,37       0,05 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIB8_062028   DEBN ENGIB8 I263178                      158.301,23       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIB8_062028   DEBN ENGIB8 I263178                   28.038.313,07       0,50 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIB8_062028   DEBN ENGIB8 I263178                      394.697,72       0,01 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIB8_062028   DEBN ENGIB8 I263178                      108.700,17       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIB8_062028   DEBN ENGIB8 I263178                    4.063.064,79       0,07 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIB8_062028   DEBN ENGIB8 I263178                    1.131.326,09       0,02 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN AEGPB7_092028   DEBN AEGPB7 I445418                      123.600,79       0,00 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN ENGIB8_062028   DEBN ENGIB8 I263178                      103.423,47       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIB8_062028   DEBN ENGIB8 I263178                       46.435,03       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIB8_062028   DEBN ENGIB8 I263178                       68.597,20       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIB8_062028   DEBN ENGIB8 I263178                       40.102,98       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIB8_062028   DEBN ENGIB8 I263178                      106.589,49       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIB8_062028   DEBN ENGIB8 I263178                      138.249,74       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIB8_062028   DEBN ENGIB8 I263178                       83.371,98       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIB8_062028   DEBN ENGIB8 I263178                      107.644,83       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIB8_062028   DEBN ENGIB8 I263178                      137.194,40       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIB8_062028   DEBN ENGIB8 I263178                       37.992,29       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN AEGPA0_052029   DEBN AEGPA0 H750651                        2.067,03       0,00 10440 - Títulos Privados-Debêntures Incent. (Lei 12.431)     AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN AEGPB7_092028   DEBN AEGPB7 I445418                       24.720,16       0,00 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN ENGIB8_062028   DEBN ENGIB8 I263178                       80.205,95       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIB8_062028   DEBN ENGIB8 I263178                       66.486,51       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIB8_062028   DEBN ENGIB8 I263178                        7.387,39       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIB8_062028   DEBN ENGIB8 I263178                      262.780,03       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIB8_062028   DEBN ENGIB8 I263178                       40.102,98       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIB8_062028   DEBN ENGIB8 I263178                      241.673,20       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIB8_062028   DEBN ENGIB8 I263178                      107.644,83       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIB8_062028   DEBN ENGIB8 I263178                      109.755,52       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIB8_062028   DEBN ENGIB8 I263178                      150.913,83       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIB8_062028   DEBN ENGIB8 I263178                       49.601,05       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN AEGPB7_092028   DEBN AEGPB7 I445418                       13.972,26       0,00 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN ENGIB8_062028   DEBN ENGIB8 I263178                      120.308,93       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIB8_062028   DEBN ENGIB8 I263178                      173.076,01       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIB8_062028   DEBN ENGIB8 I263178                       36.936,95       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIB8_062028   DEBN ENGIB8 I263178                      206.846,93       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIB8_062028   DEBN ENGIB8 I263178                       21.106,83       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIC5_102028   DEBN ENGIC5 I1988                         51.475,34       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIC5_102028   DEBN ENGIC5 I1988                      9.161.538,09       0,16 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIC5_102028   DEBN ENGIC5 I1988                         35.389,30       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIC5_102028   DEBN ENGIC5 I1988                         35.389,30       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIC5_102028   DEBN ENGIC5 I1988                        124.398,74       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN AEGPB7_092028   DEBN AEGPB7 I445418                       15.047,05       0,00 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN ENGIC5_102028   DEBN ENGIC5 I1988                         67.561,38       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIC5_102028   DEBN ENGIC5 I1988                         35.389,30       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIC5_102028   DEBN ENGIC5 I1988                         26.810,07       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIC5_102028   DEBN ENGIC5 I1988                         45.040,92       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIC5_102028   DEBN ENGIC5 I1988                         16.086,04       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIC5_102028   DEBN ENGIC5 I1988                         35.389,30       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIC5_102028   DEBN ENGIC5 I1988                         31.099,68       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIC5_102028   DEBN ENGIC5 I1988                         12.868,83       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIC5_102028   DEBN ENGIC5 I1988                         21.448,06       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIC5_102028   DEBN ENGIC5 I1988                         45.040,92       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN AEGPB7_092028   DEBN AEGPB7 I445418                       12.897,47       0,00 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN ENGIC5_102028   DEBN ENGIC5 I1988                         12.868,83       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIC5_102028   DEBN ENGIC5 I1988                         38.606,50       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIC5_102028   DEBN ENGIC5 I1988                          4.289,61       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIC5_102028   DEBN ENGIC5 I1988                        857.922,33       0,02 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIC5_102028   DEBN ENGIC5 I1988                        291.693,59       0,01 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIC5_102028   DEBN ENGIC5 I1988                         39.678,91       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIC5_102028   DEBN ENGIC5 I1988                        129.760,75       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIC5_102028   DEBN ENGIC5 I1988                         71.851,00       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIC5_102028   DEBN ENGIC5 I1988                      5.857.464,72       0,10 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIC5_102028   DEBN ENGIC5 I1988                          2.144,81       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN AEGPB7_092028   DEBN AEGPB7 I445418                      101.030,21       0,00 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN ENGIC5_102028   DEBN ENGIC5 I1988                         34.316,89       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIC5_102028   DEBN ENGIC5 I1988                        494.377,74       0,01 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIC5_102028   DEBN ENGIC5 I1988                      1.266.507,84       0,02 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIC5_102028   DEBN ENGIC5 I1988                          6.434,42       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIC5_102028   DEBN ENGIC5 I1988                         12.868,83       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIC5_102028   DEBN ENGIC5 I1988                         34.316,89       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIC5_102028   DEBN ENGIC5 I1988                        114.747,11       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIC5_102028   DEBN ENGIC5 I1988                         39.678,91       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIC5_102028   DEBN ENGIC5 I1988                         82.575,02       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIC6_042027   DEBN ENGIC6 H749258                       26.436,58       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN AEGPB7_092028   DEBN AEGPB7 I445418                      149.395,74       0,00 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN ENGIC6_042027   DEBN ENGIC6 H749258                       25.379,12       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIC6_042027   DEBN ENGIC6 H749258                      260.135,95       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIC6_042027   DEBN ENGIC6 H749258                    1.083.899,80       0,02 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIC6_042027   DEBN ENGIC6 H749258                    9.276.067,39       0,17 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIC6_042027   DEBN ENGIC6 H749258                      129.010,51       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIC6_042027   DEBN ENGIC6 H749258                      365.882,27       0,01 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIC6_042027   DEBN ENGIC6 H749258                       16.919,41       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIC6_042027   DEBN ENGIC6 H749258                      109.976,17       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIC6_042027   DEBN ENGIC6 H749258                       59.217,94       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIC6_042027   DEBN ENGIC6 H749258                       46.528,38       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN AEGPB7_092028   DEBN AEGPB7 I445418                      320.287,27       0,01 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN ENGIC6_042027   DEBN ENGIC6 H749258                       46.528,38       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIC6_042027   DEBN ENGIC6 H749258                      112.091,10       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIC6_042027   DEBN ENGIC6 H749258                       28.551,51       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIC6_042027   DEBN ENGIC6 H749258                       81.424,67       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIC6_042027   DEBN ENGIC6 H749258                    5.794.898,46       0,10 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIC6_042027   DEBN ENGIC6 H749258                       61.332,87       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIC6_042027   DEBN ENGIC6 H749258                       89.884,37       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIC6_042027   DEBN ENGIC6 H749258                       16.919,41       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIC6_042027   DEBN ENGIC6 H749258                       48.643,31       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIC6_042027   DEBN ENGIC6 H749258                       84.597,06       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN AEGPB7_092028   DEBN AEGPB7 I445418                       55.889,05       0,00 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN ENGIC6_042027   DEBN ENGIC6 H749258                       16.919,41       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIC6_042027   DEBN ENGIC6 H749258                        3.172,39       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIC6_042027   DEBN ENGIC6 H749258                       52.873,16       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIC6_042027   DEBN ENGIC6 H749258                       64.505,26       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIC6_042027   DEBN ENGIC6 H749258                       60.275,41       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIC6_042027   DEBN ENGIC6 H749258                       34.896,29       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIC6_042027   DEBN ENGIC6 H749258                       60.275,40       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIC6_042027   DEBN ENGIC6 H749258                       22.206,73       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIC6_042027   DEBN ENGIC6 H749258                       46.528,38       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIC6_042027   DEBN ENGIC6 H749258                       35.953,75       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN AEGPB7_092028   DEBN AEGPB7 I445418                       20.421,00       0,00 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN ENGIC9_092028   DEBN ENGIC9 I479534                       86.696,58       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIC9_092028   DEBN ENGIC9 I479534                       40.672,47       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIC9_092028   DEBN ENGIC9 I479534                       87.766,90       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIC9_092028   DEBN ENGIC9 I479534                       97.399,86       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIC9_092028   DEBN ENGIC9 I479534                       32.109,84       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIC9_092028   DEBN ENGIC9 I479534                       97.399,86       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIC9_092028   DEBN ENGIC9 I479534                      112.384,45       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIC9_092028   DEBN ENGIC9 I479534                       32.109,84       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIC9_092028   DEBN ENGIC9 I479534                       54.586,73       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIC9_092028   DEBN ENGIC9 I479534                        6.421,97       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN AEGPB7_092028   DEBN AEGPB7 I445418                       18.271,42       0,00 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN ENGIC9_092028   DEBN ENGIC9 I479534                      122.017,40       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIC9_092028   DEBN ENGIC9 I479534                      212.995,30       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIC9_092028   DEBN ENGIC9 I479534                      128.439,37       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIC9_092028   DEBN ENGIC9 I479534                      651.829,81       0,01 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIC9_092028   DEBN ENGIC9 I479534                   23.842.628,79       0,43 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIC9_092028   DEBN ENGIC9 I479534                       87.766,90       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIC9_092028   DEBN ENGIC9 I479534                      141.283,31       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIC9_092028   DEBN ENGIC9 I479534                       89.907,56       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIC9_092028   DEBN ENGIC9 I479534                       65.290,01       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIC9_092028   DEBN ENGIC9 I479534                       87.766,90       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN AEGPA0_052029   DEBN AEGPA0 H750651                        3.100,55       0,00 10440 - Títulos Privados-Debêntures Incent. (Lei 12.431)     AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN AEGPB7_092028   DEBN AEGPB7 I445418                      224.631,00       0,00 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN ENGIC9_092028   DEBN ENGIC9 I479534                    2.188.820,97       0,04 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIC9_092028   DEBN ENGIC9 I479534                      168.041,51       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIC9_092028   DEBN ENGIC9 I479534                       17.125,25       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIC9_092028   DEBN ENGIC9 I479534                      111.314,12       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIC9_092028   DEBN ENGIC9 I479534                       52.446,08       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIC9_092028   DEBN ENGIC9 I479534                    1.754.267,76       0,03 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIC9_092028   DEBN ENGIC9 I479534                      107.032,81       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIC9_092028   DEBN ENGIC9 I479534                      466.663,05       0,01 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIC9_092028   DEBN ENGIC9 I479534                       29.969,19       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIC9_092028   DEBN ENGIC9 I479534                      198.010,69       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN AEGPB7_092028   DEBN AEGPB7 I445418                        6.448,74       0,00 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN ENGIC9_092028   DEBN ENGIC9 I479534                       67.430,67       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIC9_092028   DEBN ENGIC9 I479534                       83.485,59       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIC9_092028   DEBN ENGIC9 I479534                    7.775.933,66       0,14 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIC9_092028   DEBN ENGIC9 I479534                       40.672,47       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIC9_092028   DEBN ENGIC9 I479534                    1.199.837,80       0,02 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIC9_092028   DEBN ENGIC9 I479534                       66.360,34       0,00 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENGIC9_092028   DEBN ENGIC9 I479534                    4.601.340,51       0,08 10403 - Títulos Privados-Debêntures simples                  ENGI - ENERGISA SA                                          
DEBN ENMTA8_042029   DEBN ENMTA8 I793078                       23.877,15       0,00 10403 - Títulos Privados-Debêntures simples                  ENMT - ENERGISA MATO GROSSO DISTRIBUIDORA ENERGIA SA        
DEBN ENMTA8_042029   DEBN ENMTA8 I793078                       24.915,28       0,00 10403 - Títulos Privados-Debêntures simples                  ENMT - ENERGISA MATO GROSSO DISTRIBUIDORA ENERGIA SA        
DEBN ENMTA8_042029   DEBN ENMTA8 I793078                       18.686,46       0,00 10403 - Títulos Privados-Debêntures simples                  ENMT - ENERGISA MATO GROSSO DISTRIBUIDORA ENERGIA SA        
DEBN AEGPB7_092028   DEBN AEGPB7 I445418                       15.047,05       0,00 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN ENMTA8_042029   DEBN ENMTA8 I793078                        3.114,41       0,00 10403 - Títulos Privados-Debêntures simples                  ENMT - ENERGISA MATO GROSSO DISTRIBUIDORA ENERGIA SA        
DEBN ENMTA8_042029   DEBN ENMTA8 I793078                       38.411,06       0,00 10403 - Títulos Privados-Debêntures simples                  ENMT - ENERGISA MATO GROSSO DISTRIBUIDORA ENERGIA SA        
DEBN ENMTA8_042029   DEBN ENMTA8 I793078                       59.173,79       0,00 10403 - Títulos Privados-Debêntures simples                  ENMT - ENERGISA MATO GROSSO DISTRIBUIDORA ENERGIA SA        
DEBN ENMTA8_042029   DEBN ENMTA8 I793078                    6.496.659,79       0,12 10403 - Títulos Privados-Debêntures simples                  ENMT - ENERGISA MATO GROSSO DISTRIBUIDORA ENERGIA SA        
DEBN ENMTA8_042029   DEBN ENMTA8 I793078                       55.021,25       0,00 10403 - Títulos Privados-Debêntures simples                  ENMT - ENERGISA MATO GROSSO DISTRIBUIDORA ENERGIA SA        
DEBN ENMTA8_042029   DEBN ENMTA8 I793078                      196.207,85       0,00 10403 - Títulos Privados-Debêntures simples                  ENMT - ENERGISA MATO GROSSO DISTRIBUIDORA ENERGIA SA        
DEBN ENMTA8_042029   DEBN ENMTA8 I793078                       14.533,91       0,00 10403 - Títulos Privados-Debêntures simples                  ENMT - ENERGISA MATO GROSSO DISTRIBUIDORA ENERGIA SA        
DEBN ENMTA8_042029   DEBN ENMTA8 I793078                       35.296,65       0,00 10403 - Títulos Privados-Debêntures simples                  ENMT - ENERGISA MATO GROSSO DISTRIBUIDORA ENERGIA SA        
DEBN ENMTA8_042029   DEBN ENMTA8 I793078                       24.915,28       0,00 10403 - Títulos Privados-Debêntures simples                  ENMT - ENERGISA MATO GROSSO DISTRIBUIDORA ENERGIA SA        
DEBN ENMTA8_042029   DEBN ENMTA8 I793078                        8.305,09       0,00 10403 - Títulos Privados-Debêntures simples                  ENMT - ENERGISA MATO GROSSO DISTRIBUIDORA ENERGIA SA        
DEBN AEGPB7_092028   DEBN AEGPB7 I445418                        1.074,79       0,00 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN ENMTA8_042029   DEBN ENMTA8 I793078                       46.716,15       0,00 10403 - Títulos Privados-Debêntures simples                  ENMT - ENERGISA MATO GROSSO DISTRIBUIDORA ENERGIA SA        
DEBN ENMTA8_042029   DEBN ENMTA8 I793078                        5.190,68       0,00 10403 - Títulos Privados-Debêntures simples                  ENMT - ENERGISA MATO GROSSO DISTRIBUIDORA ENERGIA SA        
DEBN ENMTA8_042029   DEBN ENMTA8 I793078                       31.144,10       0,00 10403 - Títulos Privados-Debêntures simples                  ENMT - ENERGISA MATO GROSSO DISTRIBUIDORA ENERGIA SA        
DEBN ENMTA8_042029   DEBN ENMTA8 I793078                       31.144,10       0,00 10403 - Títulos Privados-Debêntures simples                  ENMT - ENERGISA MATO GROSSO DISTRIBUIDORA ENERGIA SA        
DEBN ENMTA8_042029   DEBN ENMTA8 I793078                      695.551,62       0,01 10403 - Títulos Privados-Debêntures simples                  ENMT - ENERGISA MATO GROSSO DISTRIBUIDORA ENERGIA SA        
DEBN ENMTA8_042029   DEBN ENMTA8 I793078                       28.029,69       0,00 10403 - Títulos Privados-Debêntures simples                  ENMT - ENERGISA MATO GROSSO DISTRIBUIDORA ENERGIA SA        
DEBN ENMTA8_042029   DEBN ENMTA8 I793078                       34.258,51       0,00 10403 - Títulos Privados-Debêntures simples                  ENMT - ENERGISA MATO GROSSO DISTRIBUIDORA ENERGIA SA        
DEBN ENMTA8_042029   DEBN ENMTA8 I793078                       11.419,50       0,00 10403 - Títulos Privados-Debêntures simples                  ENMT - ENERGISA MATO GROSSO DISTRIBUIDORA ENERGIA SA        
DEBN ENMTA8_042029   DEBN ENMTA8 I793078                       26.991,56       0,00 10403 - Títulos Privados-Debêntures simples                  ENMT - ENERGISA MATO GROSSO DISTRIBUIDORA ENERGIA SA        
DEBN ENMTA8_042029   DEBN ENMTA8 I793078                    2.357.608,56       0,04 10403 - Títulos Privados-Debêntures simples                  ENMT - ENERGISA MATO GROSSO DISTRIBUIDORA ENERGIA SA        
DEBN AEGPB7_092028   DEBN AEGPB7 I445418                       12.897,47       0,00 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN ENMTA8_042029   DEBN ENMTA8 I793078                       80.974,67       0,00 10403 - Títulos Privados-Debêntures simples                  ENMT - ENERGISA MATO GROSSO DISTRIBUIDORA ENERGIA SA        
DEBN ENMTA8_042029   DEBN ENMTA8 I793078                       18.686,46       0,00 10403 - Títulos Privados-Debêntures simples                  ENMT - ENERGISA MATO GROSSO DISTRIBUIDORA ENERGIA SA        
DEBN ENMTA8_042029   DEBN ENMTA8 I793078                       24.915,28       0,00 10403 - Títulos Privados-Debêntures simples                  ENMT - ENERGISA MATO GROSSO DISTRIBUIDORA ENERGIA SA        
DEBN ENMTA8_042029   DEBN ENMTA8 I793078                        8.305,09       0,00 10403 - Títulos Privados-Debêntures simples                  ENMT - ENERGISA MATO GROSSO DISTRIBUIDORA ENERGIA SA        
DEBN ENMTA8_042029   DEBN ENMTA8 I793078                       15.572,05       0,00 10403 - Títulos Privados-Debêntures simples                  ENMT - ENERGISA MATO GROSSO DISTRIBUIDORA ENERGIA SA        
DEBN ENMTA8_042029   DEBN ENMTA8 I793078                       24.915,28       0,00 10403 - Títulos Privados-Debêntures simples                  ENMT - ENERGISA MATO GROSSO DISTRIBUIDORA ENERGIA SA        
DEBN ENMTA8_042029   DEBN ENMTA8 I793078                        9.343,23       0,00 10403 - Títulos Privados-Debêntures simples                  ENMT - ENERGISA MATO GROSSO DISTRIBUIDORA ENERGIA SA        
DEBN ENMTB0_092029   DEBN ENMTB0_092029 I979497                12.570,37       0,00 10403 - Títulos Privados-Debêntures simples                  ENMT - ENERGISA MATO GROSSO DISTRIBUIDORA ENERGIA SA        
DEBN ENMTB0_092029   DEBN ENMTB0_092029 I979497                 3.142,59       0,00 10403 - Títulos Privados-Debêntures simples                  ENMT - ENERGISA MATO GROSSO DISTRIBUIDORA ENERGIA SA        
DEBN ENMTB0_092029   DEBN ENMTB0_092029 I979497             2.544.452,63       0,05 10403 - Títulos Privados-Debêntures simples                  ENMT - ENERGISA MATO GROSSO DISTRIBUIDORA ENERGIA SA        
DEBN ALPKA2_052028   DEBN ALPKA2 I810568                       18.509,71       0,00 10403 - Títulos Privados-Debêntures simples                  ALPK - ALLPARK EMPREENDIMENTOS PARTICIPACOES SERVICOS SA    
DEBN ENMTB0_092029   DEBN ENMTB0_092029 I979497                21.998,15       0,00 10403 - Títulos Privados-Debêntures simples                  ENMT - ENERGISA MATO GROSSO DISTRIBUIDORA ENERGIA SA        
DEBN ENMTB0_092029   DEBN ENMTB0_092029 I979497                 2.095,06       0,00 10403 - Títulos Privados-Debêntures simples                  ENMT - ENERGISA MATO GROSSO DISTRIBUIDORA ENERGIA SA        
DEBN ENMTB0_092029   DEBN ENMTB0_092029 I979497                 6.285,19       0,00 10403 - Títulos Privados-Debêntures simples                  ENMT - ENERGISA MATO GROSSO DISTRIBUIDORA ENERGIA SA        
DEBN ENMTB0_092029   DEBN ENMTB0_092029 I979497                17.808,03       0,00 10403 - Títulos Privados-Debêntures simples                  ENMT - ENERGISA MATO GROSSO DISTRIBUIDORA ENERGIA SA        
DEBN ENMTB0_092029   DEBN ENMTB0_092029 I979497                 7.332,72       0,00 10403 - Títulos Privados-Debêntures simples                  ENMT - ENERGISA MATO GROSSO DISTRIBUIDORA ENERGIA SA        
DEBN ENMTB0_092029   DEBN ENMTB0_092029 I979497                 8.380,25       0,00 10403 - Títulos Privados-Debêntures simples                  ENMT - ENERGISA MATO GROSSO DISTRIBUIDORA ENERGIA SA        
DEBN ENMTB0_092029   DEBN ENMTB0_092029 I979497                17.808,02       0,00 10403 - Títulos Privados-Debêntures simples                  ENMT - ENERGISA MATO GROSSO DISTRIBUIDORA ENERGIA SA        
DEBN ENMTB0_092029   DEBN ENMTB0_092029 I979497                15.712,96       0,00 10403 - Títulos Privados-Debêntures simples                  ENMT - ENERGISA MATO GROSSO DISTRIBUIDORA ENERGIA SA        
DEBN ENMTB0_092029   DEBN ENMTB0_092029 I979497                 9.427,78       0,00 10403 - Títulos Privados-Debêntures simples                  ENMT - ENERGISA MATO GROSSO DISTRIBUIDORA ENERGIA SA        
DEBN ENMTB0_092029   DEBN ENMTB0_092029 I979497                 2.095,06       0,00 10403 - Títulos Privados-Debêntures simples                  ENMT - ENERGISA MATO GROSSO DISTRIBUIDORA ENERGIA SA        
DEBN ALPKA2_052028   DEBN ALPKA2 I810568                       34.962,79       0,00 10403 - Títulos Privados-Debêntures simples                  ALPK - ALLPARK EMPREENDIMENTOS PARTICIPACOES SERVICOS SA    
DEBN ENMTB0_092029   DEBN ENMTB0_092029 I979497                 5.237,65       0,00 10403 - Títulos Privados-Debêntures simples                  ENMT - ENERGISA MATO GROSSO DISTRIBUIDORA ENERGIA SA        
DEBN ENMTB0_092029   DEBN ENMTB0_092029 I979497                 3.142,59       0,00 10403 - Títulos Privados-Debêntures simples                  ENMT - ENERGISA MATO GROSSO DISTRIBUIDORA ENERGIA SA        
DEBN ENMTB0_092029   DEBN ENMTB0_092029 I979497                 9.427,78       0,00 10403 - Títulos Privados-Debêntures simples                  ENMT - ENERGISA MATO GROSSO DISTRIBUIDORA ENERGIA SA        
DEBN ENMTB0_092029   DEBN ENMTB0_092029 I979497                10.475,31       0,00 10403 - Títulos Privados-Debêntures simples                  ENMT - ENERGISA MATO GROSSO DISTRIBUIDORA ENERGIA SA        
DEBN ENMTB0_092029   DEBN ENMTB0_092029 I979497                 7.332,72       0,00 10403 - Títulos Privados-Debêntures simples                  ENMT - ENERGISA MATO GROSSO DISTRIBUIDORA ENERGIA SA        
DEBN ENMTB0_092029   DEBN ENMTB0_092029 I979497                 7.332,72       0,00 10403 - Títulos Privados-Debêntures simples                  ENMT - ENERGISA MATO GROSSO DISTRIBUIDORA ENERGIA SA        
DEBN ENMTB0_092029   DEBN ENMTB0_092029 I979497                10.475,31       0,00 10403 - Títulos Privados-Debêntures simples                  ENMT - ENERGISA MATO GROSSO DISTRIBUIDORA ENERGIA SA        
DEBN EQTL25_122028   DEBN EQTL25 I142297                       26.990,41       0,00 10403 - Títulos Privados-Debêntures simples                  EQTL - EQUATORIAL SA                                        
DEBN EQTL25_122028   DEBN EQTL25 I142297                       10.380,93       0,00 10403 - Títulos Privados-Debêntures simples                  EQTL - EQUATORIAL SA                                        
DEBN EQTL25_122028   DEBN EQTL25 I142297                       35.295,15       0,00 10403 - Títulos Privados-Debêntures simples                  EQTL - EQUATORIAL SA                                        
DEBN ALPKA2_052028   DEBN ALPKA2 I810568                   26.488.423,98       0,47 10403 - Títulos Privados-Debêntures simples                  ALPK - ALLPARK EMPREENDIMENTOS PARTICIPACOES SERVICOS SA    
DEBN EQTL25_122028   DEBN EQTL25 I142297                       16.609,48       0,00 10403 - Títulos Privados-Debêntures simples                  EQTL - EQUATORIAL SA                                        
DEBN EQTL25_122028   DEBN EQTL25 I142297                      431.846,49       0,01 10403 - Títulos Privados-Debêntures simples                  EQTL - EQUATORIAL SA                                        
DEBN EQTL25_122028   DEBN EQTL25 I142297                       10.380,93       0,00 10403 - Títulos Privados-Debêntures simples                  EQTL - EQUATORIAL SA                                        
DEBN EQTL25_122028   DEBN EQTL25 I142297                        2.076,19       0,00 10403 - Títulos Privados-Debêntures simples                  EQTL - EQUATORIAL SA                                        
DEBN EQTL25_122028   DEBN EQTL25 I142297                      329.075,33       0,01 10403 - Títulos Privados-Debêntures simples                  EQTL - EQUATORIAL SA                                        
DEBN EQTL25_122028   DEBN EQTL25 I142297                      170.247,17       0,00 10403 - Títulos Privados-Debêntures simples                  EQTL - EQUATORIAL SA                                        
DEBN EQTL25_122028   DEBN EQTL25 I142297                        9.342,83       0,00 10403 - Títulos Privados-Debêntures simples                  EQTL - EQUATORIAL SA                                        
DEBN EQTL25_122028   DEBN EQTL25 I142297                       11.419,02       0,00 10403 - Títulos Privados-Debêntures simples                  EQTL - EQUATORIAL SA                                        
DEBN EQTL25_122028   DEBN EQTL25 I142297                       28.028,50       0,00 10403 - Títulos Privados-Debêntures simples                  EQTL - EQUATORIAL SA                                        
DEBN EQTL25_122028   DEBN EQTL25 I142297                       35.295,15       0,00 10403 - Títulos Privados-Debêntures simples                  EQTL - EQUATORIAL SA                                        
DEBN ALPKA2_052028   DEBN ALPKA2 I810568                    1.075.619,84       0,02 10403 - Títulos Privados-Debêntures simples                  ALPK - ALLPARK EMPREENDIMENTOS PARTICIPACOES SERVICOS SA    
DEBN EQTL25_122028   DEBN EQTL25 I142297                       30.104,68       0,00 10403 - Títulos Privados-Debêntures simples                  EQTL - EQUATORIAL SA                                        
DEBN EQTL25_122028   DEBN EQTL25 I142297                        6.228,56       0,00 10403 - Títulos Privados-Debêntures simples                  EQTL - EQUATORIAL SA                                        
DEBN EQTL25_122028   DEBN EQTL25 I142297                       47.752,26       0,00 10403 - Títulos Privados-Debêntures simples                  EQTL - EQUATORIAL SA                                        
DEBN EQTL25_122028   DEBN EQTL25 I142297                       21.799,94       0,00 10403 - Títulos Privados-Debêntures simples                  EQTL - EQUATORIAL SA                                        
DEBN EQTL25_122028   DEBN EQTL25 I142297                       12.457,11       0,00 10403 - Títulos Privados-Debêntures simples                  EQTL - EQUATORIAL SA                                        
DEBN EQTL25_122028   DEBN EQTL25 I142297                       52.942,72       0,00 10403 - Títulos Privados-Debêntures simples                  EQTL - EQUATORIAL SA                                        
DEBN EQTL25_122028   DEBN EQTL25 I142297                       19.723,76       0,00 10403 - Títulos Privados-Debêntures simples                  EQTL - EQUATORIAL SA                                        
DEBN EQTL25_122028   DEBN EQTL25 I142297                       37.371,33       0,00 10403 - Títulos Privados-Debêntures simples                  EQTL - EQUATORIAL SA                                        
DEBN EQTL25_122028   DEBN EQTL25 I142297                       65.399,83       0,00 10403 - Títulos Privados-Debêntures simples                  EQTL - EQUATORIAL SA                                        
DEBN EQTL25_122028   DEBN EQTL25 I142297                       28.028,50       0,00 10403 - Títulos Privados-Debêntures simples                  EQTL - EQUATORIAL SA                                        
DEBN ANHBA4_062028   DEBN ANHBA4 I243525                      227.897,15       0,00 10403 - Títulos Privados-Debêntures simples                  ANHB - CONCESSIONARIA SISTEMA ANHANGUERA BANDEIRANTES S/A   
DEBN EQTL25_122028   DEBN EQTL25 I142297                       65.399,83       0,00 10403 - Títulos Privados-Debêntures simples                  EQTL - EQUATORIAL SA                                        
DEBN EQTL25_122028   DEBN EQTL25 I142297                      264.713,59       0,00 10403 - Títulos Privados-Debêntures simples                  EQTL - EQUATORIAL SA                                        
DEBN EQTL25_122028   DEBN EQTL25 I142297                       38.409,42       0,00 10403 - Títulos Privados-Debêntures simples                  EQTL - EQUATORIAL SA                                        
DEBN EQTL25_122028   DEBN EQTL25 I142297                       29.066,59       0,00 10403 - Títulos Privados-Debêntures simples                  EQTL - EQUATORIAL SA                                        
DEBN EQTL25_122028   DEBN EQTL25 I142297                      803.483,61       0,01 10403 - Títulos Privados-Debêntures simples                  EQTL - EQUATORIAL SA                                        
DEBN EQTL25_122028   DEBN EQTL25 I142297                       36.333,24       0,00 10403 - Títulos Privados-Debêntures simples                  EQTL - EQUATORIAL SA                                        
DEBN EQTL25_122028   DEBN EQTL25 I142297                       29.066,59       0,00 10403 - Títulos Privados-Debêntures simples                  EQTL - EQUATORIAL SA                                        
DEBN EQTL25_122028   DEBN EQTL25 I142297                    7.720.294,06       0,14 10403 - Títulos Privados-Debêntures simples                  EQTL - EQUATORIAL SA                                        
DEBN ERDVA1_082027   DEBN ERDVA1 H886837                       66.416,80       0,00 10403 - Títulos Privados-Debêntures simples                  ERDV - ECORODOVIAS CONCESSOES SERVICOS SA                   
DEBN ERDVA1_082027   DEBN ERDVA1 H886837                       52.490,69       0,00 10403 - Títulos Privados-Debêntures simples                  ERDV - ECORODOVIAS CONCESSOES SERVICOS SA                   
DEBN AEGPA0_052029   DEBN AEGPA0 H750651                        6.201,09       0,00 10440 - Títulos Privados-Debêntures Incent. (Lei 12.431)     AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN ANHBA4_062028   DEBN ANHBA4 I243525                      293.456,60       0,01 10403 - Títulos Privados-Debêntures simples                  ANHB - CONCESSIONARIA SISTEMA ANHANGUERA BANDEIRANTES S/A   
DEBN ERDVA1_082027   DEBN ERDVA1 H886837                       18.211,06       0,00 10403 - Títulos Privados-Debêntures simples                  ERDV - ECORODOVIAS CONCESSOES SERVICOS SA                   
DEBN ERDVA1_082027   DEBN ERDVA1 H886837                    3.617.572,86       0,06 10403 - Títulos Privados-Debêntures simples                  ERDV - ECORODOVIAS CONCESSOES SERVICOS SA                   
DEBN ERDVA1_082027   DEBN ERDVA1 H886837                       20.353,53       0,00 10403 - Títulos Privados-Debêntures simples                  ERDV - ECORODOVIAS CONCESSOES SERVICOS SA                   
DEBN ERDVA1_082027   DEBN ERDVA1 H886837                       58.918,12       0,00 10403 - Títulos Privados-Debêntures simples                  ERDV - ECORODOVIAS CONCESSOES SERVICOS SA                   
DEBN ERDVA1_082027   DEBN ERDVA1 H886837                       17.139,82       0,00 10403 - Títulos Privados-Debêntures simples                  ERDV - ECORODOVIAS CONCESSOES SERVICOS SA                   
DEBN ERDVA1_082027   DEBN ERDVA1 H886837                      712.373,69       0,01 10403 - Títulos Privados-Debêntures simples                  ERDV - ECORODOVIAS CONCESSOES SERVICOS SA                   
DEBN ERDVA1_082027   DEBN ERDVA1 H886837                        4.284,95       0,00 10403 - Títulos Privados-Debêntures simples                  ERDV - ECORODOVIAS CONCESSOES SERVICOS SA                   
DEBN ERDVA1_082027   DEBN ERDVA1 H886837                      250.669,84       0,00 10403 - Títulos Privados-Debêntures simples                  ERDV - ECORODOVIAS CONCESSOES SERVICOS SA                   
DEBN ERDVA1_082027   DEBN ERDVA1 H886837                    1.313.338,56       0,02 10403 - Títulos Privados-Debêntures simples                  ERDV - ECORODOVIAS CONCESSOES SERVICOS SA                   
DEBN ERDVA1_082027   DEBN ERDVA1 H886837                       32.137,16       0,00 10403 - Títulos Privados-Debêntures simples                  ERDV - ECORODOVIAS CONCESSOES SERVICOS SA                   
DEBN ANHBA4_062028   DEBN ANHBA4 I243525                       81.168,85       0,00 10403 - Títulos Privados-Debêntures simples                  ANHB - CONCESSIONARIA SISTEMA ANHANGUERA BANDEIRANTES S/A   
DEBN ERDVA1_082027   DEBN ERDVA1 H886837                    2.632.033,32       0,05 10403 - Títulos Privados-Debêntures simples                  ERDV - ECORODOVIAS CONCESSOES SERVICOS SA                   
DEBN ERDVA1_082027   DEBN ERDVA1 H886837                       32.137,16       0,00 10403 - Títulos Privados-Debêntures simples                  ERDV - ECORODOVIAS CONCESSOES SERVICOS SA                   
DEBN ERDVA1_082027   DEBN ERDVA1 H886837                      128.548,64       0,00 10403 - Títulos Privados-Debêntures simples                  ERDV - ECORODOVIAS CONCESSOES SERVICOS SA                   
DEBN ERDVA1_082027   DEBN ERDVA1 H886837                       85.699,09       0,00 10403 - Títulos Privados-Debêntures simples                  ERDV - ECORODOVIAS CONCESSOES SERVICOS SA                   
DEBN ERDVA1_082027   DEBN ERDVA1 H886837                      116.765,01       0,00 10403 - Títulos Privados-Debêntures simples                  ERDV - ECORODOVIAS CONCESSOES SERVICOS SA                   
DEBN ERDVA1_082027   DEBN ERDVA1 H886837                       73.915,47       0,00 10403 - Títulos Privados-Debêntures simples                  ERDV - ECORODOVIAS CONCESSOES SERVICOS SA                   
DEBN ERDVA1_082027   DEBN ERDVA1 H886837                       59.989,37       0,00 10403 - Títulos Privados-Debêntures simples                  ERDV - ECORODOVIAS CONCESSOES SERVICOS SA                   
DEBN ERDVA1_082027   DEBN ERDVA1 H886837                       39.635,83       0,00 10403 - Títulos Privados-Debêntures simples                  ERDV - ECORODOVIAS CONCESSOES SERVICOS SA                   
DEBN ERDVA1_082027   DEBN ERDVA1 H886837                       52.490,69       0,00 10403 - Títulos Privados-Debêntures simples                  ERDV - ECORODOVIAS CONCESSOES SERVICOS SA                   
DEBN ERDVA1_082027   DEBN ERDVA1 H886837                       52.490,69       0,00 10403 - Títulos Privados-Debêntures simples                  ERDV - ECORODOVIAS CONCESSOES SERVICOS SA                   
DEBN ANHBA4_062028   DEBN ANHBA4 I243525                      535.922,52       0,01 10403 - Títulos Privados-Debêntures simples                  ANHB - CONCESSIONARIA SISTEMA ANHANGUERA BANDEIRANTES S/A   
DEBN ERDVA1_082027   DEBN ERDVA1 H886837                       10.712,39       0,00 10403 - Títulos Privados-Debêntures simples                  ERDV - ECORODOVIAS CONCESSOES SERVICOS SA                   
DEBN ERDVA1_082027   DEBN ERDVA1 H886837                       23.567,25       0,00 10403 - Títulos Privados-Debêntures simples                  ERDV - ECORODOVIAS CONCESSOES SERVICOS SA                   
DEBN ERDVA1_082027   DEBN ERDVA1 H886837                      409.213,16       0,01 10403 - Títulos Privados-Debêntures simples                  ERDV - ECORODOVIAS CONCESSOES SERVICOS SA                   
DEBN ERDVA1_082027   DEBN ERDVA1 H886837                       67.488,03       0,00 10403 - Títulos Privados-Debêntures simples                  ERDV - ECORODOVIAS CONCESSOES SERVICOS SA                   
DEBN ERDVA1_082027   DEBN ERDVA1 H886837                      101.767,67       0,00 10403 - Títulos Privados-Debêntures simples                  ERDV - ECORODOVIAS CONCESSOES SERVICOS SA                   
DEBN ERDVA1_082027   DEBN ERDVA1 H886837                       18.211,06       0,00 10403 - Títulos Privados-Debêntures simples                  ERDV - ECORODOVIAS CONCESSOES SERVICOS SA                   
DEBN ERDVA1_082027   DEBN ERDVA1 H886837                       41.778,31       0,00 10403 - Títulos Privados-Debêntures simples                  ERDV - ECORODOVIAS CONCESSOES SERVICOS SA                   
DEBN ERDVA1_082027   DEBN ERDVA1 H886837                       53.561,93       0,00 10403 - Títulos Privados-Debêntures simples                  ERDV - ECORODOVIAS CONCESSOES SERVICOS SA                   
DEBN ERDVA1_082027   DEBN ERDVA1 H886837                       78.200,42       0,00 10403 - Títulos Privados-Debêntures simples                  ERDV - ECORODOVIAS CONCESSOES SERVICOS SA                   
DEBN ERDVA1_082027   DEBN ERDVA1 H886837                   14.126.423,83       0,25 10403 - Títulos Privados-Debêntures simples                  ERDV - ECORODOVIAS CONCESSOES SERVICOS SA                   
DEBN ANHBA4_062028   DEBN ANHBA4 I243525                   63.675.920,29       1,14 10403 - Títulos Privados-Debêntures simples                  ANHB - CONCESSIONARIA SISTEMA ANHANGUERA BANDEIRANTES S/A   
DEBN ERDVA1_082027   DEBN ERDVA1 H886837                       52.490,69       0,00 10403 - Títulos Privados-Debêntures simples                  ERDV - ECORODOVIAS CONCESSOES SERVICOS SA                   
DEBN ERDVA2_062026   DEBN ERDVA2 I252177                      249.986,11       0,00 10403 - Títulos Privados-Debêntures simples                  ERDV - ECORODOVIAS CONCESSOES SERVICOS SA                   
DEBN ERDVA2_062026   DEBN ERDVA2 I252177                      256.184,11       0,00 10403 - Títulos Privados-Debêntures simples                  ERDV - ECORODOVIAS CONCESSOES SERVICOS SA                   
DEBN ERDVA2_062026   DEBN ERDVA2 I252177                       85.739,04       0,00 10403 - Títulos Privados-Debêntures simples                  ERDV - ECORODOVIAS CONCESSOES SERVICOS SA                   
DEBN ERDVA2_062026   DEBN ERDVA2 I252177                    2.064.967,89       0,04 10403 - Títulos Privados-Debêntures simples                  ERDV - ECORODOVIAS CONCESSOES SERVICOS SA                   
DEBN ERDVA2_062026   DEBN ERDVA2 I252177                      277.877,12       0,00 10403 - Títulos Privados-Debêntures simples                  ERDV - ECORODOVIAS CONCESSOES SERVICOS SA                   
DEBN ERDVA2_062026   DEBN ERDVA2 I252177                      251.019,11       0,00 10403 - Títulos Privados-Debêntures simples                  ERDV - ECORODOVIAS CONCESSOES SERVICOS SA                   
DEBN ERDVA2_062026   DEBN ERDVA2 I252177                      348.121,15       0,01 10403 - Títulos Privados-Debêntures simples                  ERDV - ECORODOVIAS CONCESSOES SERVICOS SA                   
DEBN ERDVA2_062026   DEBN ERDVA2 I252177                      282.009,12       0,01 10403 - Títulos Privados-Debêntures simples                  ERDV - ECORODOVIAS CONCESSOES SERVICOS SA                   
DEBN ERDVA2_062026   DEBN ERDVA2 I252177                      186.973,08       0,00 10403 - Títulos Privados-Debêntures simples                  ERDV - ECORODOVIAS CONCESSOES SERVICOS SA                   
DEBN ANHBA4_062028   DEBN ANHBA4 I243525                      380.869,21       0,01 10403 - Títulos Privados-Debêntures simples                  ANHB - CONCESSIONARIA SISTEMA ANHANGUERA BANDEIRANTES S/A   
DEBN ERDVA2_062026   DEBN ERDVA2 I252177                      319.197,14       0,01 10403 - Títulos Privados-Debêntures simples                  ERDV - ECORODOVIAS CONCESSOES SERVICOS SA                   
DEBN ERDVA2_062026   DEBN ERDVA2 I252177                      113.630,05       0,00 10403 - Títulos Privados-Debêntures simples                  ERDV - ECORODOVIAS CONCESSOES SERVICOS SA                   
DEBN ERDVA2_062026   DEBN ERDVA2 I252177                       48.551,02       0,00 10403 - Títulos Privados-Debêntures simples                  ERDV - ECORODOVIAS CONCESSOES SERVICOS SA                   
DEBN ERDVA2_062026   DEBN ERDVA2 I252177                    9.414.766,07       0,17 10403 - Títulos Privados-Debêntures simples                  ERDV - ECORODOVIAS CONCESSOES SERVICOS SA                   
DEBN ERDVA2_062026   DEBN ERDVA2 I252177                      477.246,21       0,01 10403 - Títulos Privados-Debêntures simples                  ERDV - ECORODOVIAS CONCESSOES SERVICOS SA                   
DEBN ERDVA2_062026   DEBN ERDVA2 I252177                      107.432,05       0,00 10403 - Títulos Privados-Debêntures simples                  ERDV - ECORODOVIAS CONCESSOES SERVICOS SA                   
DEBN ERDVA2_062026   DEBN ERDVA2 I252177                      239.656,10       0,00 10403 - Títulos Privados-Debêntures simples                  ERDV - ECORODOVIAS CONCESSOES SERVICOS SA                   
DEBN ERDVA2_062026   DEBN ERDVA2 I252177                    2.616.590,13       0,05 10403 - Títulos Privados-Debêntures simples                  ERDV - ECORODOVIAS CONCESSOES SERVICOS SA                   
DEBN ERDVA2_062026   DEBN ERDVA2 I252177                   64.934.408,10       1,16 10403 - Títulos Privados-Debêntures simples                  ERDV - ECORODOVIAS CONCESSOES SERVICOS SA                   
DEBN ERDVA2_062026   DEBN ERDVA2 I252177                      914.205,40       0,02 10403 - Títulos Privados-Debêntures simples                  ERDV - ECORODOVIAS CONCESSOES SERVICOS SA                   
DEBN ANHBA4_062028   DEBN ANHBA4 I243525                      118.631,39       0,00 10403 - Títulos Privados-Debêntures simples                  ANHB - CONCESSIONARIA SISTEMA ANHANGUERA BANDEIRANTES S/A   
DEBN ERDVA2_062026   DEBN ERDVA2 I252177                    6.093.669,64       0,11 10403 - Títulos Privados-Debêntures simples                  ERDV - ECORODOVIAS CONCESSOES SERVICOS SA                   
DEBN ERDVA2_062026   DEBN ERDVA2 I252177                      158.049,07       0,00 10403 - Títulos Privados-Debêntures simples                  ERDV - ECORODOVIAS CONCESSOES SERVICOS SA                   
DEBN ERDVA2_062026   DEBN ERDVA2 I252177                      150.818,07       0,00 10403 - Títulos Privados-Debêntures simples                  ERDV - ECORODOVIAS CONCESSOES SERVICOS SA                   
DEBN ERDVA2_062026   DEBN ERDVA2 I252177                      365.682,16       0,01 10403 - Títulos Privados-Debêntures simples                  ERDV - ECORODOVIAS CONCESSOES SERVICOS SA                   
DEBN ERDVA2_062026   DEBN ERDVA2 I252177                       91.937,04       0,00 10403 - Títulos Privados-Debêntures simples                  ERDV - ECORODOVIAS CONCESSOES SERVICOS SA                   
DEBN ERDVA2_062026   DEBN ERDVA2 I252177                      558.853,25       0,01 10403 - Títulos Privados-Debêntures simples                  ERDV - ECORODOVIAS CONCESSOES SERVICOS SA                   
DEBN ERDVA2_062026   DEBN ERDVA2 I252177                       88.838,04       0,00 10403 - Títulos Privados-Debêntures simples                  ERDV - ECORODOVIAS CONCESSOES SERVICOS SA                   
DEBN ERDVA2_062026   DEBN ERDVA2 I252177                       22.726,01       0,00 10403 - Títulos Privados-Debêntures simples                  ERDV - ECORODOVIAS CONCESSOES SERVICOS SA                   
DEBN ERDVA2_062026   DEBN ERDVA2 I252177                      247.920,11       0,00 10403 - Títulos Privados-Debêntures simples                  ERDV - ECORODOVIAS CONCESSOES SERVICOS SA                   
DEBN ERDVA2_062026   DEBN ERDVA2 I252177                      316.098,14       0,01 10403 - Títulos Privados-Debêntures simples                  ERDV - ECORODOVIAS CONCESSOES SERVICOS SA                   
DEBN ANHBA4_062028   DEBN ANHBA4 I243525                      139.443,92       0,00 10403 - Títulos Privados-Debêntures simples                  ANHB - CONCESSIONARIA SISTEMA ANHANGUERA BANDEIRANTES S/A   
DEBN ERDVA2_062026   DEBN ERDVA2 I252177                      248.953,11       0,00 10403 - Títulos Privados-Debêntures simples                  ERDV - ECORODOVIAS CONCESSOES SERVICOS SA                   
DEBN ERDVA2_062026   DEBN ERDVA2 I252177                      607.404,26       0,01 10403 - Títulos Privados-Debêntures simples                  ERDV - ECORODOVIAS CONCESSOES SERVICOS SA                   
DEBN ERDVA2_062026   DEBN ERDVA2 I252177                       92.970,04       0,00 10403 - Títulos Privados-Debêntures simples                  ERDV - ECORODOVIAS CONCESSOES SERVICOS SA                   
DEBN ERDVA2_062026   DEBN ERDVA2 I252177                      193.171,08       0,00 10403 - Títulos Privados-Debêntures simples                  ERDV - ECORODOVIAS CONCESSOES SERVICOS SA                   
DEBN ERDVA2_062026   DEBN ERDVA2 I252177                      153.917,07       0,00 10403 - Títulos Privados-Debêntures simples                  ERDV - ECORODOVIAS CONCESSOES SERVICOS SA                   
DEBN ERDVA2_062026   DEBN ERDVA2 I252177                      401.837,18       0,01 10403 - Títulos Privados-Debêntures simples                  ERDV - ECORODOVIAS CONCESSOES SERVICOS SA                   
DEBN ERDVB3_102030   DEBN ERDVB3 I504231                      118.774,14       0,00 10403 - Títulos Privados-Debêntures simples                  ERDV - ECORODOVIAS CONCESSOES SERVICOS SA                   
DEBN ERDVB3_102030   DEBN ERDVB3 I504231                       70.184,72       0,00 10403 - Títulos Privados-Debêntures simples                  ERDV - ECORODOVIAS CONCESSOES SERVICOS SA                   
DEBN ERDVB3_102030   DEBN ERDVB3 I504231                       42.110,83       0,00 10403 - Títulos Privados-Debêntures simples                  ERDV - ECORODOVIAS CONCESSOES SERVICOS SA                   
DEBN ERDVB3_102030   DEBN ERDVB3 I504231                      103.657,43       0,00 10403 - Títulos Privados-Debêntures simples                  ERDV - ECORODOVIAS CONCESSOES SERVICOS SA                   
DEBN ANHBA4_062028   DEBN ANHBA4 I243525                      229.978,40       0,00 10403 - Títulos Privados-Debêntures simples                  ANHB - CONCESSIONARIA SISTEMA ANHANGUERA BANDEIRANTES S/A   
DEBN ERDVB3_102030   DEBN ERDVB3 I504231                      157.645,68       0,00 10403 - Títulos Privados-Debêntures simples                  ERDV - ECORODOVIAS CONCESSOES SERVICOS SA                   
DEBN ERDVB3_102030   DEBN ERDVB3 I504231                      102.577,67       0,00 10403 - Títulos Privados-Debêntures simples                  ERDV - ECORODOVIAS CONCESSOES SERVICOS SA                   
DEBN ERDVB3_102030   DEBN ERDVB3 I504231                       34.552,48       0,00 10403 - Títulos Privados-Debêntures simples                  ERDV - ECORODOVIAS CONCESSOES SERVICOS SA                   
DEBN ERDVB3_102030   DEBN ERDVB3 I504231                      275.340,06       0,00 10403 - Títulos Privados-Debêntures simples                  ERDV - ECORODOVIAS CONCESSOES SERVICOS SA                   
DEBN ERDVB3_102030   DEBN ERDVB3 I504231                        7.558,35       0,00 10403 - Títulos Privados-Debêntures simples                  ERDV - ECORODOVIAS CONCESSOES SERVICOS SA                   
DEBN ERDVB3_102030   DEBN ERDVB3 I504231                       95.019,31       0,00 10403 - Títulos Privados-Debêntures simples                  ERDV - ECORODOVIAS CONCESSOES SERVICOS SA                   
DEBN ERDVB3_102030   DEBN ERDVB3 I504231                       70.184,72       0,00 10403 - Títulos Privados-Debêntures simples                  ERDV - ECORODOVIAS CONCESSOES SERVICOS SA                   
DEBN ERDVB3_102030   DEBN ERDVB3 I504231                       33.472,71       0,00 10403 - Títulos Privados-Debêntures simples                  ERDV - ECORODOVIAS CONCESSOES SERVICOS SA                   
DEBN ERDVB3_102030   DEBN ERDVB3 I504231                    6.889.979,94       0,12 10403 - Títulos Privados-Debêntures simples                  ERDV - ECORODOVIAS CONCESSOES SERVICOS SA                   
DEBN ERDVB3_102030   DEBN ERDVB3 I504231                       92.859,78       0,00 10403 - Títulos Privados-Debêntures simples                  ERDV - ECORODOVIAS CONCESSOES SERVICOS SA                   
DEBN ANHBA4_062028   DEBN ANHBA4 I243525                      104.062,63       0,00 10403 - Títulos Privados-Debêntures simples                  ANHB - CONCESSIONARIA SISTEMA ANHANGUERA BANDEIRANTES S/A   
DEBN ERDVB3_102030   DEBN ERDVB3 I504231                       92.859,78       0,00 10403 - Títulos Privados-Debêntures simples                  ERDV - ECORODOVIAS CONCESSOES SERVICOS SA                   
DEBN ERDVB3_102030   DEBN ERDVB3 I504231                       91.780,02       0,00 10403 - Títulos Privados-Debêntures simples                  ERDV - ECORODOVIAS CONCESSOES SERVICOS SA                   
DEBN ERDVB3_102030   DEBN ERDVB3 I504231                      117.694,38       0,00 10403 - Títulos Privados-Debêntures simples                  ERDV - ECORODOVIAS CONCESSOES SERVICOS SA                   
DEBN ERDVB3_102030   DEBN ERDVB3 I504231                    2.222.156,20       0,04 10403 - Títulos Privados-Debêntures simples                  ERDV - ECORODOVIAS CONCESSOES SERVICOS SA                   
DEBN ERDVB3_102030   DEBN ERDVB3 I504231                       92.859,78       0,00 10403 - Títulos Privados-Debêntures simples                  ERDV - ECORODOVIAS CONCESSOES SERVICOS SA                   
DEBN ERDVB3_102030   DEBN ERDVB3 I504231                       18.356,00       0,00 10403 - Títulos Privados-Debêntures simples                  ERDV - ECORODOVIAS CONCESSOES SERVICOS SA                   
DEBN ERDVB3_102030   DEBN ERDVB3 I504231                       87.460,96       0,00 10403 - Títulos Privados-Debêntures simples                  ERDV - ECORODOVIAS CONCESSOES SERVICOS SA                   
DEBN ERDVB3_102030   DEBN ERDVB3 I504231                      786.068,86       0,01 10403 - Títulos Privados-Debêntures simples                  ERDV - ECORODOVIAS CONCESSOES SERVICOS SA                   
DEBN ERDVB3_102030   DEBN ERDVB3 I504231                    1.641.242,67       0,03 10403 - Títulos Privados-Debêntures simples                  ERDV - ECORODOVIAS CONCESSOES SERVICOS SA                   
DEBN ERDVB3_102030   DEBN ERDVB3 I504231                       56.147,78       0,00 10403 - Títulos Privados-Debêntures simples                  ERDV - ECORODOVIAS CONCESSOES SERVICOS SA                   
DEBN ANHBA4_062028   DEBN ANHBA4 I243525                      294.497,23       0,01 10403 - Títulos Privados-Debêntures simples                  ANHB - CONCESSIONARIA SISTEMA ANHANGUERA BANDEIRANTES S/A   
DEBN ERDVB3_102030   DEBN ERDVB3 I504231                      183.560,03       0,00 10403 - Títulos Privados-Debêntures simples                  ERDV - ECORODOVIAS CONCESSOES SERVICOS SA                   
DEBN ERDVB3_102030   DEBN ERDVB3 I504231                      136.050,38       0,00 10403 - Títulos Privados-Debêntures simples                  ERDV - ECORODOVIAS CONCESSOES SERVICOS SA                   
DEBN ERDVB3_102030   DEBN ERDVB3 I504231                      177.081,45       0,00 10403 - Títulos Privados-Debêntures simples                  ERDV - ECORODOVIAS CONCESSOES SERVICOS SA                   
DEBN ERDVB3_102030   DEBN ERDVB3 I504231                       32.392,95       0,00 10403 - Títulos Privados-Debêntures simples                  ERDV - ECORODOVIAS CONCESSOES SERVICOS SA                   
DEBN ERDVB3_102030   DEBN ERDVB3 I504231                   23.839.049,84       0,43 10403 - Títulos Privados-Debêntures simples                  ERDV - ECORODOVIAS CONCESSOES SERVICOS SA                   
DEBN ERDVB3_102030   DEBN ERDVB3 I504231                      381.157,02       0,01 10403 - Títulos Privados-Debêntures simples                  ERDV - ECORODOVIAS CONCESSOES SERVICOS SA                   
DEBN ERDVB3_102030   DEBN ERDVB3 I504231                      255.904,28       0,00 10403 - Títulos Privados-Debêntures simples                  ERDV - ECORODOVIAS CONCESSOES SERVICOS SA                   
DEBN EUFA17_032031   DEBN EUFA17 I700271                      109.802,40       0,00 10403 - Títulos Privados-Debêntures simples                  EUFA - EUROFARMA LABORATORIOS S/A                           
DEBN EUFA17_032031   DEBN EUFA17 I700271                   39.785.071,17       0,71 10403 - Títulos Privados-Debêntures simples                  EUFA - EUROFARMA LABORATORIOS S/A                           
DEBN EUFA17_032031   DEBN EUFA17 I700271                   11.118.277,74       0,20 10403 - Títulos Privados-Debêntures simples                  EUFA - EUROFARMA LABORATORIOS S/A                           
DEBN AEGPA0_052029   DEBN AEGPA0 H750651                      287.317,38       0,01 10440 - Títulos Privados-Debêntures Incent. (Lei 12.431)     AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN ANHBA4_062028   DEBN ANHBA4 I243525                      171.703,33       0,00 10403 - Títulos Privados-Debêntures simples                  ANHB - CONCESSIONARIA SISTEMA ANHANGUERA BANDEIRANTES S/A   
DEBN EUFA17_032031   DEBN EUFA17 I700271                   16.640.815,81       0,30 10403 - Títulos Privados-Debêntures simples                  EUFA - EUROFARMA LABORATORIOS S/A                           
DEBN EUFA17_032031   DEBN EUFA17 I700271                  102.146.562,40       1,83 10403 - Títulos Privados-Debêntures simples                  EUFA - EUROFARMA LABORATORIOS S/A                           
DEBN EUFA17_032031   DEBN EUFA17 I700271                       27.189,17       0,00 10403 - Títulos Privados-Debêntures simples                  EUFA - EUROFARMA LABORATORIOS S/A                           
DEBN EUFA17_032031   DEBN EUFA17 I700271                      141.174,52       0,00 10403 - Títulos Privados-Debêntures simples                  EUFA - EUROFARMA LABORATORIOS S/A                           
DEBN EUFA17_032031   DEBN EUFA17 I700271                      420.386,35       0,01 10403 - Títulos Privados-Debêntures simples                  EUFA - EUROFARMA LABORATORIOS S/A                           
DEBN EUFA17_032031   DEBN EUFA17 I700271                      476.856,16       0,01 10403 - Títulos Privados-Debêntures simples                  EUFA - EUROFARMA LABORATORIOS S/A                           
DEBN EUFA17_032031   DEBN EUFA17 I700271                      711.101,29       0,01 10403 - Títulos Privados-Debêntures simples                  EUFA - EUROFARMA LABORATORIOS S/A                           
DEBN EUFA17_032031   DEBN EUFA17 I700271                      296.989,36       0,01 10403 - Títulos Privados-Debêntures simples                  EUFA - EUROFARMA LABORATORIOS S/A                           
DEBN EUFA17_032031   DEBN EUFA17 I700271                      152.677,63       0,00 10403 - Títulos Privados-Debêntures simples                  EUFA - EUROFARMA LABORATORIOS S/A                           
DEBN EUFA17_032031   DEBN EUFA17 I700271                      250.976,92       0,00 10403 - Títulos Privados-Debêntures simples                  EUFA - EUROFARMA LABORATORIOS S/A                           
DEBN ANHBA4_062028   DEBN ANHBA4 I243525                      321.553,51       0,01 10403 - Títulos Privados-Debêntures simples                  ANHB - CONCESSIONARIA SISTEMA ANHANGUERA BANDEIRANTES S/A   
DEBN EUFA17_032031   DEBN EUFA17 I700271                      404.700,29       0,01 10403 - Títulos Privados-Debêntures simples                  EUFA - EUROFARMA LABORATORIOS S/A                           
DEBN EUFA17_032031   DEBN EUFA17 I700271                    1.774.616,00       0,03 10403 - Títulos Privados-Debêntures simples                  EUFA - EUROFARMA LABORATORIOS S/A                           
DEBN EUFA17_032031   DEBN EUFA17 I700271                      518.685,64       0,01 10403 - Títulos Privados-Debêntures simples                  EUFA - EUROFARMA LABORATORIOS S/A                           
DEBN EUFA17_032031   DEBN EUFA17 I700271                      528.097,28       0,01 10403 - Títulos Privados-Debêntures simples                  EUFA - EUROFARMA LABORATORIOS S/A                           
DEBN EUFA17_032031   DEBN EUFA17 I700271                      313.721,16       0,01 10403 - Títulos Privados-Debêntures simples                  EUFA - EUROFARMA LABORATORIOS S/A                           
DEBN EUFA17_032031   DEBN EUFA17 I700271                      925.477,40       0,02 10403 - Títulos Privados-Debêntures simples                  EUFA - EUROFARMA LABORATORIOS S/A                           
DEBN EUFA17_032031   DEBN EUFA17 I700271                      404.700,29       0,01 10403 - Títulos Privados-Debêntures simples                  EUFA - EUROFARMA LABORATORIOS S/A                           
DEBN EUFA17_032031   DEBN EUFA17 I700271                      566.789,55       0,01 10403 - Títulos Privados-Debêntures simples                  EUFA - EUROFARMA LABORATORIOS S/A                           
DEBN EUFA17_032031   DEBN EUFA17 I700271                      453.849,94       0,01 10403 - Títulos Privados-Debêntures simples                  EUFA - EUROFARMA LABORATORIOS S/A                           
DEBN EUFA17_032031   DEBN EUFA17 I700271                      987.175,90       0,02 10403 - Títulos Privados-Debêntures simples                  EUFA - EUROFARMA LABORATORIOS S/A                           
DEBN ANHBA4_062028   DEBN ANHBA4 I243525                       15.609,39       0,00 10403 - Títulos Privados-Debêntures simples                  ANHB - CONCESSIONARIA SISTEMA ANHANGUERA BANDEIRANTES S/A   
DEBN EUFA17_032031   DEBN EUFA17 I700271                      785.348,63       0,01 10403 - Títulos Privados-Debêntures simples                  EUFA - EUROFARMA LABORATORIOS S/A                           
DEBN EUFA17_032031   DEBN EUFA17 I700271                    3.385.051,26       0,06 10403 - Títulos Privados-Debêntures simples                  EUFA - EUROFARMA LABORATORIOS S/A                           
DEBN EUFA17_032031   DEBN EUFA17 I700271                      673.454,74       0,01 10403 - Títulos Privados-Debêntures simples                  EUFA - EUROFARMA LABORATORIOS S/A                           
DEBN EUFA17_032031   DEBN EUFA17 I700271                      522.868,59       0,01 10403 - Títulos Privados-Debêntures simples                  EUFA - EUROFARMA LABORATORIOS S/A                           
DEBN EUFA17_032031   DEBN EUFA17 I700271                      144.311,73       0,00 10403 - Títulos Privados-Debêntures simples                  EUFA - EUROFARMA LABORATORIOS S/A                           
DEBN EUFA17_032031   DEBN EUFA17 I700271                      406.791,76       0,01 10403 - Títulos Privados-Debêntures simples                  EUFA - EUROFARMA LABORATORIOS S/A                           
DEBN EUFA17_032031   DEBN EUFA17 I700271                      185.095,48       0,00 10403 - Títulos Privados-Debêntures simples                  EUFA - EUROFARMA LABORATORIOS S/A                           
DEBN EUFA17_032031   DEBN EUFA17 I700271                      304.309,52       0,01 10403 - Títulos Privados-Debêntures simples                  EUFA - EUROFARMA LABORATORIOS S/A                           
DEBN EUFA18_092028   DEBN EUFA18_092028 I978578                41.759,96       0,00 10403 - Títulos Privados-Debêntures simples                  EUFA - EUROFARMA LABORATORIOS S/A                           
DEBN EUFA18_092028   DEBN EUFA18_092028 I978578                 6.263,99       0,00 10403 - Títulos Privados-Debêntures simples                  EUFA - EUROFARMA LABORATORIOS S/A                           
DEBN ANHBA4_062028   DEBN ANHBA4 I243525                      551.531,92       0,01 10403 - Títulos Privados-Debêntures simples                  ANHB - CONCESSIONARIA SISTEMA ANHANGUERA BANDEIRANTES S/A   
DEBN EUFA18_092028   DEBN EUFA18_092028 I978578                64.727,94       0,00 10403 - Títulos Privados-Debêntures simples                  EUFA - EUROFARMA LABORATORIOS S/A                           
DEBN EUFA18_092028   DEBN EUFA18_092028 I978578                15.659,98       0,00 10403 - Títulos Privados-Debêntures simples                  EUFA - EUROFARMA LABORATORIOS S/A                           
DEBN EUFA18_092028   DEBN EUFA18_092028 I978578                19.835,98       0,00 10403 - Títulos Privados-Debêntures simples                  EUFA - EUROFARMA LABORATORIOS S/A                           
DEBN EUFA18_092028   DEBN EUFA18_092028 I978578                58.463,94       0,00 10403 - Títulos Privados-Debêntures simples                  EUFA - EUROFARMA LABORATORIOS S/A                           
DEBN EUFA18_092028   DEBN EUFA18_092028 I978578                10.439,99       0,00 10403 - Títulos Privados-Debêntures simples                  EUFA - EUROFARMA LABORATORIOS S/A                           
DEBN EUFA18_092028   DEBN EUFA18_092028 I978578                62.639,94       0,00 10403 - Títulos Privados-Debêntures simples                  EUFA - EUROFARMA LABORATORIOS S/A                           
DEBN EUFA18_092028   DEBN EUFA18_092028 I978578                28.187,97       0,00 10403 - Títulos Privados-Debêntures simples                  EUFA - EUROFARMA LABORATORIOS S/A                           
DEBN EUFA18_092028   DEBN EUFA18_092028 I978578                 1.044,00       0,00 10403 - Títulos Privados-Debêntures simples                  EUFA - EUROFARMA LABORATORIOS S/A                           
DEBN EUFA18_092028   DEBN EUFA18_092028 I978578                26.099,97       0,00 10403 - Títulos Privados-Debêntures simples                  EUFA - EUROFARMA LABORATORIOS S/A                           
DEBN EUFA18_092028   DEBN EUFA18_092028 I978578             8.881.299,30       0,16 10403 - Títulos Privados-Debêntures simples                  EUFA - EUROFARMA LABORATORIOS S/A                           
DEBN ANHBA4_062028   DEBN ANHBA4 I243525                      319.472,26       0,01 10403 - Títulos Privados-Debêntures simples                  ANHB - CONCESSIONARIA SISTEMA ANHANGUERA BANDEIRANTES S/A   
DEBN EUFA18_092028   DEBN EUFA18_092028 I978578                34.451,97       0,00 10403 - Títulos Privados-Debêntures simples                  EUFA - EUROFARMA LABORATORIOS S/A                           
DEBN EUFA18_092028   DEBN EUFA18_092028 I978578                43.847,96       0,00 10403 - Títulos Privados-Debêntures simples                  EUFA - EUROFARMA LABORATORIOS S/A                           
DEBN EUFA18_092028   DEBN EUFA18_092028 I978578                11.483,99       0,00 10403 - Títulos Privados-Debêntures simples                  EUFA - EUROFARMA LABORATORIOS S/A                           
DEBN EUFA18_092028   DEBN EUFA18_092028 I978578                15.659,98       0,00 10403 - Títulos Privados-Debêntures simples                  EUFA - EUROFARMA LABORATORIOS S/A                           
DEBN EUFA18_092028   DEBN EUFA18_092028 I978578                11.483,99       0,00 10403 - Títulos Privados-Debêntures simples                  EUFA - EUROFARMA LABORATORIOS S/A                           
DEBN EUFA18_092028   DEBN EUFA18_092028 I978578                33.407,97       0,00 10403 - Títulos Privados-Debêntures simples                  EUFA - EUROFARMA LABORATORIOS S/A                           
DEBN EUFA18_092028   DEBN EUFA18_092028 I978578                26.099,97       0,00 10403 - Títulos Privados-Debêntures simples                  EUFA - EUROFARMA LABORATORIOS S/A                           
DEBN EUFA18_092028   DEBN EUFA18_092028 I978578                18.791,98       0,00 10403 - Títulos Privados-Debêntures simples                  EUFA - EUROFARMA LABORATORIOS S/A                           
DEBN EUFA18_092028   DEBN EUFA18_092028 I978578                37.583,96       0,00 10403 - Títulos Privados-Debêntures simples                  EUFA - EUROFARMA LABORATORIOS S/A                           
DEBN EUFA18_092028   DEBN EUFA18_092028 I978578                35.495,96       0,00 10403 - Títulos Privados-Debêntures simples                  EUFA - EUROFARMA LABORATORIOS S/A                           
DEBN ANHBA4_062028   DEBN ANHBA4 I243525                       86.371,98       0,00 10403 - Títulos Privados-Debêntures simples                  ANHB - CONCESSIONARIA SISTEMA ANHANGUERA BANDEIRANTES S/A   
DEBN GUAR16_102027   DEBN GUAR16 I488305                      127.178,80       0,00 10403 - Títulos Privados-Debêntures simples                  GUAR - GUARARAPES CONFECCOES SA (EX CONFECCOES GUARARAPES   
DEBN GUAR16_102027   DEBN GUAR16 I488305                        1.042,45       0,00 10403 - Títulos Privados-Debêntures simples                  GUAR - GUARARAPES CONFECCOES SA (EX CONFECCOES GUARARAPES   
DEBN GUAR16_102027   DEBN GUAR16 I488305                       84.438,38       0,00 10403 - Títulos Privados-Debêntures simples                  GUAR - GUARARAPES CONFECCOES SA (EX CONFECCOES GUARARAPES   
DEBN GUAR16_102027   DEBN GUAR16 I488305                    3.029.357,33       0,05 10403 - Títulos Privados-Debêntures simples                  GUAR - GUARARAPES CONFECCOES SA (EX CONFECCOES GUARARAPES   
DEBN GUAR16_102027   DEBN GUAR16 I488305                      117.796,76       0,00 10403 - Títulos Privados-Debêntures simples                  GUAR - GUARARAPES CONFECCOES SA (EX CONFECCOES GUARARAPES   
DEBN GUAR16_102027   DEBN GUAR16 I488305                       97.990,23       0,00 10403 - Títulos Privados-Debêntures simples                  GUAR - GUARARAPES CONFECCOES SA (EX CONFECCOES GUARARAPES   
DEBN GUAR16_102027   DEBN GUAR16 I488305                    2.031.733,46       0,04 10403 - Títulos Privados-Debêntures simples                  GUAR - GUARARAPES CONFECCOES SA (EX CONFECCOES GUARARAPES   
DEBN GUAR16_102027   DEBN GUAR16 I488305                       89.650,63       0,00 10403 - Títulos Privados-Debêntures simples                  GUAR - GUARARAPES CONFECCOES SA (EX CONFECCOES GUARARAPES   
DEBN GUAR16_102027   DEBN GUAR16 I488305                       65.674,30       0,00 10403 - Títulos Privados-Debêntures simples                  GUAR - GUARARAPES CONFECCOES SA (EX CONFECCOES GUARARAPES   
DEBN GUAR16_102027   DEBN GUAR16 I488305                      201.192,70       0,00 10403 - Títulos Privados-Debêntures simples                  GUAR - GUARARAPES CONFECCOES SA (EX CONFECCOES GUARARAPES   
DEBN ANHBA4_062028   DEBN ANHBA4 I243525                       52.031,31       0,00 10403 - Títulos Privados-Debêntures simples                  ANHB - CONCESSIONARIA SISTEMA ANHANGUERA BANDEIRANTES S/A   
DEBN GUAR16_102027   DEBN GUAR16 I488305                       63.589,40       0,00 10403 - Títulos Privados-Debêntures simples                  GUAR - GUARARAPES CONFECCOES SA (EX CONFECCOES GUARARAPES   
DEBN GUAR16_102027   DEBN GUAR16 I488305                        5.212,25       0,00 10403 - Títulos Privados-Debêntures simples                  GUAR - GUARARAPES CONFECCOES SA (EX CONFECCOES GUARARAPES   
DEBN GUAR16_102027   DEBN GUAR16 I488305                       35.443,27       0,00 10403 - Títulos Privados-Debêntures simples                  GUAR - GUARARAPES CONFECCOES SA (EX CONFECCOES GUARARAPES   
DEBN GUAR16_102027   DEBN GUAR16 I488305                       41.697,97       0,00 10403 - Títulos Privados-Debêntures simples                  GUAR - GUARARAPES CONFECCOES SA (EX CONFECCOES GUARARAPES   
DEBN GUAR16_102027   DEBN GUAR16 I488305                      157.409,82       0,00 10403 - Títulos Privados-Debêntures simples                  GUAR - GUARARAPES CONFECCOES SA (EX CONFECCOES GUARARAPES   
DEBN GUAR16_102027   DEBN GUAR16 I488305                       67.759,20       0,00 10403 - Títulos Privados-Debêntures simples                  GUAR - GUARARAPES CONFECCOES SA (EX CONFECCOES GUARARAPES   
DEBN GUAR16_102027   DEBN GUAR16 I488305                       10.424,49       0,00 10403 - Títulos Privados-Debêntures simples                  GUAR - GUARARAPES CONFECCOES SA (EX CONFECCOES GUARARAPES   
DEBN GUAR16_102027   DEBN GUAR16 I488305                      699.483,40       0,01 10403 - Títulos Privados-Debêntures simples                  GUAR - GUARARAPES CONFECCOES SA (EX CONFECCOES GUARARAPES   
DEBN GUAR16_102027   DEBN GUAR16 I488305                       91.735,53       0,00 10403 - Títulos Privados-Debêntures simples                  GUAR - GUARARAPES CONFECCOES SA (EX CONFECCOES GUARARAPES   
DEBN GUAR16_102027   DEBN GUAR16 I488305                       85.480,83       0,00 10403 - Títulos Privados-Debêntures simples                  GUAR - GUARARAPES CONFECCOES SA (EX CONFECCOES GUARARAPES   
DEBN ANHBA4_062028   DEBN ANHBA4 I243525                      400.641,11       0,01 10403 - Títulos Privados-Debêntures simples                  ANHB - CONCESSIONARIA SISTEMA ANHANGUERA BANDEIRANTES S/A   
DEBN GUAR16_102027   DEBN GUAR16 I488305                      119.881,66       0,00 10403 - Títulos Privados-Debêntures simples                  GUAR - GUARARAPES CONFECCOES SA (EX CONFECCOES GUARARAPES   
DEBN GUAR16_102027   DEBN GUAR16 I488305                    3.193.021,86       0,06 10403 - Títulos Privados-Debêntures simples                  GUAR - GUARARAPES CONFECCOES SA (EX CONFECCOES GUARARAPES   
DEBN GUAR16_102027   DEBN GUAR16 I488305                       50.037,56       0,00 10403 - Títulos Privados-Debêntures simples                  GUAR - GUARARAPES CONFECCOES SA (EX CONFECCOES GUARARAPES   
DEBN GUAR16_102027   DEBN GUAR16 I488305                       66.716,75       0,00 10403 - Títulos Privados-Debêntures simples                  GUAR - GUARARAPES CONFECCOES SA (EX CONFECCOES GUARARAPES   
DEBN GUAR16_102027   DEBN GUAR16 I488305                    1.165.458,19       0,02 10403 - Títulos Privados-Debêntures simples                  GUAR - GUARARAPES CONFECCOES SA (EX CONFECCOES GUARARAPES   
DEBN GUAR16_102027   DEBN GUAR16 I488305                    8.458.432,71       0,15 10403 - Títulos Privados-Debêntures simples                  GUAR - GUARARAPES CONFECCOES SA (EX CONFECCOES GUARARAPES   
DEBN GUAR16_102027   DEBN GUAR16 I488305                       74.013,89       0,00 10403 - Títulos Privados-Debêntures simples                  GUAR - GUARARAPES CONFECCOES SA (EX CONFECCOES GUARARAPES   
DEBN GUAR16_102027   DEBN GUAR16 I488305                    6.760.282,97       0,12 10403 - Títulos Privados-Debêntures simples                  GUAR - GUARARAPES CONFECCOES SA (EX CONFECCOES GUARARAPES   
DEBN GUAR16_102027   DEBN GUAR16 I488305                      546.243,37       0,01 10403 - Títulos Privados-Debêntures simples                  GUAR - GUARARAPES CONFECCOES SA (EX CONFECCOES GUARARAPES   
DEBN HAPV12_042027   DEBN HAPV12 H677807                       19.739,19       0,00 10403 - Títulos Privados-Debêntures simples                  HAPV - HAPVIDA PARTICIPACOES INVESTIMENTO SA                
DEBN ANHBA4_062028   DEBN ANHBA4 I243525                      174.825,21       0,00 10403 - Títulos Privados-Debêntures simples                  ANHB - CONCESSIONARIA SISTEMA ANHANGUERA BANDEIRANTES S/A   
DEBN HAPV12_042027   DEBN HAPV12 H677807                        9.350,14       0,00 10403 - Títulos Privados-Debêntures simples                  HAPV - HAPVIDA PARTICIPACOES INVESTIMENTO SA                
DEBN HAPV12_042027   DEBN HAPV12 H677807                    1.586.407,74       0,03 10403 - Títulos Privados-Debêntures simples                  HAPV - HAPVIDA PARTICIPACOES INVESTIMENTO SA                
DEBN HAPV12_042027   DEBN HAPV12 H677807                       17.661,38       0,00 10403 - Títulos Privados-Debêntures simples                  HAPV - HAPVIDA PARTICIPACOES INVESTIMENTO SA                
DEBN HAPV12_042027   DEBN HAPV12 H677807                    1.141.756,46       0,02 10403 - Títulos Privados-Debêntures simples                  HAPV - HAPVIDA PARTICIPACOES INVESTIMENTO SA                
DEBN HAPV12_042027   DEBN HAPV12 H677807                       65.451,00       0,00 10403 - Títulos Privados-Debêntures simples                  HAPV - HAPVIDA PARTICIPACOES INVESTIMENTO SA                
DEBN HAPV12_042027   DEBN HAPV12 H677807                        8.311,24       0,00 10403 - Títulos Privados-Debêntures simples                  HAPV - HAPVIDA PARTICIPACOES INVESTIMENTO SA                
DEBN HAPV12_042027   DEBN HAPV12 H677807                      520.491,34       0,01 10403 - Títulos Privados-Debêntures simples                  HAPV - HAPVIDA PARTICIPACOES INVESTIMENTO SA                
DEBN HAPV12_042027   DEBN HAPV12 H677807                      346.994,23       0,01 10403 - Títulos Privados-Debêntures simples                  HAPV - HAPVIDA PARTICIPACOES INVESTIMENTO SA                
DEBN HAPV12_042027   DEBN HAPV12 H677807                       17.661,38       0,00 10403 - Títulos Privados-Debêntures simples                  HAPV - HAPVIDA PARTICIPACOES INVESTIMENTO SA                
DEBN HAPV12_042027   DEBN HAPV12 H677807                    1.491.867,40       0,03 10403 - Títulos Privados-Debêntures simples                  HAPV - HAPVIDA PARTICIPACOES INVESTIMENTO SA                
DEBN ANHBA4_062028   DEBN ANHBA4 I243525                    2.154.096,34       0,04 10403 - Títulos Privados-Debêntures simples                  ANHB - CONCESSIONARIA SISTEMA ANHANGUERA BANDEIRANTES S/A   
DEBN HAPV12_042027   DEBN HAPV12 H677807                    1.184.351,56       0,02 10403 - Títulos Privados-Debêntures simples                  HAPV - HAPVIDA PARTICIPACOES INVESTIMENTO SA                
DEBN HAPV12_042027   DEBN HAPV12 H677807                    1.310.059,05       0,02 10403 - Títulos Privados-Debêntures simples                  HAPV - HAPVIDA PARTICIPACOES INVESTIMENTO SA                
DEBN HAPV12_042027   DEBN HAPV12 H677807                    3.147.881,77       0,06 10403 - Títulos Privados-Debêntures simples                  HAPV - HAPVIDA PARTICIPACOES INVESTIMENTO SA                
DEBN HAPV13_052029   DEBN HAPV13 I497320                    3.689.896,10       0,07 10403 - Títulos Privados-Debêntures simples                  HAPV - HAPVIDA PARTICIPACOES INVESTIMENTO SA                
DEBN HAPV13_052029   DEBN HAPV13 I497320                       42.424,49       0,00 10403 - Títulos Privados-Debêntures simples                  HAPV - HAPVIDA PARTICIPACOES INVESTIMENTO SA                
DEBN HAPV13_052029   DEBN HAPV13 I497320                   13.809.689,66       0,25 10403 - Títulos Privados-Debêntures simples                  HAPV - HAPVIDA PARTICIPACOES INVESTIMENTO SA                
DEBN HAPV13_052029   DEBN HAPV13 I497320                   16.776.299,90       0,30 10403 - Títulos Privados-Debêntures simples                  HAPV - HAPVIDA PARTICIPACOES INVESTIMENTO SA                
DEBN HAPV13_052029   DEBN HAPV13 I497320                    1.151.669,76       0,02 10403 - Títulos Privados-Debêntures simples                  HAPV - HAPVIDA PARTICIPACOES INVESTIMENTO SA                
DEBN HAPV13_052029   DEBN HAPV13 I497320                       61.049,88       0,00 10403 - Títulos Privados-Debêntures simples                  HAPV - HAPVIDA PARTICIPACOES INVESTIMENTO SA                
DEBN HAPV13_052029   DEBN HAPV13 I497320                      218.330,92       0,00 10403 - Títulos Privados-Debêntures simples                  HAPV - HAPVIDA PARTICIPACOES INVESTIMENTO SA                
CRA_0220099D         CRA_0220099D CRA  H949490                 33.883,30       0,00 10444 - Títulos Privados-Certif.Receb. Agronegócio (CRA)     ECOA - ECO SECURITIZADORA DIREITOS CREDITORIOS AGRONEGOCI   
DEBN AEGPA0_052029   DEBN AEGPA0 H750651                      118.854,31       0,00 10440 - Títulos Privados-Debêntures Incent. (Lei 12.431)     AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN ANHBA4_062028   DEBN ANHBA4 I243525                       79.087,60       0,00 10403 - Títulos Privados-Debêntures simples                  ANHB - CONCESSIONARIA SISTEMA ANHANGUERA BANDEIRANTES S/A   
DEBN HAPV13_052029   DEBN HAPV13 I497320                       62.084,62       0,00 10403 - Títulos Privados-Debêntures simples                  HAPV - HAPVIDA PARTICIPACOES INVESTIMENTO SA                
DEBN HAPV13_052029   DEBN HAPV13 I497320                    1.731.126,24       0,03 10403 - Títulos Privados-Debêntures simples                  HAPV - HAPVIDA PARTICIPACOES INVESTIMENTO SA                
DEBN HAPV13_052029   DEBN HAPV13 I497320                       30.007,57       0,00 10403 - Títulos Privados-Debêntures simples                  HAPV - HAPVIDA PARTICIPACOES INVESTIMENTO SA                
DEBN HAPV13_052029   DEBN HAPV13 I497320                       46.563,47       0,00 10403 - Títulos Privados-Debêntures simples                  HAPV - HAPVIDA PARTICIPACOES INVESTIMENTO SA                
DEBN HAPV15_012030   DEBN HAPV15 I783879A                       2.043,91       0,00 10403 - Títulos Privados-Debêntures simples                  HAPV - HAPVIDA PARTICIPACOES INVESTIMENTO SA                
DEBN HAPV15_012030   DEBN HAPV15 I783879A                     134.898,21       0,00 10403 - Títulos Privados-Debêntures simples                  HAPV - HAPVIDA PARTICIPACOES INVESTIMENTO SA                
DEBN HAPV15_012030   DEBN HAPV15 I783879A                     285.125,77       0,01 10403 - Títulos Privados-Debêntures simples                  HAPV - HAPVIDA PARTICIPACOES INVESTIMENTO SA                
DEBN HAPV15_012030   DEBN HAPV15 I783879A                       5.109,78       0,00 10403 - Títulos Privados-Debêntures simples                  HAPV - HAPVIDA PARTICIPACOES INVESTIMENTO SA                
DEBN HAPV15_012030   DEBN HAPV15 I783879A                      16.351,30       0,00 10403 - Títulos Privados-Debêntures simples                  HAPV - HAPVIDA PARTICIPACOES INVESTIMENTO SA                
DEBN HAPV15_012030   DEBN HAPV15 I783879A                   3.158.866,51       0,06 10403 - Títulos Privados-Debêntures simples                  HAPV - HAPVIDA PARTICIPACOES INVESTIMENTO SA                
DEBN ANHBA4_062028   DEBN ANHBA4 I243525                      443.306,78       0,01 10403 - Títulos Privados-Debêntures simples                  ANHB - CONCESSIONARIA SISTEMA ANHANGUERA BANDEIRANTES S/A   
DEBN HAPV17_052031   DEBN HAPV17 I779684                   42.652.655,72       0,76 10403 - Títulos Privados-Debêntures simples                  HAPV - HAPVIDA PARTICIPACOES INVESTIMENTO SA                
DEBN HAPV17_052031   DEBN HAPV17 I779684                       40.250,04       0,00 10403 - Títulos Privados-Debêntures simples                  HAPV - HAPVIDA PARTICIPACOES INVESTIMENTO SA                
DEBN HAPV17_052031   DEBN HAPV17 I779684                    2.050.687,84       0,04 10403 - Títulos Privados-Debêntures simples                  HAPV - HAPVIDA PARTICIPACOES INVESTIMENTO SA                
DEBN HAPV17_052031   DEBN HAPV17 I779684                    3.012.560,55       0,05 10403 - Títulos Privados-Debêntures simples                  HAPV - HAPVIDA PARTICIPACOES INVESTIMENTO SA                
DEBN HAPV17_052031   DEBN HAPV17 I779684                      272.461,80       0,00 10403 - Títulos Privados-Debêntures simples                  HAPV - HAPVIDA PARTICIPACOES INVESTIMENTO SA                
DEBN HAPV17_052031   DEBN HAPV17 I779684                      116.621,91       0,00 10403 - Títulos Privados-Debêntures simples                  HAPV - HAPVIDA PARTICIPACOES INVESTIMENTO SA                
DEBN HAPV17_052031   DEBN HAPV17 I779684                      899.949,57       0,02 10403 - Títulos Privados-Debêntures simples                  HAPV - HAPVIDA PARTICIPACOES INVESTIMENTO SA                
DEBN HAPV17_052031   DEBN HAPV17 I779684                    4.330.491,27       0,08 10403 - Títulos Privados-Debêntures simples                  HAPV - HAPVIDA PARTICIPACOES INVESTIMENTO SA                
DEBN HAPV21_072026   DEBN HAPV21                               23.200,62       0,00 10403 - Títulos Privados-Debêntures simples                  HAPV - HAPVIDA PARTICIPACOES INVESTIMENTO SA                
DEBN HAPV21_072026   DEBN HAPV21                               65.566,96       0,00 10403 - Títulos Privados-Debêntures simples                  HAPV - HAPVIDA PARTICIPACOES INVESTIMENTO SA                
DEBN ANHBA4_062028   DEBN ANHBA4 I243525                      228.937,78       0,00 10403 - Títulos Privados-Debêntures simples                  ANHB - CONCESSIONARIA SISTEMA ANHANGUERA BANDEIRANTES S/A   
DEBN HAPV21_072026   DEBN HAPV21                               29.252,95       0,00 10403 - Títulos Privados-Debêntures simples                  HAPV - HAPVIDA PARTICIPACOES INVESTIMENTO SA                
DEBN HAPV21_072026   DEBN HAPV21                               33.287,84       0,00 10403 - Títulos Privados-Debêntures simples                  HAPV - HAPVIDA PARTICIPACOES INVESTIMENTO SA                
DEBN HAPV21_072026   DEBN HAPV21                               62.540,79       0,00 10403 - Títulos Privados-Debêntures simples                  HAPV - HAPVIDA PARTICIPACOES INVESTIMENTO SA                
DEBN HAPV21_072026   DEBN HAPV21                               37.322,73       0,00 10403 - Títulos Privados-Debêntures simples                  HAPV - HAPVIDA PARTICIPACOES INVESTIMENTO SA                
DEBN HAPV21_072026   DEBN HAPV21                               17.148,28       0,00 10403 - Títulos Privados-Debêntures simples                  HAPV - HAPVIDA PARTICIPACOES INVESTIMENTO SA                
DEBN HAPV21_072026   DEBN HAPV21                              160.386,87       0,00 10403 - Títulos Privados-Debêntures simples                  HAPV - HAPVIDA PARTICIPACOES INVESTIMENTO SA                
DEBN HAPV21_072026   DEBN HAPV21                              135.168,81       0,00 10403 - Títulos Privados-Debêntures simples                  HAPV - HAPVIDA PARTICIPACOES INVESTIMENTO SA                
DEBN HAPV21_072026   DEBN HAPV21                               26.226,78       0,00 10403 - Títulos Privados-Debêntures simples                  HAPV - HAPVIDA PARTICIPACOES INVESTIMENTO SA                
DEBN HAPV21_072026   DEBN HAPV21                               66.575,68       0,00 10403 - Títulos Privados-Debêntures simples                  HAPV - HAPVIDA PARTICIPACOES INVESTIMENTO SA                
DEBN HAPV21_072026   DEBN HAPV21                              157.360,71       0,00 10403 - Títulos Privados-Debêntures simples                  HAPV - HAPVIDA PARTICIPACOES INVESTIMENTO SA                
DEBN ANHBA4_062028   DEBN ANHBA4 I243525                      247.669,05       0,00 10403 - Títulos Privados-Debêntures simples                  ANHB - CONCESSIONARIA SISTEMA ANHANGUERA BANDEIRANTES S/A   
DEBN HAPV21_072026   DEBN HAPV21                               23.200,62       0,00 10403 - Títulos Privados-Debêntures simples                  HAPV - HAPVIDA PARTICIPACOES INVESTIMENTO SA                
DEBN HAPV21_072026   DEBN HAPV21                               54.471,01       0,00 10403 - Títulos Privados-Debêntures simples                  HAPV - HAPVIDA PARTICIPACOES INVESTIMENTO SA                
DEBN HAPV21_072026   DEBN HAPV21                               59.514,63       0,00 10403 - Títulos Privados-Debêntures simples                  HAPV - HAPVIDA PARTICIPACOES INVESTIMENTO SA                
DEBN HAPV21_072026   DEBN HAPV21                              105.915,86       0,00 10403 - Títulos Privados-Debêntures simples                  HAPV - HAPVIDA PARTICIPACOES INVESTIMENTO SA                
DEBN HAPV21_072026   DEBN HAPV21                              175.517,71       0,00 10403 - Títulos Privados-Debêntures simples                  HAPV - HAPVIDA PARTICIPACOES INVESTIMENTO SA                
DEBN HAPV21_072026   DEBN HAPV21                              515.457,18       0,01 10403 - Títulos Privados-Debêntures simples                  HAPV - HAPVIDA PARTICIPACOES INVESTIMENTO SA                
DEBN HAPV21_072026   DEBN HAPV21                                9.078,50       0,00 10403 - Títulos Privados-Debêntures simples                  HAPV - HAPVIDA PARTICIPACOES INVESTIMENTO SA                
DEBN HAPV21_072026   DEBN HAPV21                               68.593,13       0,00 10403 - Títulos Privados-Debêntures simples                  HAPV - HAPVIDA PARTICIPACOES INVESTIMENTO SA                
DEBN HAPV21_072026   DEBN HAPV21                                5.043,61       0,00 10403 - Títulos Privados-Debêntures simples                  HAPV - HAPVIDA PARTICIPACOES INVESTIMENTO SA                
DEBN HAPV21_072026   DEBN HAPV21                               16.139,56       0,00 10403 - Títulos Privados-Debêntures simples                  HAPV - HAPVIDA PARTICIPACOES INVESTIMENTO SA                
DEBN ANHBA4_062028   DEBN ANHBA4 I243525                    5.553.822,30       0,10 10403 - Títulos Privados-Debêntures simples                  ANHB - CONCESSIONARIA SISTEMA ANHANGUERA BANDEIRANTES S/A   
DEBN HAPV21_072026   DEBN HAPV21                               86.750,13       0,00 10403 - Títulos Privados-Debêntures simples                  HAPV - HAPVIDA PARTICIPACOES INVESTIMENTO SA                
DEBN HAPV21_072026   DEBN HAPV21                               64.558,24       0,00 10403 - Títulos Privados-Debêntures simples                  HAPV - HAPVIDA PARTICIPACOES INVESTIMENTO SA                
DEBN HAPV21_072026   DEBN HAPV21                              161.395,60       0,00 10403 - Títulos Privados-Debêntures simples                  HAPV - HAPVIDA PARTICIPACOES INVESTIMENTO SA                
DEBN HAPV21_072026   DEBN HAPV21                               79.689,08       0,00 10403 - Títulos Privados-Debêntures simples                  HAPV - HAPVIDA PARTICIPACOES INVESTIMENTO SA                
DEBN HAPV21_072026   DEBN HAPV21                              156.351,98       0,00 10403 - Títulos Privados-Debêntures simples                  HAPV - HAPVIDA PARTICIPACOES INVESTIMENTO SA                
DEBN HAPV21_072026   DEBN HAPV21                               23.200,62       0,00 10403 - Títulos Privados-Debêntures simples                  HAPV - HAPVIDA PARTICIPACOES INVESTIMENTO SA                
DEBN HAPV21_072026   DEBN HAPV21                              149.290,93       0,00 10403 - Títulos Privados-Debêntures simples                  HAPV - HAPVIDA PARTICIPACOES INVESTIMENTO SA                
DEBN HAPV21_072026   DEBN HAPV21                              106.924,58       0,00 10403 - Títulos Privados-Debêntures simples                  HAPV - HAPVIDA PARTICIPACOES INVESTIMENTO SA                
DEBN HAPV21_072026   DEBN HAPV21                               84.732,69       0,00 10403 - Títulos Privados-Debêntures simples                  HAPV - HAPVIDA PARTICIPACOES INVESTIMENTO SA                
DEBN HAPV21_072026   DEBN HAPV21                            1.047.053,93       0,02 10403 - Títulos Privados-Debêntures simples                  HAPV - HAPVIDA PARTICIPACOES INVESTIMENTO SA                
DEBN ANHBA4_062028   DEBN ANHBA4 I243525                      238.303,41       0,00 10403 - Títulos Privados-Debêntures simples                  ANHB - CONCESSIONARIA SISTEMA ANHANGUERA BANDEIRANTES S/A   
DEBN HAPV21_072026   DEBN HAPV21                              116.003,08       0,00 10403 - Títulos Privados-Debêntures simples                  HAPV - HAPVIDA PARTICIPACOES INVESTIMENTO SA                
DEBN HAPV21_072026   DEBN HAPV21                               37.322,73       0,00 10403 - Títulos Privados-Debêntures simples                  HAPV - HAPVIDA PARTICIPACOES INVESTIMENTO SA                
DEBN HAPV21_072026   DEBN HAPV21                               59.514,63       0,00 10403 - Títulos Privados-Debêntures simples                  HAPV - HAPVIDA PARTICIPACOES INVESTIMENTO SA                
DEBN HAPV21_072026   DEBN HAPV21                               13.113,39       0,00 10403 - Títulos Privados-Debêntures simples                  HAPV - HAPVIDA PARTICIPACOES INVESTIMENTO SA                
DEBN HAPV21_072026   DEBN HAPV21                              113.985,64       0,00 10403 - Títulos Privados-Debêntures simples                  HAPV - HAPVIDA PARTICIPACOES INVESTIMENTO SA                
DEBN HAPV21_072026   DEBN HAPV21                              236.041,06       0,00 10403 - Títulos Privados-Debêntures simples                  HAPV - HAPVIDA PARTICIPACOES INVESTIMENTO SA                
DEBN HAPV21_072026   DEBN HAPV21                                9.078,50       0,00 10403 - Títulos Privados-Debêntures simples                  HAPV - HAPVIDA PARTICIPACOES INVESTIMENTO SA                
DEBN HAPV21_072026   DEBN HAPV21                                4.034,89       0,00 10403 - Títulos Privados-Debêntures simples                  HAPV - HAPVIDA PARTICIPACOES INVESTIMENTO SA                
DEBN HAPV21_072026   DEBN HAPV21                                4.034,89       0,00 10403 - Títulos Privados-Debêntures simples                  HAPV - HAPVIDA PARTICIPACOES INVESTIMENTO SA                
DEBN HAPV21_072026   DEBN HAPV21                               36.314,00       0,00 10403 - Títulos Privados-Debêntures simples                  HAPV - HAPVIDA PARTICIPACOES INVESTIMENTO SA                
DEBN ANHBA4_062028   DEBN ANHBA4 I243525                      254.953,43       0,00 10403 - Títulos Privados-Debêntures simples                  ANHB - CONCESSIONARIA SISTEMA ANHANGUERA BANDEIRANTES S/A   
DEBN HAPV22_042029   DEBN HAPV22 I294529                       48.878,13       0,00 10403 - Títulos Privados-Debêntures simples                  HAPV - HAPVIDA PARTICIPACOES INVESTIMENTO SA                
DEBN HAPV22_042029   DEBN HAPV22 I294529                       57.197,81       0,00 10403 - Títulos Privados-Debêntures simples                  HAPV - HAPVIDA PARTICIPACOES INVESTIMENTO SA                
DEBN HAPV22_042029   DEBN HAPV22 I294529                    1.068.039,13       0,02 10403 - Títulos Privados-Debêntures simples                  HAPV - HAPVIDA PARTICIPACOES INVESTIMENTO SA                
DEBN HAPV22_042029   DEBN HAPV22 I294529                    5.940.252,67       0,11 10403 - Títulos Privados-Debêntures simples                  HAPV - HAPVIDA PARTICIPACOES INVESTIMENTO SA                
DEBN HAPV22_042029   DEBN HAPV22 I294529                    1.605.698,55       0,03 10403 - Títulos Privados-Debêntures simples                  HAPV - HAPVIDA PARTICIPACOES INVESTIMENTO SA                
DEBN HAPV22_042029   DEBN HAPV22 I294529                       28.078,93       0,00 10403 - Títulos Privados-Debêntures simples                  HAPV - HAPVIDA PARTICIPACOES INVESTIMENTO SA                
DEBN HAPV22_042029   DEBN HAPV22 I294529                       90.476,54       0,00 10403 - Títulos Privados-Debêntures simples                  HAPV - HAPVIDA PARTICIPACOES INVESTIMENTO SA                
DEBN HAPV22_042029   DEBN HAPV22 I294529                    3.708.498,08       0,07 10403 - Títulos Privados-Debêntures simples                  HAPV - HAPVIDA PARTICIPACOES INVESTIMENTO SA                
DEBN HAPV22_042029   DEBN HAPV22 I294529                      203.832,20       0,00 10403 - Títulos Privados-Debêntures simples                  HAPV - HAPVIDA PARTICIPACOES INVESTIMENTO SA                
DEBN HAPV22_042029   DEBN HAPV22 I294529                       49.918,09       0,00 10403 - Títulos Privados-Debêntures simples                  HAPV - HAPVIDA PARTICIPACOES INVESTIMENTO SA                
DEBN ANIM15_052029   DEBN ANIM15 I922081                       75.145,37       0,00 10403 - Títulos Privados-Debêntures simples                  ANIM - ANIMA HOLDING SA                                     
DEBN HAPV22_042029   DEBN HAPV22 I294529                       25.999,00       0,00 10403 - Títulos Privados-Debêntures simples                  HAPV - HAPVIDA PARTICIPACOES INVESTIMENTO SA                
DEBN HAPV22_042029   DEBN HAPV22 I294529                    7.242.282,85       0,13 10403 - Títulos Privados-Debêntures simples                  HAPV - HAPVIDA PARTICIPACOES INVESTIMENTO SA                
DEBN HAPV22_042029   DEBN HAPV22 I294529                   11.813.947,90       0,21 10403 - Títulos Privados-Debêntures simples                  HAPV - HAPVIDA PARTICIPACOES INVESTIMENTO SA                
DEBN HAPV22_042029   DEBN HAPV22 I294529                      237.110,93       0,00 10403 - Títulos Privados-Debêntures simples                  HAPV - HAPVIDA PARTICIPACOES INVESTIMENTO SA                
DEBN HYPEA4_122027   DEBN HYPEA4 I408566                      761.583,56       0,01 10403 - Títulos Privados-Debêntures simples                  HYPE - HYPERA S.A.                                          
DEBN HYPEA4_122027   DEBN HYPEA4 I408566                        4.111,11       0,00 10403 - Títulos Privados-Debêntures simples                  HYPE - HYPERA S.A.                                          
DEBN HYPEA4_122027   DEBN HYPEA4 I408566                        9.250,00       0,00 10403 - Títulos Privados-Debêntures simples                  HYPE - HYPERA S.A.                                          
DEBN HYPEA4_122027   DEBN HYPEA4 I408566                       13.361,12       0,00 10403 - Títulos Privados-Debêntures simples                  HYPE - HYPERA S.A.                                          
DEBN HYPEA4_122027   DEBN HYPEA4 I408566                       79.138,91       0,00 10403 - Títulos Privados-Debêntures simples                  HYPE - HYPERA S.A.                                          
DEBN HYPEA4_122027   DEBN HYPEA4 I408566                       25.694,45       0,00 10403 - Títulos Privados-Debêntures simples                  HYPE - HYPERA S.A.                                          
DEBN APRB28_062027   DEBN APRB28                               73.992,65       0,00 10403 - Títulos Privados-Debêntures simples                  APRB - AUTOPISTA REGIS BITTENCOURT SA                       
DEBN HYPEA4_122027   DEBN HYPEA4 I408566                    3.959.001,18       0,07 10403 - Títulos Privados-Debêntures simples                  HYPE - HYPERA S.A.                                          
DEBN HYPEA4_122027   DEBN HYPEA4 I408566                       21.583,34       0,00 10403 - Títulos Privados-Debêntures simples                  HYPE - HYPERA S.A.                                          
DEBN HYPEA4_122027   DEBN HYPEA4 I408566                      117.166,70       0,00 10403 - Títulos Privados-Debêntures simples                  HYPE - HYPERA S.A.                                          
DEBN HYPEA4_122027   DEBN HYPEA4 I408566                      120.250,04       0,00 10403 - Títulos Privados-Debêntures simples                  HYPE - HYPERA S.A.                                          
DEBN HYPEA4_122027   DEBN HYPEA4 I408566                       12.333,34       0,00 10403 - Títulos Privados-Debêntures simples                  HYPE - HYPERA S.A.                                          
DEBN HYPEA4_122027   DEBN HYPEA4 I408566                       10.277,78       0,00 10403 - Títulos Privados-Debêntures simples                  HYPE - HYPERA S.A.                                          
DEBN HYPEA4_122027   DEBN HYPEA4 I408566                       13.361,12       0,00 10403 - Títulos Privados-Debêntures simples                  HYPE - HYPERA S.A.                                          
DEBN HYPEA4_122027   DEBN HYPEA4 I408566                        7.194,45       0,00 10403 - Títulos Privados-Debêntures simples                  HYPE - HYPERA S.A.                                          
DEBN HYPEA4_122027   DEBN HYPEA4 I408566                       12.333,34       0,00 10403 - Títulos Privados-Debêntures simples                  HYPE - HYPERA S.A.                                          
DEBN HYPEA4_122027   DEBN HYPEA4 I408566                        4.111,11       0,00 10403 - Títulos Privados-Debêntures simples                  HYPE - HYPERA S.A.                                          
DEBN APRB28_062027   DEBN APRB28                               23.237,36       0,00 10403 - Títulos Privados-Debêntures simples                  APRB - AUTOPISTA REGIS BITTENCOURT SA                       
DEBN HYPEA4_122027   DEBN HYPEA4 I408566                        6.166,67       0,00 10403 - Títulos Privados-Debêntures simples                  HYPE - HYPERA S.A.                                          
DEBN HYPEA4_122027   DEBN HYPEA4 I408566                        5.138,89       0,00 10403 - Títulos Privados-Debêntures simples                  HYPE - HYPERA S.A.                                          
DEBN HYPEA4_122027   DEBN HYPEA4 I408566                       16.444,45       0,00 10403 - Títulos Privados-Debêntures simples                  HYPE - HYPERA S.A.                                          
DEBN HYPEA4_122027   DEBN HYPEA4 I408566                       29.805,57       0,00 10403 - Títulos Privados-Debêntures simples                  HYPE - HYPERA S.A.                                          
DEBN HYPEA4_122027   DEBN HYPEA4 I408566                       13.361,12       0,00 10403 - Títulos Privados-Debêntures simples                  HYPE - HYPERA S.A.                                          
DEBN HYPEA4_122027   DEBN HYPEA4 I408566                       14.388,89       0,00 10403 - Títulos Privados-Debêntures simples                  HYPE - HYPERA S.A.                                          
DEBN HYPEA4_122027   DEBN HYPEA4 I408566                       31.861,12       0,00 10403 - Títulos Privados-Debêntures simples                  HYPE - HYPERA S.A.                                          
DEBN HYPEA4_122027   DEBN HYPEA4 I408566                        1.027,78       0,00 10403 - Títulos Privados-Debêntures simples                  HYPE - HYPERA S.A.                                          
DEBN HYPEA4_122027   DEBN HYPEA4 I408566                       22.611,12       0,00 10403 - Títulos Privados-Debêntures simples                  HYPE - HYPERA S.A.                                          
DEBN HYPEA4_122027   DEBN HYPEA4 I408566                        2.055,56       0,00 10403 - Títulos Privados-Debêntures simples                  HYPE - HYPERA S.A.                                          
DEBN AEGPA0_052029   DEBN AEGPA0 H750651                      135.390,57       0,00 10440 - Títulos Privados-Debêntures Incent. (Lei 12.431)     AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN APRB28_062027   DEBN APRB28                              142.481,71       0,00 10403 - Títulos Privados-Debêntures simples                  APRB - AUTOPISTA REGIS BITTENCOURT SA                       
DEBN HYPEA4_122027   DEBN HYPEA4 I408566                       16.444,45       0,00 10403 - Títulos Privados-Debêntures simples                  HYPE - HYPERA S.A.                                          
DEBN HYPEA4_122027   DEBN HYPEA4 I408566                       17.472,23       0,00 10403 - Títulos Privados-Debêntures simples                  HYPE - HYPERA S.A.                                          
DEBN HYPEA4_122027   DEBN HYPEA4 I408566                       19.527,79       0,00 10403 - Títulos Privados-Debêntures simples                  HYPE - HYPERA S.A.                                          
DEBN HYPEA4_122027   DEBN HYPEA4 I408566                       10.277,78       0,00 10403 - Títulos Privados-Debêntures simples                  HYPE - HYPERA S.A.                                          
DEBN HYPEA5_042028   DEBN HYPEA5 I179253                      127.154,20       0,00 10403 - Títulos Privados-Debêntures simples                  HYPE - HYPERA S.A.                                          
DEBN HYPEA5_042028   DEBN HYPEA5 I179253                       31.788,55       0,00 10403 - Títulos Privados-Debêntures simples                  HYPE - HYPERA S.A.                                          
DEBN HYPEA5_042028   DEBN HYPEA5 I179253                       95.365,65       0,00 10403 - Títulos Privados-Debêntures simples                  HYPE - HYPERA S.A.                                          
DEBN HYPEA5_042028   DEBN HYPEA5 I179253                       31.788,55       0,00 10403 - Títulos Privados-Debêntures simples                  HYPE - HYPERA S.A.                                          
DEBN HYPEA5_042028   DEBN HYPEA5 I179253                      178.015,88       0,00 10403 - Títulos Privados-Debêntures simples                  HYPE - HYPERA S.A.                                          
DEBN HYPEA5_042028   DEBN HYPEA5 I179253                    1.234.455,35       0,02 10403 - Títulos Privados-Debêntures simples                  HYPE - HYPERA S.A.                                          
DEBN APRB28_062027   DEBN APRB28                               26.906,42       0,00 10403 - Títulos Privados-Debêntures simples                  APRB - AUTOPISTA REGIS BITTENCOURT SA                       
DEBN HYPEA5_042028   DEBN HYPEA5 I179253                    2.552.620,55       0,05 10403 - Títulos Privados-Debêntures simples                  HYPE - HYPERA S.A.                                          
DEBN HYPEA5_042028   DEBN HYPEA5 I179253                      102.782,98       0,00 10403 - Títulos Privados-Debêntures simples                  HYPE - HYPERA S.A.                                          
DEBN HYPEA5_042028   DEBN HYPEA5 I179253                      147.286,95       0,00 10403 - Títulos Privados-Debêntures simples                  HYPE - HYPERA S.A.                                          
DEBN HYPEA5_042028   DEBN HYPEA5 I179253                       61.457,86       0,00 10403 - Títulos Privados-Debêntures simples                  HYPE - HYPERA S.A.                                          
DEBN HYPEA5_042028   DEBN HYPEA5 I179253                      621.995,96       0,01 10403 - Títulos Privados-Debêntures simples                  HYPE - HYPERA S.A.                                          
DEBN HYPEA5_042028   DEBN HYPEA5 I179253                      102.782,98       0,00 10403 - Títulos Privados-Debêntures simples                  HYPE - HYPERA S.A.                                          
DEBN HYPEA5_042028   DEBN HYPEA5 I179253                       33.907,79       0,00 10403 - Títulos Privados-Debêntures simples                  HYPE - HYPERA S.A.                                          
DEBN HYPEA5_042028   DEBN HYPEA5 I179253                       92.186,79       0,00 10403 - Títulos Privados-Debêntures simples                  HYPE - HYPERA S.A.                                          
DEBN HYPEA5_042028   DEBN HYPEA5 I179253                       42.384,73       0,00 10403 - Títulos Privados-Debêntures simples                  HYPE - HYPERA S.A.                                          
DEBN HYPEA5_042028   DEBN HYPEA5 I179253                      117.617,63       0,00 10403 - Títulos Privados-Debêntures simples                  HYPE - HYPERA S.A.                                          
DEBN APRB28_062027   DEBN APRB28                              474.531,37       0,01 10403 - Títulos Privados-Debêntures simples                  APRB - AUTOPISTA REGIS BITTENCOURT SA                       
DEBN HYPEA5_042028   DEBN HYPEA5 I179253                       68.875,19       0,00 10403 - Títulos Privados-Debêntures simples                  HYPE - HYPERA S.A.                                          
DEBN HYPEA5_042028   DEBN HYPEA5 I179253                      128.213,82       0,00 10403 - Títulos Privados-Debêntures simples                  HYPE - HYPERA S.A.                                          
DEBN HYPEA5_042028   DEBN HYPEA5 I179253                   24.523.806,61       0,44 10403 - Títulos Privados-Debêntures simples                  HYPE - HYPERA S.A.                                          
DEBN HYPEA5_042028   DEBN HYPEA5 I179253                      162.121,61       0,00 10403 - Títulos Privados-Debêntures simples                  HYPE - HYPERA S.A.                                          
DEBN HYPEA5_042028   DEBN HYPEA5 I179253                       32.848,17       0,00 10403 - Títulos Privados-Debêntures simples                  HYPE - HYPERA S.A.                                          
DEBN HYPEA5_042028   DEBN HYPEA5 I179253                       56.159,77       0,00 10403 - Títulos Privados-Debêntures simples                  HYPE - HYPERA S.A.                                          
DEBN HYPEA5_042028   DEBN HYPEA5 I179253                      215.102,52       0,00 10403 - Títulos Privados-Debêntures simples                  HYPE - HYPERA S.A.                                          
DEBN HYPEA5_042028   DEBN HYPEA5 I179253                        5.298,09       0,00 10403 - Títulos Privados-Debêntures simples                  HYPE - HYPERA S.A.                                          
DEBN HYPEA5_042028   DEBN HYPEA5 I179253                      220.400,61       0,00 10403 - Títulos Privados-Debêntures simples                  HYPE - HYPERA S.A.                                          
DEBN HYPEA5_042028   DEBN HYPEA5 I179253                       91.127,18       0,00 10403 - Títulos Privados-Debêntures simples                  HYPE - HYPERA S.A.                                          
DEBN APRB28_062027   DEBN APRB28                            1.451.723,55       0,03 10403 - Títulos Privados-Debêntures simples                  APRB - AUTOPISTA REGIS BITTENCOURT SA                       
DEBN HYPEA5_042028   DEBN HYPEA5 I179253                      116.558,02       0,00 10403 - Títulos Privados-Debêntures simples                  HYPE - HYPERA S.A.                                          
DEBN HYPEA5_042028   DEBN HYPEA5 I179253                       69.934,81       0,00 10403 - Títulos Privados-Debêntures simples                  HYPE - HYPERA S.A.                                          
DEBN HYPEA5_042028   DEBN HYPEA5 I179253                       91.127,18       0,00 10403 - Títulos Privados-Debêntures simples                  HYPE - HYPERA S.A.                                          
DEBN HYPEA5_042028   DEBN HYPEA5 I179253                       22.251,98       0,00 10403 - Títulos Privados-Debêntures simples                  HYPE - HYPERA S.A.                                          
DEBN HYPEA5_042028   DEBN HYPEA5 I179253                      180.135,12       0,00 10403 - Títulos Privados-Debêntures simples                  HYPE - HYPERA S.A.                                          
DEBN HYPEA6_102028   DEBN HYPEA6 I474549                      132.307,44       0,00 10403 - Títulos Privados-Debêntures simples                  HYPE - HYPERA S.A.                                          
DEBN HYPEA6_102028   DEBN HYPEA6 I474549                       34.651,95       0,00 10403 - Títulos Privados-Debêntures simples                  HYPE - HYPERA S.A.                                          
DEBN HYPEA6_102028   DEBN HYPEA6 I474549                    2.414.085,84       0,04 10403 - Títulos Privados-Debêntures simples                  HYPE - HYPERA S.A.                                          
DEBN HYPEA6_102028   DEBN HYPEA6 I474549                      827.446,56       0,01 10403 - Títulos Privados-Debêntures simples                  HYPE - HYPERA S.A.                                          
DEBN HYPEA6_102028   DEBN HYPEA6 I474549                       63.003,55       0,00 10403 - Títulos Privados-Debêntures simples                  HYPE - HYPERA S.A.                                          
DEBN APRB28_062027   DEBN APRB28                              944.170,67       0,02 10403 - Títulos Privados-Debêntures simples                  APRB - AUTOPISTA REGIS BITTENCOURT SA                       
DEBN HYPEA6_102028   DEBN HYPEA6 I474549                      151.208,51       0,00 10403 - Títulos Privados-Debêntures simples                  HYPE - HYPERA S.A.                                          
DEBN HYPEA6_102028   DEBN HYPEA6 I474549                      126.007,09       0,00 10403 - Títulos Privados-Debêntures simples                  HYPE - HYPERA S.A.                                          
DEBN HYPEA6_102028   DEBN HYPEA6 I474549                       54.603,07       0,00 10403 - Títulos Privados-Debêntures simples                  HYPE - HYPERA S.A.                                          
DEBN HYPEA6_102028   DEBN HYPEA6 I474549                       68.253,84       0,00 10403 - Títulos Privados-Debêntures simples                  HYPE - HYPERA S.A.                                          
DEBN HYPEA6_102028   DEBN HYPEA6 I474549                      115.506,50       0,00 10403 - Títulos Privados-Debêntures simples                  HYPE - HYPERA S.A.                                          
DEBN HYPEA6_102028   DEBN HYPEA6 I474549                       31.501,77       0,00 10403 - Títulos Privados-Debêntures simples                  HYPE - HYPERA S.A.                                          
DEBN HYPEA6_102028   DEBN HYPEA6 I474549                       89.255,02       0,00 10403 - Títulos Privados-Debêntures simples                  HYPE - HYPERA S.A.                                          
DEBN HYPEA6_102028   DEBN HYPEA6 I474549                      211.061,88       0,00 10403 - Títulos Privados-Debêntures simples                  HYPE - HYPERA S.A.                                          
DEBN HYPEA6_102028   DEBN HYPEA6 I474549                       40.952,30       0,00 10403 - Títulos Privados-Debêntures simples                  HYPE - HYPERA S.A.                                          
DEBN HYPEA6_102028   DEBN HYPEA6 I474549                       91.355,14       0,00 10403 - Títulos Privados-Debêntures simples                  HYPE - HYPERA S.A.                                          
DEBN APRB28_062027   DEBN APRB28                              320.430,98       0,01 10403 - Títulos Privados-Debêntures simples                  APRB - AUTOPISTA REGIS BITTENCOURT SA                       
DEBN HYPEA6_102028   DEBN HYPEA6 I474549                      100.805,67       0,00 10403 - Títulos Privados-Debêntures simples                  HYPE - HYPERA S.A.                                          
DEBN HYPEA6_102028   DEBN HYPEA6 I474549                       93.455,26       0,00 10403 - Títulos Privados-Debêntures simples                  HYPE - HYPERA S.A.                                          
DEBN HYPEA6_102028   DEBN HYPEA6 I474549                      217.362,23       0,00 10403 - Títulos Privados-Debêntures simples                  HYPE - HYPERA S.A.                                          
DEBN HYPEA6_102028   DEBN HYPEA6 I474549                       90.305,08       0,00 10403 - Títulos Privados-Debêntures simples                  HYPE - HYPERA S.A.                                          
DEBN HYPEA6_102028   DEBN HYPEA6 I474549                      115.506,50       0,00 10403 - Títulos Privados-Debêntures simples                  HYPE - HYPERA S.A.                                          
DEBN HYPEA6_102028   DEBN HYPEA6 I474549                       69.303,90       0,00 10403 - Títulos Privados-Debêntures simples                  HYPE - HYPERA S.A.                                          
DEBN HYPEA6_102028   DEBN HYPEA6 I474549                      157.508,87       0,00 10403 - Títulos Privados-Debêntures simples                  HYPE - HYPERA S.A.                                          
DEBN HYPEA6_102028   DEBN HYPEA6 I474549                   27.154.528,02       0,49 10403 - Títulos Privados-Debêntures simples                  HYPE - HYPERA S.A.                                          
DEBN HYPEA6_102028   DEBN HYPEA6 I474549                        8.400,47       0,00 10403 - Títulos Privados-Debêntures simples                  HYPE - HYPERA S.A.                                          
DEBN HYPEA6_102028   DEBN HYPEA6 I474549                      175.359,87       0,00 10403 - Títulos Privados-Debêntures simples                  HYPE - HYPERA S.A.                                          
DEBN APRB28_062027   DEBN APRB28                               13.453,21       0,00 10403 - Títulos Privados-Debêntures simples                  APRB - AUTOPISTA REGIS BITTENCOURT SA                       
DEBN HYPEA6_102028   DEBN HYPEA6 I474549                       31.501,77       0,00 10403 - Títulos Privados-Debêntures simples                  HYPE - HYPERA S.A.                                          
DEBN HYPEA6_102028   DEBN HYPEA6 I474549                        8.400,47       0,00 10403 - Títulos Privados-Debêntures simples                  HYPE - HYPERA S.A.                                          
DEBN HYPEA7_122028   DEBN HYPEA7 I584839                      136.652,90       0,00 10403 - Títulos Privados-Debêntures simples                  HYPE - HYPERA S.A.                                          
DEBN HYPEA7_122028   DEBN HYPEA7 I584839                      255.838,88       0,00 10403 - Títulos Privados-Debêntures simples                  HYPE - HYPERA S.A.                                          
DEBN HYPEA7_122028   DEBN HYPEA7 I584839                      105.828,93       0,00 10403 - Títulos Privados-Debêntures simples                  HYPE - HYPERA S.A.                                          
DEBN HYPEA7_122028   DEBN HYPEA7 I584839                      248.646,63       0,00 10403 - Títulos Privados-Debêntures simples                  HYPE - HYPERA S.A.                                          
DEBN HYPEA7_122028   DEBN HYPEA7 I584839                      106.856,40       0,00 10403 - Títulos Privados-Debêntures simples                  HYPE - HYPERA S.A.                                          
DEBN HYPEA7_122028   DEBN HYPEA7 I584839                      105.828,93       0,00 10403 - Títulos Privados-Debêntures simples                  HYPE - HYPERA S.A.                                          
DEBN HYPEA7_122028   DEBN HYPEA7 I584839                       38.016,22       0,00 10403 - Títulos Privados-Debêntures simples                  HYPE - HYPERA S.A.                                          
DEBN HYPEA7_122028   DEBN HYPEA7 I584839                       18.494,38       0,00 10403 - Títulos Privados-Debêntures simples                  HYPE - HYPERA S.A.                                          
DEBN APRB28_062027   DEBN APRB28                               39.748,12       0,00 10403 - Títulos Privados-Debêntures simples                  APRB - AUTOPISTA REGIS BITTENCOURT SA                       
DEBN HYPEA7_122028   DEBN HYPEA7 I584839                       64.730,32       0,00 10403 - Títulos Privados-Debêntures simples                  HYPE - HYPERA S.A.                                          
DEBN HYPEA7_122028   DEBN HYPEA7 I584839                       49.318,34       0,00 10403 - Títulos Privados-Debêntures simples                  HYPE - HYPERA S.A.                                          
DEBN HYPEA7_122028   DEBN HYPEA7 I584839                      110.966,26       0,00 10403 - Títulos Privados-Debêntures simples                  HYPE - HYPERA S.A.                                          
DEBN HYPEA7_122028   DEBN HYPEA7 I584839                      147.955,02       0,00 10403 - Títulos Privados-Debêntures simples                  HYPE - HYPERA S.A.                                          
DEBN HYPEA7_122028   DEBN HYPEA7 I584839                      151.037,41       0,00 10403 - Títulos Privados-Debêntures simples                  HYPE - HYPERA S.A.                                          
DEBN HYPEA7_122028   DEBN HYPEA7 I584839                       79.114,83       0,00 10403 - Títulos Privados-Debêntures simples                  HYPE - HYPERA S.A.                                          
DEBN HYPEA7_122028   DEBN HYPEA7 I584839                      136.652,90       0,00 10403 - Títulos Privados-Debêntures simples                  HYPE - HYPERA S.A.                                          
DEBN HYPEA7_122028   DEBN HYPEA7 I584839                      205.493,08       0,00 10403 - Títulos Privados-Debêntures simples                  HYPE - HYPERA S.A.                                          
DEBN HYPEA7_122028   DEBN HYPEA7 I584839                       36.988,75       0,00 10403 - Títulos Privados-Debêntures simples                  HYPE - HYPERA S.A.                                          
DEBN HYPEA7_122028   DEBN HYPEA7 I584839                       39.043,68       0,00 10403 - Títulos Privados-Debêntures simples                  HYPE - HYPERA S.A.                                          
DEBN APRB28_062027   DEBN APRB28                               39.136,61       0,00 10403 - Títulos Privados-Debêntures simples                  APRB - AUTOPISTA REGIS BITTENCOURT SA                       
DEBN HYPEA7_122028   DEBN HYPEA7 I584839                      102.746,54       0,00 10403 - Títulos Privados-Debêntures simples                  HYPE - HYPERA S.A.                                          
DEBN HYPEA7_122028   DEBN HYPEA7 I584839                   14.648.573,90       0,26 10403 - Títulos Privados-Debêntures simples                  HYPE - HYPERA S.A.                                          
DEBN HYPEA7_122028   DEBN HYPEA7 I584839                       81.169,76       0,00 10403 - Títulos Privados-Debêntures simples                  HYPE - HYPERA S.A.                                          
DEBN HYPEA7_122028   DEBN HYPEA7 I584839                      185.971,24       0,00 10403 - Títulos Privados-Debêntures simples                  HYPE - HYPERA S.A.                                          
DEBN HYPEA7_122028   DEBN HYPEA7 I584839                        6.164,79       0,00 10403 - Títulos Privados-Debêntures simples                  HYPE - HYPERA S.A.                                          
DEBN HYPEA7_122028   DEBN HYPEA7 I584839                      118.158,52       0,00 10403 - Títulos Privados-Debêntures simples                  HYPE - HYPERA S.A.                                          
DEBN IGTAB0_092027   DEBN IGTAB0                                8.665,88       0,00 10403 - Títulos Privados-Debêntures simples                  IGTA - IGUATEMI EMPRESA SHOPPING CENTERS SA                 
DEBN IGTAB0_092027   DEBN IGTAB0                               16.248,52       0,00 10403 - Títulos Privados-Debêntures simples                  IGTA - IGUATEMI EMPRESA SHOPPING CENTERS SA                 
DEBN IGTAB0_092027   DEBN IGTAB0                               62.827,59       0,00 10403 - Títulos Privados-Debêntures simples                  IGTA - IGUATEMI EMPRESA SHOPPING CENTERS SA                 
DEBN IGTAB0_092027   DEBN IGTAB0                               27.080,86       0,00 10403 - Títulos Privados-Debêntures simples                  IGTA - IGUATEMI EMPRESA SHOPPING CENTERS SA                 
DEBN APRB28_062027   DEBN APRB28                           10.066.057,89       0,18 10403 - Títulos Privados-Debêntures simples                  APRB - AUTOPISTA REGIS BITTENCOURT SA                       
DEBN IGTAB0_092027   DEBN IGTAB0                              748.514,99       0,01 10403 - Títulos Privados-Debêntures simples                  IGTA - IGUATEMI EMPRESA SHOPPING CENTERS SA                 
DEBN IGTAB0_092027   DEBN IGTAB0                               85.575,52       0,00 10403 - Títulos Privados-Debêntures simples                  IGTA - IGUATEMI EMPRESA SHOPPING CENTERS SA                 
DEBN IGTAB0_092027   DEBN IGTAB0                              277.308,01       0,00 10403 - Títulos Privados-Debêntures simples                  IGTA - IGUATEMI EMPRESA SHOPPING CENTERS SA                 
DEBN IGTAB0_092027   DEBN IGTAB0                              172.234,27       0,00 10403 - Títulos Privados-Debêntures simples                  IGTA - IGUATEMI EMPRESA SHOPPING CENTERS SA                 
DEBN IGTAB0_092027   DEBN IGTAB0                               25.997,63       0,00 10403 - Títulos Privados-Debêntures simples                  IGTA - IGUATEMI EMPRESA SHOPPING CENTERS SA                 
DEBN IGTAB0_092027   DEBN IGTAB0                               41.162,91       0,00 10403 - Títulos Privados-Debêntures simples                  IGTA - IGUATEMI EMPRESA SHOPPING CENTERS SA                 
DEBN IGTAB0_092027   DEBN IGTAB0                            6.664.058,19       0,12 10403 - Títulos Privados-Debêntures simples                  IGTA - IGUATEMI EMPRESA SHOPPING CENTERS SA                 
DEBN IGTAB0_092027   DEBN IGTAB0                               33.580,27       0,00 10403 - Títulos Privados-Debêntures simples                  IGTA - IGUATEMI EMPRESA SHOPPING CENTERS SA                 
DEBN IGTAB0_092027   DEBN IGTAB0                              708.435,31       0,01 10403 - Títulos Privados-Debêntures simples                  IGTA - IGUATEMI EMPRESA SHOPPING CENTERS SA                 
DEBN IGTAB0_092027   DEBN IGTAB0                               33.580,27       0,00 10403 - Títulos Privados-Debêntures simples                  IGTA - IGUATEMI EMPRESA SHOPPING CENTERS SA                 
DEBN AEGPA0_052029   DEBN AEGPA0 H750651                       40.307,11       0,00 10440 - Títulos Privados-Debêntures Incent. (Lei 12.431)     AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN APRB28_062027   DEBN APRB28                               73.381,14       0,00 10403 - Títulos Privados-Debêntures simples                  APRB - AUTOPISTA REGIS BITTENCOURT SA                       
DEBN IGTAB0_092027   DEBN IGTAB0                               11.915,58       0,00 10403 - Títulos Privados-Debêntures simples                  IGTA - IGUATEMI EMPRESA SHOPPING CENTERS SA                 
DEBN IGTAB0_092027   DEBN IGTAB0                               27.080,86       0,00 10403 - Títulos Privados-Debêntures simples                  IGTA - IGUATEMI EMPRESA SHOPPING CENTERS SA                 
DEBN IGTAB0_092027   DEBN IGTAB0                                9.749,11       0,00 10403 - Títulos Privados-Debêntures simples                  IGTA - IGUATEMI EMPRESA SHOPPING CENTERS SA                 
DEBN IGTAB0_092027   DEBN IGTAB0                               46.579,08       0,00 10403 - Títulos Privados-Debêntures simples                  IGTA - IGUATEMI EMPRESA SHOPPING CENTERS SA                 
DEBN IGTAB0_092027   DEBN IGTAB0                                7.582,64       0,00 10403 - Títulos Privados-Debêntures simples                  IGTA - IGUATEMI EMPRESA SHOPPING CENTERS SA                 
DEBN IGTAB0_092027   DEBN IGTAB0                               50.912,02       0,00 10403 - Títulos Privados-Debêntures simples                  IGTA - IGUATEMI EMPRESA SHOPPING CENTERS SA                 
DEBN IGTAB0_092027   DEBN IGTAB0                               19.498,22       0,00 10403 - Títulos Privados-Debêntures simples                  IGTA - IGUATEMI EMPRESA SHOPPING CENTERS SA                 
DEBN IGTAB0_092027   DEBN IGTAB0                               34.663,50       0,00 10403 - Títulos Privados-Debêntures simples                  IGTA - IGUATEMI EMPRESA SHOPPING CENTERS SA                 
DEBN IGTAB0_092027   DEBN IGTAB0                                9.749,11       0,00 10403 - Títulos Privados-Debêntures simples                  IGTA - IGUATEMI EMPRESA SHOPPING CENTERS SA                 
DEBN IGTAB0_092027   DEBN IGTAB0                               36.829,98       0,00 10403 - Títulos Privados-Debêntures simples                  IGTA - IGUATEMI EMPRESA SHOPPING CENTERS SA                 
DEBN APRB28_062027   DEBN APRB28                               17.122,27       0,00 10403 - Títulos Privados-Debêntures simples                  APRB - AUTOPISTA REGIS BITTENCOURT SA                       
DEBN IGTAB0_092027   DEBN IGTAB0                               34.663,50       0,00 10403 - Títulos Privados-Debêntures simples                  IGTA - IGUATEMI EMPRESA SHOPPING CENTERS SA                 
DEBN IGTAB0_092027   DEBN IGTAB0                               27.080,86       0,00 10403 - Títulos Privados-Debêntures simples                  IGTA - IGUATEMI EMPRESA SHOPPING CENTERS SA                 
DEBN IGTAB0_092027   DEBN IGTAB0                               62.827,60       0,00 10403 - Títulos Privados-Debêntures simples                  IGTA - IGUATEMI EMPRESA SHOPPING CENTERS SA                 
DEBN IGTAB0_092027   DEBN IGTAB0                                2.166,47       0,00 10403 - Títulos Privados-Debêntures simples                  IGTA - IGUATEMI EMPRESA SHOPPING CENTERS SA                 
DEBN IGTAB0_092027   DEBN IGTAB0                               16.248,52       0,00 10403 - Títulos Privados-Debêntures simples                  IGTA - IGUATEMI EMPRESA SHOPPING CENTERS SA                 
DEBN IGTAB0_092027   DEBN IGTAB0                               20.581,45       0,00 10403 - Títulos Privados-Debêntures simples                  IGTA - IGUATEMI EMPRESA SHOPPING CENTERS SA                 
DEBN IGTAB0_092027   DEBN IGTAB0                               29.247,33       0,00 10403 - Títulos Privados-Debêntures simples                  IGTA - IGUATEMI EMPRESA SHOPPING CENTERS SA                 
DEBN IGTAB1_062028   DEBN IGTAB1 I192278                        5.199,40       0,00 10403 - Títulos Privados-Debêntures simples                  IGTA - IGUATEMI EMPRESA SHOPPING CENTERS SA                 
DEBN IGTAB1_062028   DEBN IGTAB1 I192278                        8.319,03       0,00 10403 - Títulos Privados-Debêntures simples                  IGTA - IGUATEMI EMPRESA SHOPPING CENTERS SA                 
DEBN IGTAB1_062028   DEBN IGTAB1 I192278                        4.159,52       0,00 10403 - Títulos Privados-Debêntures simples                  IGTA - IGUATEMI EMPRESA SHOPPING CENTERS SA                 
DEBN APRB28_062027   DEBN APRB28                               48.920,76       0,00 10403 - Títulos Privados-Debêntures simples                  APRB - AUTOPISTA REGIS BITTENCOURT SA                       
DEBN IGTAB1_062028   DEBN IGTAB1 I192278                        1.039,88       0,00 10403 - Títulos Privados-Debêntures simples                  IGTA - IGUATEMI EMPRESA SHOPPING CENTERS SA                 
DEBN IGTAB1_062028   DEBN IGTAB1 I192278                        2.079,76       0,00 10403 - Títulos Privados-Debêntures simples                  IGTA - IGUATEMI EMPRESA SHOPPING CENTERS SA                 
DEBN IGTAB1_062028   DEBN IGTAB1 I192278                        4.159,52       0,00 10403 - Títulos Privados-Debêntures simples                  IGTA - IGUATEMI EMPRESA SHOPPING CENTERS SA                 
DEBN IGTAB1_062028   DEBN IGTAB1 I192278                        8.319,03       0,00 10403 - Títulos Privados-Debêntures simples                  IGTA - IGUATEMI EMPRESA SHOPPING CENTERS SA                 
DEBN IGTAB1_062028   DEBN IGTAB1 I192278                       15.598,19       0,00 10403 - Títulos Privados-Debêntures simples                  IGTA - IGUATEMI EMPRESA SHOPPING CENTERS SA                 
DEBN IGTAB1_062028   DEBN IGTAB1 I192278                       16.638,07       0,00 10403 - Títulos Privados-Debêntures simples                  IGTA - IGUATEMI EMPRESA SHOPPING CENTERS SA                 
DEBN IGTAB1_062028   DEBN IGTAB1 I192278                        7.279,15       0,00 10403 - Títulos Privados-Debêntures simples                  IGTA - IGUATEMI EMPRESA SHOPPING CENTERS SA                 
DEBN IGTAB1_062028   DEBN IGTAB1 I192278                       11.438,67       0,00 10403 - Títulos Privados-Debêntures simples                  IGTA - IGUATEMI EMPRESA SHOPPING CENTERS SA                 
DEBN IGTAB1_062028   DEBN IGTAB1 I192278                       13.518,43       0,00 10403 - Títulos Privados-Debêntures simples                  IGTA - IGUATEMI EMPRESA SHOPPING CENTERS SA                 
DEBN IGTAB1_062028   DEBN IGTAB1 I192278                        3.119,64       0,00 10403 - Títulos Privados-Debêntures simples                  IGTA - IGUATEMI EMPRESA SHOPPING CENTERS SA                 
DEBN APRB28_062027   DEBN APRB28                               14.676,23       0,00 10403 - Títulos Privados-Debêntures simples                  APRB - AUTOPISTA REGIS BITTENCOURT SA                       
DEBN IGTAB1_062028   DEBN IGTAB1 I192278                        3.119,64       0,00 10403 - Títulos Privados-Debêntures simples                  IGTA - IGUATEMI EMPRESA SHOPPING CENTERS SA                 
DEBN IGTAB1_062028   DEBN IGTAB1 I192278                        7.279,15       0,00 10403 - Títulos Privados-Debêntures simples                  IGTA - IGUATEMI EMPRESA SHOPPING CENTERS SA                 
DEBN IGTAB1_062028   DEBN IGTAB1 I192278                        6.239,28       0,00 10403 - Títulos Privados-Debêntures simples                  IGTA - IGUATEMI EMPRESA SHOPPING CENTERS SA                 
DEBN IGTAB1_062028   DEBN IGTAB1 I192278                        7.279,15       0,00 10403 - Títulos Privados-Debêntures simples                  IGTA - IGUATEMI EMPRESA SHOPPING CENTERS SA                 
DEBN IGTAB1_062028   DEBN IGTAB1 I192278                        4.159,52       0,00 10403 - Títulos Privados-Debêntures simples                  IGTA - IGUATEMI EMPRESA SHOPPING CENTERS SA                 
DEBN IGTAB1_062028   DEBN IGTAB1 I192278                        9.358,91       0,00 10403 - Títulos Privados-Debêntures simples                  IGTA - IGUATEMI EMPRESA SHOPPING CENTERS SA                 
DEBN IGTAB1_062028   DEBN IGTAB1 I192278                      188.218,15       0,00 10403 - Títulos Privados-Debêntures simples                  IGTA - IGUATEMI EMPRESA SHOPPING CENTERS SA                 
DEBN IGTAB1_062028   DEBN IGTAB1 I192278                       19.757,71       0,00 10403 - Títulos Privados-Debêntures simples                  IGTA - IGUATEMI EMPRESA SHOPPING CENTERS SA                 
DEBN IGTAB1_062028   DEBN IGTAB1 I192278                      162.221,17       0,00 10403 - Títulos Privados-Debêntures simples                  IGTA - IGUATEMI EMPRESA SHOPPING CENTERS SA                 
DEBN IGTAB1_062028   DEBN IGTAB1 I192278                       37.435,65       0,00 10403 - Títulos Privados-Debêntures simples                  IGTA - IGUATEMI EMPRESA SHOPPING CENTERS SA                 
DEBN APRB28_062027   DEBN APRB28                               43.417,17       0,00 10403 - Títulos Privados-Debêntures simples                  APRB - AUTOPISTA REGIS BITTENCOURT SA                       
DEBN IGTAB1_062028   DEBN IGTAB1 I192278                        5.199,40       0,00 10403 - Títulos Privados-Debêntures simples                  IGTA - IGUATEMI EMPRESA SHOPPING CENTERS SA                 
DEBN IGTAB1_062028   DEBN IGTAB1 I192278                        7.279,15       0,00 10403 - Títulos Privados-Debêntures simples                  IGTA - IGUATEMI EMPRESA SHOPPING CENTERS SA                 
DEBN IGTAB1_062028   DEBN IGTAB1 I192278                       11.438,67       0,00 10403 - Títulos Privados-Debêntures simples                  IGTA - IGUATEMI EMPRESA SHOPPING CENTERS SA                 
DEBN IGTAB1_062028   DEBN IGTAB1 I192278                        2.079,76       0,00 10403 - Títulos Privados-Debêntures simples                  IGTA - IGUATEMI EMPRESA SHOPPING CENTERS SA                 
DEBN IGTAB1_062028   DEBN IGTAB1 I192278                        9.358,91       0,00 10403 - Títulos Privados-Debêntures simples                  IGTA - IGUATEMI EMPRESA SHOPPING CENTERS SA                 
DEBN IGTAB1_062028   DEBN IGTAB1 I192278                    1.385.119,20       0,02 10403 - Títulos Privados-Debêntures simples                  IGTA - IGUATEMI EMPRESA SHOPPING CENTERS SA                 
DEBN INEL12_052029   DEBN INEL12 I921418                       86.490,87       0,00 10403 - Títulos Privados-Debêntures simples                  INEL - INSPIRALI EDUCACAO S.A.                              
DEBN JSLGA5_102028   DEBN JSLGA5                               58.955,01       0,00 10403 - Títulos Privados-Debêntures simples                  JSLG - JSL SA                                               
DEBN JSLGA5_102028   DEBN JSLGA5                              143.767,49       0,00 10403 - Títulos Privados-Debêntures simples                  JSLG - JSL SA                                               
DEBN JSLGA5_102028   DEBN JSLGA5                              145.836,09       0,00 10403 - Títulos Privados-Debêntures simples                  JSLG - JSL SA                                               
DEBN APRB28_062027   DEBN APRB28                               38.525,10       0,00 10403 - Títulos Privados-Debêntures simples                  APRB - AUTOPISTA REGIS BITTENCOURT SA                       
DEBN JSLGA5_102028   DEBN JSLGA5                              145.836,09       0,00 10403 - Títulos Privados-Debêntures simples                  JSLG - JSL SA                                               
DEBN JSLGA5_102028   DEBN JSLGA5                               14.480,18       0,00 10403 - Títulos Privados-Debêntures simples                  JSLG - JSL SA                                               
DEBN JSLGA5_102028   DEBN JSLGA5                              184.105,13       0,00 10403 - Títulos Privados-Debêntures simples                  JSLG - JSL SA                                               
DEBN JSLGA5_102028   DEBN JSLGA5                                3.102,90       0,00 10403 - Títulos Privados-Debêntures simples                  JSLG - JSL SA                                               
DEBN JSLGA5_102028   DEBN JSLGA5                                8.274,39       0,00 10403 - Títulos Privados-Debêntures simples                  JSLG - JSL SA                                               
DEBN JSLGA5_102028   DEBN JSLGA5                               18.617,37       0,00 10403 - Títulos Privados-Debêntures simples                  JSLG - JSL SA                                               
DEBN JSLGA5_102028   DEBN JSLGA5                                7.240,09       0,00 10403 - Títulos Privados-Debêntures simples                  JSLG - JSL SA                                               
DEBN JSLGA5_102028   DEBN JSLGA5                              491.291,78       0,01 10403 - Títulos Privados-Debêntures simples                  JSLG - JSL SA                                               
DEBN JSLGA5_102028   DEBN JSLGA5                               19.651,67       0,00 10403 - Títulos Privados-Debêntures simples                  JSLG - JSL SA                                               
DEBN JSLGA5_102028   DEBN JSLGA5                                6.205,79       0,00 10403 - Títulos Privados-Debêntures simples                  JSLG - JSL SA                                               
DEBN APRB28_062027   DEBN APRB28                               28.129,44       0,00 10403 - Títulos Privados-Debêntures simples                  APRB - AUTOPISTA REGIS BITTENCOURT SA                       
DEBN JSLGA5_102028   DEBN JSLGA5                              216.168,38       0,00 10403 - Títulos Privados-Debêntures simples                  JSLG - JSL SA                                               
DEBN JSLGA5_102028   DEBN JSLGA5                                4.137,19       0,00 10403 - Títulos Privados-Debêntures simples                  JSLG - JSL SA                                               
DEBN JSLGA5_102028   DEBN JSLGA5                               33.097,55       0,00 10403 - Títulos Privados-Debêntures simples                  JSLG - JSL SA                                               
DEBN JSLGA5_102028   DEBN JSLGA5                               47.577,73       0,00 10403 - Títulos Privados-Debêntures simples                  JSLG - JSL SA                                               
DEBN JSLGA5_102028   DEBN JSLGA5                              137.561,70       0,00 10403 - Títulos Privados-Debêntures simples                  JSLG - JSL SA                                               
DEBN JSLGA5_102028   DEBN JSLGA5                               22.754,57       0,00 10403 - Títulos Privados-Debêntures simples                  JSLG - JSL SA                                               
DEBN JSLGA5_102028   DEBN JSLGA5                              115.841,43       0,00 10403 - Títulos Privados-Debêntures simples                  JSLG - JSL SA                                               
DEBN JSLGA5_102028   DEBN JSLGA5                               19.651,67       0,00 10403 - Títulos Privados-Debêntures simples                  JSLG - JSL SA                                               
DEBN JSLGA5_102028   DEBN JSLGA5                               56.886,42       0,00 10403 - Títulos Privados-Debêntures simples                  JSLG - JSL SA                                               
DEBN JSLGA5_102028   DEBN JSLGA5                               24.823,16       0,00 10403 - Títulos Privados-Debêntures simples                  JSLG - JSL SA                                               
DEBN APRB28_062027   DEBN APRB28                               29.352,46       0,00 10403 - Títulos Privados-Debêntures simples                  APRB - AUTOPISTA REGIS BITTENCOURT SA                       
DEBN JSLGA5_102028   DEBN JSLGA5                               26.891,76       0,00 10403 - Títulos Privados-Debêntures simples                  JSLG - JSL SA                                               
DEBN JSLGA5_102028   DEBN JSLGA5                              234.785,76       0,00 10403 - Títulos Privados-Debêntures simples                  JSLG - JSL SA                                               
DEBN JSLGA5_102028   DEBN JSLGA5                               29.994,66       0,00 10403 - Títulos Privados-Debêntures simples                  JSLG - JSL SA                                               
DEBN JSLGA5_102028   DEBN JSLGA5                               92.052,57       0,00 10403 - Títulos Privados-Debêntures simples                  JSLG - JSL SA                                               
DEBN JSLGA5_102028   DEBN JSLGA5                               13.445,88       0,00 10403 - Títulos Privados-Debêntures simples                  JSLG - JSL SA                                               
DEBN JSLGA5_102028   DEBN JSLGA5                               22.754,57       0,00 10403 - Títulos Privados-Debêntures simples                  JSLG - JSL SA                                               
DEBN JSLGA5_102028   DEBN JSLGA5                               53.783,52       0,00 10403 - Títulos Privados-Debêntures simples                  JSLG - JSL SA                                               
DEBN JSLGA5_102028   DEBN JSLGA5                               67.229,40       0,00 10403 - Títulos Privados-Debêntures simples                  JSLG - JSL SA                                               
DEBN JSLGA5_102028   DEBN JSLGA5                               56.886,42       0,00 10403 - Títulos Privados-Debêntures simples                  JSLG - JSL SA                                               
DEBN JSLGA5_102028   DEBN JSLGA5                               63.092,21       0,00 10403 - Títulos Privados-Debêntures simples                  JSLG - JSL SA                                               
DEBN APRB28_062027   DEBN APRB28                            2.449.095,55       0,04 10403 - Títulos Privados-Debêntures simples                  APRB - AUTOPISTA REGIS BITTENCOURT SA                       
DEBN JSLGA5_102028   DEBN JSLGA5                               35.166,15       0,00 10403 - Títulos Privados-Debêntures simples                  JSLG - JSL SA                                               
DEBN JSLGA5_102028   DEBN JSLGA5                              133.424,51       0,00 10403 - Títulos Privados-Debêntures simples                  JSLG - JSL SA                                               
DEBN JSLGA5_102028   DEBN JSLGA5                                9.308,69       0,00 10403 - Títulos Privados-Debêntures simples                  JSLG - JSL SA                                               
DEBN JSLGA5_102028   DEBN JSLGA5                              125.150,12       0,00 10403 - Títulos Privados-Debêntures simples                  JSLG - JSL SA                                               
DEBN JSLGA5_102028   DEBN JSLGA5                               84.812,48       0,00 10403 - Títulos Privados-Debêntures simples                  JSLG - JSL SA                                               
DEBN JSLGA5_102028   DEBN JSLGA5                            1.092.219,21       0,02 10403 - Títulos Privados-Debêntures simples                  JSLG - JSL SA                                               
DEBN JSLGA5_102028   DEBN JSLGA5                               69.298,00       0,00 10403 - Títulos Privados-Debêntures simples                  JSLG - JSL SA                                               
DEBN JSLGA5_102028   DEBN JSLGA5                               94.121,16       0,00 10403 - Títulos Privados-Debêntures simples                  JSLG - JSL SA                                               
DEBN JSLGA5_102028   DEBN JSLGA5                               54.817,82       0,00 10403 - Títulos Privados-Debêntures simples                  JSLG - JSL SA                                               
DEBN KLBNA2_032029   DEBN KLBNA2                               21.652,88       0,00 10403 - Títulos Privados-Debêntures simples                  KLBN - KLABIN SA                                            
DEBN APRB28_062027   DEBN APRB28                               42.805,67       0,00 10403 - Títulos Privados-Debêntures simples                  APRB - AUTOPISTA REGIS BITTENCOURT SA                       
DEBN KLBNA2_032029   DEBN KLBNA2                               10.826,44       0,00 10403 - Títulos Privados-Debêntures simples                  KLBN - KLABIN SA                                            
DEBN KLBNA2_032029   DEBN KLBNA2                               10.826,44       0,00 10403 - Títulos Privados-Debêntures simples                  KLBN - KLABIN SA                                            
DEBN KLBNA2_032029   DEBN KLBNA2                               21.652,88       0,00 10403 - Títulos Privados-Debêntures simples                  KLBN - KLABIN SA                                            
DEBN KLBNA2_032029   DEBN KLBNA2                               21.652,88       0,00 10403 - Títulos Privados-Debêntures simples                  KLBN - KLABIN SA                                            
DEBN KLBNA2_032029   DEBN KLBNA2                               54.132,20       0,00 10403 - Títulos Privados-Debêntures simples                  KLBN - KLABIN SA                                            
DEBN KLBNA2_032029   DEBN KLBNA2                               32.479,32       0,00 10403 - Títulos Privados-Debêntures simples                  KLBN - KLABIN SA                                            
DEBN KLBNA2_032029   DEBN KLBNA2                              140.743,72       0,00 10403 - Títulos Privados-Debêntures simples                  KLBN - KLABIN SA                                            
DEBN KLBNA2_032029   DEBN KLBNA2                               10.826,44       0,00 10403 - Títulos Privados-Debêntures simples                  KLBN - KLABIN SA                                            
DEBN KLBNA2_032029   DEBN KLBNA2                              649.586,42       0,01 10403 - Títulos Privados-Debêntures simples                  KLBN - KLABIN SA                                            
DEBN KLBNA2_032029   DEBN KLBNA2                               75.785,08       0,00 10403 - Títulos Privados-Debêntures simples                  KLBN - KLABIN SA                                            
DEBN AEGPA0_052029   DEBN AEGPA0 H750651                        1.033,52       0,00 10440 - Títulos Privados-Debêntures Incent. (Lei 12.431)     AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN APRB28_062027   DEBN APRB28                               62.985,48       0,00 10403 - Títulos Privados-Debêntures simples                  APRB - AUTOPISTA REGIS BITTENCOURT SA                       
DEBN KLBNA2_032029   DEBN KLBNA2                              638.759,98       0,01 10403 - Títulos Privados-Debêntures simples                  KLBN - KLABIN SA                                            
DEBN KLBNA2_032029   DEBN KLBNA2                               64.958,64       0,00 10403 - Títulos Privados-Debêntures simples                  KLBN - KLABIN SA                                            
DEBN KLBNA2_032029   DEBN KLBNA2                               21.652,88       0,00 10403 - Títulos Privados-Debêntures simples                  KLBN - KLABIN SA                                            
DEBN KLBNA2_032029   DEBN KLBNA2                               64.958,64       0,00 10403 - Títulos Privados-Debêntures simples                  KLBN - KLABIN SA                                            
DEBN KLBNA2_032029   DEBN KLBNA2                            3.496.940,21       0,06 10403 - Títulos Privados-Debêntures simples                  KLBN - KLABIN SA                                            
DEBN KLBNA2_032029   DEBN KLBNA2                               32.479,32       0,00 10403 - Títulos Privados-Debêntures simples                  KLBN - KLABIN SA                                            
DEBN KLBNA2_032029   DEBN KLBNA2                               21.652,88       0,00 10403 - Títulos Privados-Debêntures simples                  KLBN - KLABIN SA                                            
DEBN KLBNA2_032029   DEBN KLBNA2                               32.479,32       0,00 10403 - Títulos Privados-Debêntures simples                  KLBN - KLABIN SA                                            
DEBN KLBNA2_032029   DEBN KLBNA2                               43.305,76       0,00 10403 - Títulos Privados-Debêntures simples                  KLBN - KLABIN SA                                            
DEBN KLBNA2_032029   DEBN KLBNA2                               43.305,76       0,00 10403 - Títulos Privados-Debêntures simples                  KLBN - KLABIN SA                                            
DEBN APRB28_062027   DEBN APRB28                               49.532,27       0,00 10403 - Títulos Privados-Debêntures simples                  APRB - AUTOPISTA REGIS BITTENCOURT SA                       
DEBN KLBNA2_032029   DEBN KLBNA2                               43.305,76       0,00 10403 - Títulos Privados-Debêntures simples                  KLBN - KLABIN SA                                            
DEBN KLBNA2_032029   DEBN KLBNA2                               32.479,32       0,00 10403 - Títulos Privados-Debêntures simples                  KLBN - KLABIN SA                                            
DEBN KLBNA2_032029   DEBN KLBNA2                               21.652,88       0,00 10403 - Títulos Privados-Debêntures simples                  KLBN - KLABIN SA                                            
DEBN KLBNA2_032029   DEBN KLBNA2                            5.564.790,30       0,10 10403 - Títulos Privados-Debêntures simples                  KLBN - KLABIN SA                                            
DEBN KLBNA2_032029   DEBN KLBNA2                               43.305,76       0,00 10403 - Títulos Privados-Debêntures simples                  KLBN - KLABIN SA                                            
DEBN KLBNA2_032029   DEBN KLBNA2                               43.305,76       0,00 10403 - Títulos Privados-Debêntures simples                  KLBN - KLABIN SA                                            
DEBN KLBNA2_032029   DEBN KLBNA2                               10.826,44       0,00 10403 - Títulos Privados-Debêntures simples                  KLBN - KLABIN SA                                            
DEBN KLBNA2_032029   DEBN KLBNA2                               21.652,88       0,00 10403 - Títulos Privados-Debêntures simples                  KLBN - KLABIN SA                                            
DEBN KLBNA2_032029   DEBN KLBNA2                               10.826,44       0,00 10403 - Títulos Privados-Debêntures simples                  KLBN - KLABIN SA                                            
DEBN KLBNA2_032029   DEBN KLBNA2                               32.479,32       0,00 10403 - Títulos Privados-Debêntures simples                  KLBN - KLABIN SA                                            
DEBN APRB28_062027   DEBN APRB28                                7.949,62       0,00 10403 - Títulos Privados-Debêntures simples                  APRB - AUTOPISTA REGIS BITTENCOURT SA                       
DEBN LCAMB4_052027   DEBN LCAMB4 H753337                       27.026,38       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN LCAMB4_052027   DEBN LCAMB4 H753337                        3.118,43       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN LCAMB4_052027   DEBN LCAMB4 H753337                       37.421,15       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN LCAMB4_052027   DEBN LCAMB4 H753337                      312.882,37       0,01 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN LCAMB4_052027   DEBN LCAMB4 H753337                       27.026,38       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN LCAMB4_052027   DEBN LCAMB4 H753337                       35.342,19       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN LCAMB4_052027   DEBN LCAMB4 H753337                       12.473,72       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN LCAMB4_052027   DEBN LCAMB4 H753337                       73.802,82       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN LCAMB4_052027   DEBN LCAMB4 H753337                       62.368,58       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN LCAMB4_052027   DEBN LCAMB4 H753337                       13.513,19       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN APRB28_062027   DEBN APRB28                               38.525,10       0,00 10403 - Títulos Privados-Debêntures simples                  APRB - AUTOPISTA REGIS BITTENCOURT SA                       
DEBN LCAMB4_052027   DEBN LCAMB4 H753337                        9.355,29       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN LCAMB4_052027   DEBN LCAMB4 H753337                        6.236,86       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN LCAMB4_052027   DEBN LCAMB4 H753337                       13.513,19       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN LCAMB4_052027   DEBN LCAMB4 H753337                      182.947,83       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN LCAMB4_052027   DEBN LCAMB4 H753337                       13.513,19       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN LCAMB4_052027   DEBN LCAMB4 H753337                      104.987,11       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN LCAMB4_052027   DEBN LCAMB4 H753337                       89.394,96       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN LCAMB4_052027   DEBN LCAMB4 H753337                       77.960,72       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN LCAMB4_052027   DEBN LCAMB4 H753337                       59.250,15       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN LCAMB4_052027   DEBN LCAMB4 H753337                       67.565,96       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN APRB28_062027   DEBN APRB28                               38.525,10       0,00 10403 - Títulos Privados-Debêntures simples                  APRB - AUTOPISTA REGIS BITTENCOURT SA                       
DEBN LCAMB4_052027   DEBN LCAMB4 H753337                       87.316,01       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN LCAMB4_052027   DEBN LCAMB4 H753337                       24.947,43       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN LCAMB4_052027   DEBN LCAMB4 H753337                       84.197,58       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN LCAMB4_052027   DEBN LCAMB4 H753337                       21.829,00       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN LCAMB4_052027   DEBN LCAMB4 H753337                        9.355,29       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN LCAMB4_052027   DEBN LCAMB4 H753337                       43.658,01       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN LCAMB4_052027   DEBN LCAMB4 H753337                      479.198,58       0,01 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN LCAMB4_052027   DEBN LCAMB4 H753337                       43.658,01       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN LCAMB4_052027   DEBN LCAMB4 H753337                       88.355,49       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN LCAMB4_052027   DEBN LCAMB4 H753337                       11.434,24       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN APRB28_062027   DEBN APRB28                               34.856,04       0,00 10403 - Títulos Privados-Debêntures simples                  APRB - AUTOPISTA REGIS BITTENCOURT SA                       
DEBN LCAMB4_052027   DEBN LCAMB4 H753337                       64.447,53       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN LCAMB4_052027   DEBN LCAMB4 H753337                      106.026,59       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN LCAMB4_052027   DEBN LCAMB4 H753337                        7.276,33       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN LCAMB4_052027   DEBN LCAMB4 H753337                       19.750,05       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN LCAMC3_042027   DEBN LCAMC3 H742904                       38.782,81       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN LCAMC3_042027   DEBN LCAMC3 H742904                       38.782,81       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN LCAMC3_042027   DEBN LCAMC3 H742904                       12.578,21       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN LCAMC3_042027   DEBN LCAMC3 H742904                       77.565,61       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN LCAMC3_042027   DEBN LCAMC3 H742904                        9.433,66       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN LCAMC3_042027   DEBN LCAMC3 H742904                       12.578,21       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN APRB28_062027   DEBN APRB28                               56.870,38       0,00 10403 - Títulos Privados-Debêntures simples                  APRB - AUTOPISTA REGIS BITTENCOURT SA                       
DEBN LCAMC3_042027   DEBN LCAMC3 H742904                        2.096,37       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN LCAMC3_042027   DEBN LCAMC3 H742904                        6.289,10       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN LCAMC3_042027   DEBN LCAMC3 H742904                       19.915,50       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN LCAMC3_042027   DEBN LCAMC3 H742904                      170.853,99       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN LCAMC3_042027   DEBN LCAMC3 H742904                      387.828,07       0,01 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN LCAMC3_042027   DEBN LCAMC3 H742904                       32.493,70       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN LCAMC3_042027   DEBN LCAMC3 H742904                      272.527,83       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN LCAMC3_042027   DEBN LCAMC3 H742904                        8.385,47       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN LCAMC3_042027   DEBN LCAMC3 H742904                       31.445,52       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN LCAMC3_042027   DEBN LCAMC3 H742904                       66.035,59       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN APRB28_062027   DEBN APRB28                               14.064,72       0,00 10403 - Títulos Privados-Debêntures simples                  APRB - AUTOPISTA REGIS BITTENCOURT SA                       
DEBN LCAMC3_042027   DEBN LCAMC3 H742904                       55.553,75       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN LCAMC3_042027   DEBN LCAMC3 H742904                        6.289,10       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN LCAMC3_042027   DEBN LCAMC3 H742904                       80.710,17       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN LCAMC3_042027   DEBN LCAMC3 H742904                        8.385,47       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN LCAMC3_042027   DEBN LCAMC3 H742904                       94.336,56       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN LCAMC3_042027   DEBN LCAMC3 H742904                       53.457,38       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN LCAMC3_042027   DEBN LCAMC3 H742904                       57.650,12       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN LCAMC3_042027   DEBN LCAMC3 H742904                       27.252,78       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN LCAMC3_042027   DEBN LCAMC3 H742904                       74.421,06       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN LCAMC3_042027   DEBN LCAMC3 H742904                       81.758,35       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN APRB28_062027   DEBN APRB28                              101.510,58       0,00 10403 - Títulos Privados-Debêntures simples                  APRB - AUTOPISTA REGIS BITTENCOURT SA                       
DEBN LCAMC3_042027   DEBN LCAMC3 H742904                       31.445,53       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN LCAMC3_042027   DEBN LCAMC3 H742904                       24.108,23       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN LCAMC3_042027   DEBN LCAMC3 H742904                       71.276,51       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN LCAMC3_042027   DEBN LCAMC3 H742904                       18.867,31       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN LCAMC3_042027   DEBN LCAMC3 H742904                       71.276,51       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN LCAMD2_112026   DEBN LCAMD2 I51900                        35.284,54       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN LCAMD2_112026   DEBN LCAMD2 I51900                         7.264,46       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN LCAMD2_112026   DEBN LCAMD2 I51900                         7.264,46       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN LCAMD2_112026   DEBN LCAMD2 I51900                        13.491,15       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN LCAMD2_112026   DEBN LCAMD2 I51900                       792.864,43       0,01 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN APRB28_062027   DEBN APRB28                              110.071,71       0,00 10403 - Títulos Privados-Debêntures simples                  APRB - AUTOPISTA REGIS BITTENCOURT SA                       
DEBN LCAMD2_112026   DEBN LCAMD2 I51900                       291.616,37       0,01 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN LCAMD2_112026   DEBN LCAMD2 I51900                        22.831,17       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN LCAMD2_112026   DEBN LCAMD2 I51900                        56.040,16       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN LCAMD2_112026   DEBN LCAMD2 I51900                        33.208,98       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN LCAMD2_112026   DEBN LCAMD2 I51900                        32.171,20       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN LCAMD2_112026   DEBN LCAMD2 I51900                        41.511,23       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN LCAMD2_112026   DEBN LCAMD2 I51900                         1.037,78       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN LCAMD2_112026   DEBN LCAMD2 I51900                        13.491,15       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN LCAMD2_112026   DEBN LCAMD2 I51900                         6.226,68       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN LCAMD2_112026   DEBN LCAMD2 I51900                       189.913,86       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN AEGPA0_052029   DEBN AEGPA0 H750651                       33.072,50       0,00 10440 - Títulos Privados-Debêntures Incent. (Lei 12.431)     AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN APRB28_062027   DEBN APRB28                                7.338,11       0,00 10403 - Títulos Privados-Debêntures simples                  APRB - AUTOPISTA REGIS BITTENCOURT SA                       
DEBN LCAMD2_112026   DEBN LCAMD2 I51900                       114.155,87       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN LCAMD2_112026   DEBN LCAMD2 I51900                        43.586,79       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN LCAMD2_112026   DEBN LCAMD2 I51900                        13.491,15       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN LCAMD2_112026   DEBN LCAMD2 I51900                        10.377,81       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN LCAMD2_112026   DEBN LCAMD2 I51900                        29.057,86       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN LCAMD2_112026   DEBN LCAMD2 I51900                         6.226,68       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN LCAMD2_112026   DEBN LCAMD2 I51900                        31.133,42       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN LCAMD2_112026   DEBN LCAMD2 I51900                       118.307,00       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN LCAMD2_112026   DEBN LCAMD2 I51900                        24.906,74       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN LCAMD2_112026   DEBN LCAMD2 I51900                        17.642,27       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN BRKPA0_042027   DEBN BRKPA0 H752145                        1.045,58       0,00 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN LCAMD2_112026   DEBN LCAMD2 I51900                        13.491,15       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN LCAMD2_112026   DEBN LCAMD2 I51900                         8.302,25       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN LCAMD2_112026   DEBN LCAMD2 I51900                        48.775,69       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN LCAMD2_112026   DEBN LCAMD2 I51900                        41.511,23       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN LCAMD2_112026   DEBN LCAMD2 I51900                        36.322,32       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN LCAMD2_112026   DEBN LCAMD2 I51900                        36.322,32       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN LCAMD2_112026   DEBN LCAMD2 I51900                        56.040,16       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN LCAMD2_112026   DEBN LCAMD2 I51900                         3.113,34       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN LCAMD2_112026   DEBN LCAMD2 I51900                        17.642,27       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN LCAMD2_112026   DEBN LCAMD2 I51900                        42.549,01       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN BRKPA0_042027   DEBN BRKPA0 H752145                       84.692,37       0,00 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN LORTA5_042026   DEBN LORTA5                               29.061,62       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN LORTA5_042026   DEBN LORTA5                               21.796,21       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN LORTA5_042026   DEBN LORTA5                                9.341,23       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN LORTA5_042026   DEBN LORTA5                                4.151,66       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN LORTA5_042026   DEBN LORTA5                               53.971,58       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN LORTA5_042026   DEBN LORTA5                               32.175,36       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN LORTA5_042026   DEBN LORTA5                               21.796,21       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN LORTA5_042026   DEBN LORTA5                               11.417,06       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN LORTA5_042026   DEBN LORTA5                               45.668,26       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN LORTA5_042026   DEBN LORTA5                              188.900,53       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN BRKPA0_042027   DEBN BRKPA0 H752145                      121.287,83       0,00 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN LORTA5_042026   DEBN LORTA5                                5.189,57       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN LORTA5_042026   DEBN LORTA5                                7.265,40       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN LORTA5_042026   DEBN LORTA5                                5.189,57       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN LORTA5_042026   DEBN LORTA5                                3.113,74       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN LORTA5_042026   DEBN LORTA5                                7.265,40       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN LORTA5_042026   DEBN LORTA5                               83.033,20       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN LORTA5_042026   DEBN LORTA5                               22.834,13       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN LORTA5_042026   DEBN LORTA5                               13.492,89       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN LORTA5_042026   DEBN LORTA5                                2.075,83       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN LORTA5_042026   DEBN LORTA5                               14.530,80       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN BRKPA0_042027   DEBN BRKPA0 H752145                       61.689,50       0,00 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN LORTA5_042026   DEBN LORTA5                              274.009,56       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN LORTA5_042026   DEBN LORTA5                               53.971,58       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN LORTA5_042026   DEBN LORTA5                              121.436,05       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN LORTA5_042026   DEBN LORTA5                               29.061,62       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN LORTA5_042026   DEBN LORTA5                               37.364,94       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN LORTA5_042026   DEBN LORTA5                               18.682,47       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN LORTA5_042026   DEBN LORTA5                               18.682,47       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN LORTA5_042026   DEBN LORTA5                               55.009,49       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN LORTA5_042026   DEBN LORTA5                               13.492,89       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN LORTA5_042026   DEBN LORTA5                               35.289,11       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN BRKPA0_042027   DEBN BRKPA0 H752145                    1.862.186,46       0,03 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN LORTA5_042026   DEBN LORTA5                                4.151,66       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN LORTA5_042026   DEBN LORTA5                                6.227,49       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN LORTA5_042026   DEBN LORTA5                               35.289,11       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN LORTA5_042026   DEBN LORTA5                               49.819,92       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN LORTA5_042026   DEBN LORTA5                               37.364,94       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN LORTA5_042026   DEBN LORTA5                               42.554,51       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN LORTA5_042026   DEBN LORTA5                               32.175,36       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN LORTA5_042026   DEBN LORTA5                               43.592,43       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN LORTA5_042026   DEBN LORTA5                               36.327,02       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN LORTA5_042026   DEBN LORTA5                               24.909,96       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN BRKPA0_042027   DEBN BRKPA0 H752145                    1.025.718,65       0,02 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN LORTA5_042026   DEBN LORTA5                               13.492,89       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN LORTA5_042026   DEBN LORTA5                                9.341,23       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN LORTA8_102026   DEBN LORTA8 H890420A                      74.565,74       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN LORTA8_102026   DEBN LORTA8 H890420A                   2.228.570,47       0,04 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN LORTA8_102026   DEBN LORTA8 H890420A                     378.079,82       0,01 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN LORTA8_102026   DEBN LORTA8 H890420A                      73.515,52       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN LORTA8_102026   DEBN LORTA8 H890420A                     579.722,39       0,01 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN LORTA8_102026   DEBN LORTA8 H890420A                      19.954,21       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN LORTA8_102026   DEBN LORTA8 H890420A                     436.892,23       0,01 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN LORTA8_102026   DEBN LORTA8 H890420A                     403.285,14       0,01 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN BRKPA0_042027   DEBN BRKPA0 H752145                       85.737,95       0,00 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN LORTA8_102026   DEBN LORTA8 H890420A                     365.477,16       0,01 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN LORTA8_102026   DEBN LORTA8 H890420A                   2.187.611,83       0,04 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN LORTA8_102026   DEBN LORTA8 H890420A                     375.979,37       0,01 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN LORTA8_102026   DEBN LORTA8 H890420A                     155.432,82       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN LORTA8_102026   DEBN LORTA8 H890420A                     114.474,17       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN LORTA8_102026   DEBN LORTA8 H890420A                     166.985,25       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN LORTA8_102026   DEBN LORTA8 H890420A                     215.295,45       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN LORTA8_102026   DEBN LORTA8 H890420A                     303.514,07       0,01 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN LORTA8_102026   DEBN LORTA8 H890420A                     261.505,21       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN LORTA8_102026   DEBN LORTA8 H890420A                     968.304,42       0,02 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN BRKPA0_042027   DEBN BRKPA0 H752145                        4.182,34       0,00 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN LORTA8_102026   DEBN LORTA8 H890420A                   1.037.619,05       0,02 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN LORTA8_102026   DEBN LORTA8 H890420A                      85.067,96       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN LORTA8_102026   DEBN LORTA8 H890420A                      37.807,98       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN LORTA8_102026   DEBN LORTA8 H890420A                      56.711,97       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN LORTA8_102026   DEBN LORTA8 H890420A                     498.855,31       0,01 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN LORTA8_102026   DEBN LORTA8 H890420A                      69.314,63       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN LORTA8_102026   DEBN LORTA8 H890420A                   1.038.669,27       0,02 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN LORTA8_102026   DEBN LORTA8 H890420A                   3.122.309,15       0,06 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN LORTA8_102026   DEBN LORTA8 H890420A                      85.067,96       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN LORTA8_102026   DEBN LORTA8 H890420A                     276.208,32       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN BRKPA0_042027   DEBN BRKPA0 H752145                       64.826,26       0,00 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN LORTA8_102026   DEBN LORTA8 H890420A                     265.706,09       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN LORTA8_102026   DEBN LORTA8 H890420A                      88.218,62       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN LORTA8_102026   DEBN LORTA8 H890420A                     258.354,54       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN LORTA8_102026   DEBN LORTA8 H890420A                     221.596,78       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN LORTA8_102026   DEBN LORTA8 H890420A                     322.418,07       0,01 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN LORTA8_102026   DEBN LORTA8 H890420A                     434.791,79       0,01 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN LORTA9_022027   DEBN LORTA9_022027 J77688                 13.816,35       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN LORTA9_022027   DEBN LORTA9_022027 J77688                534.586,34       0,01 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN LORTA9_022027   DEBN LORTA9_022027 J77688                889.560,17       0,02 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN LORTB2_122028   DEBN LORTB2 I203215                       11.337,95       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN AEGPA0_052029   DEBN AEGPA0 H750651                        6.201,09       0,00 10440 - Títulos Privados-Debêntures Incent. (Lei 12.431)     AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN BRKPA0_042027   DEBN BRKPA0 H752145                       95.148,21       0,00 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN LORTB2_122028   DEBN LORTB2 I203215                       55.659,05       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN LORTB2_122028   DEBN LORTB2 I203215                      687.492,30       0,01 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN LORTB2_122028   DEBN LORTB2 I203215                      203.052,45       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN LORTB2_122028   DEBN LORTB2 I203215                       18.553,02       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN LORTB2_122028   DEBN LORTB2 I203215                      467.948,28       0,01 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN LORTB2_122028   DEBN LORTB2 I203215                       53.597,60       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN LORTB2_122028   DEBN LORTB2 I203215                       17.522,29       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN LORTB2_122028   DEBN LORTB2 I203215                       15.460,85       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN LORTB2_122028   DEBN LORTB2 I203215                      111.318,10       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN LORTB2_122028   DEBN LORTB2 I203215                       26.798,80       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN BRKPA0_042027   DEBN BRKPA0 H752145                       81.555,61       0,00 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN LORTB2_122028   DEBN LORTB2 I203215                       53.597,60       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN LORTB2_122028   DEBN LORTB2 I203215                       74.212,06       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN LORTB2_122028   DEBN LORTB2 I203215                       34.013,86       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN LORTB2_122028   DEBN LORTB2 I203215                       34.013,87       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN LORTB2_122028   DEBN LORTB2 I203215                        4.122,89       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN LORTB2_122028   DEBN LORTB2 I203215                        8.245,78       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN LORTB2_122028   DEBN LORTB2 I203215                       12.368,68       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN LORTB2_122028   DEBN LORTB2 I203215                       24.737,36       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN LORTB2_122028   DEBN LORTB2 I203215                       10.307,23       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN LORTB2_122028   DEBN LORTB2 I203215                       43.290,37       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN BRKPA0_042027   DEBN BRKPA0 H752145                       77.373,27       0,00 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN LORTB2_122028   DEBN LORTB2 I203215                       77.304,23       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN LORTB2_122028   DEBN LORTB2 I203215                      142.239,79       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN LORTB2_122028   DEBN LORTB2 I203215                      225.728,36       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN LORTB2_122028   DEBN LORTB2 I203215                       85.550,02       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN LORTB2_122028   DEBN LORTB2 I203215                        8.245,78       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN LORTB2_122028   DEBN LORTB2 I203215                       61.843,39       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN LORTB2_122028   DEBN LORTB2 I203215                       16.491,57       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN LORTB2_122028   DEBN LORTB2 I203215                      121.625,32       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN LORTB2_122028   DEBN LORTB2 I203215                      105.133,75       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN LORTB2_122028   DEBN LORTB2 I203215                       92.765,08       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN BRKPA0_042027   DEBN BRKPA0 H752145                    2.225.004,37       0,04 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN LORTB2_122028   DEBN LORTB2 I203215                       91.734,35       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN LORTB2_122028   DEBN LORTB2 I203215                      491.654,91       0,01 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN LORTB2_122028   DEBN LORTB2 I203215                       80.396,40       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN LORTB2_122028   DEBN LORTB2 I203215                       46.382,54       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN LORTB2_122028   DEBN LORTB2 I203215                       32.983,14       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN LORTB2_122028   DEBN LORTB2 I203215                       21.645,18       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN LORTB2_122028   DEBN LORTB2 I203215                       74.212,06       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN LORTB2_122028   DEBN LORTB2 I203215                       87.611,46       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN LORTB2_122028   DEBN LORTB2 I203215                      107.195,20       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN LORTB9_022029   DEBN LORTB9 I627204                      292.439,89       0,01 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN BRKPA0_042027   DEBN BRKPA0 H752145                      674.402,17       0,01 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN LORTB9_022029   DEBN LORTB9 I627204                      972.657,21       0,02 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN LORTB9_022029   DEBN LORTB9 I627204                    1.926.032,66       0,03 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN LORTB9_022029   DEBN LORTB9 I627204                       76.055,79       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN LORTB9_022029   DEBN LORTB9 I627204                   11.143.780,75       0,20 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN LORTB9_022029   DEBN LORTB9 I627204                       20.352,96       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN LORTB9_022029   DEBN LORTB9 I627204                      163.894,87       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN LORTB9_022029   DEBN LORTB9 I627204                    1.326.155,97       0,02 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN LORTB9_022029   DEBN LORTB9 I627204                    2.878.336,91       0,05 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN MGLUA0_102026   DEBN MGLUA0 I338896                    3.417.372,71       0,06 10403 - Títulos Privados-Debêntures simples                  MGLU - MAGAZINE LUIZA SA                                    
DEBN MGLUA0_102026   DEBN MGLUA0 I338896                      107.377,81       0,00 10403 - Títulos Privados-Debêntures simples                  MGLU - MAGAZINE LUIZA SA                                    
DEBN BRKPA0_042027   DEBN BRKPA0 H752145                      139.062,77       0,00 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN MGLUA0_102026   DEBN MGLUA0 I338896                      122.154,57       0,00 10403 - Títulos Privados-Debêntures simples                  MGLU - MAGAZINE LUIZA SA                                    
DEBN MGLUA0_102026   DEBN MGLUA0 I338896                      208.844,92       0,00 10403 - Títulos Privados-Debêntures simples                  MGLU - MAGAZINE LUIZA SA                                    
DEBN MGLUA0_102026   DEBN MGLUA0 I338896                      163.529,51       0,00 10403 - Títulos Privados-Debêntures simples                  MGLU - MAGAZINE LUIZA SA                                    
DEBN MGLUA0_102026   DEBN MGLUA0 I338896                      180.276,51       0,00 10403 - Títulos Privados-Debêntures simples                  MGLU - MAGAZINE LUIZA SA                                    
DEBN MGLUA0_102026   DEBN MGLUA0 I338896                    2.401.716,54       0,04 10403 - Títulos Privados-Debêntures simples                  MGLU - MAGAZINE LUIZA SA                                    
DEBN MGLUA0_102026   DEBN MGLUA0 I338896                      160.574,16       0,00 10403 - Títulos Privados-Debêntures simples                  MGLU - MAGAZINE LUIZA SA                                    
DEBN MGLUA0_102026   DEBN MGLUA0 I338896                   12.422.332,03       0,22 10403 - Títulos Privados-Debêntures simples                  MGLU - MAGAZINE LUIZA SA                                    
DEBN MGLUA0_102026   DEBN MGLUA0 I338896                      124.124,81       0,00 10403 - Títulos Privados-Debêntures simples                  MGLU - MAGAZINE LUIZA SA                                    
DEBN MGLUA0_102026   DEBN MGLUA0 I338896                   14.956.054,31       0,27 10403 - Títulos Privados-Debêntures simples                  MGLU - MAGAZINE LUIZA SA                                    
DEBN MGLUA0_102026   DEBN MGLUA0 I338896                        8.866,06       0,00 10403 - Títulos Privados-Debêntures simples                  MGLU - MAGAZINE LUIZA SA                                    
DEBN BRKPA0_042027   DEBN BRKPA0 H752145                      123.379,00       0,00 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN MGLUA0_102026   DEBN MGLUA0 I338896                      231.502,62       0,00 10403 - Títulos Privados-Debêntures simples                  MGLU - MAGAZINE LUIZA SA                                    
DEBN MGLUA0_102026   DEBN MGLUA0 I338896                   18.235.510,56       0,33 10403 - Títulos Privados-Debêntures simples                  MGLU - MAGAZINE LUIZA SA                                    
DEBN MGLUA0_102026   DEBN MGLUA0 I338896                      109.348,05       0,00 10403 - Títulos Privados-Debêntures simples                  MGLU - MAGAZINE LUIZA SA                                    
DEBN MGLUA0_102026   DEBN MGLUA0 I338896                      214.755,62       0,00 10403 - Títulos Privados-Debêntures simples                  MGLU - MAGAZINE LUIZA SA                                    
DEBN MGLUA0_102026   DEBN MGLUA0 I338896                      239.383,56       0,00 10403 - Títulos Privados-Debêntures simples                  MGLU - MAGAZINE LUIZA SA                                    
DEBN MGLUA0_102026   DEBN MGLUA0 I338896                      322.133,43       0,01 10403 - Títulos Privados-Debêntures simples                  MGLU - MAGAZINE LUIZA SA                                    
DEBN MGLUA0_102026   DEBN MGLUA0 I338896                      157.618,80       0,00 10403 - Títulos Privados-Debêntures simples                  MGLU - MAGAZINE LUIZA SA                                    
DEBN MGLUA0_102026   DEBN MGLUA0 I338896                      308.341,79       0,01 10403 - Títulos Privados-Debêntures simples                  MGLU - MAGAZINE LUIZA SA                                    
DEBN MGLUA0_102026   DEBN MGLUA0 I338896                   15.191.497,40       0,27 10403 - Títulos Privados-Debêntures simples                  MGLU - MAGAZINE LUIZA SA                                    
DEBN MGLUA0_102026   DEBN MGLUA0 I338896                      163.529,51       0,00 10403 - Títulos Privados-Debêntures simples                  MGLU - MAGAZINE LUIZA SA                                    
DEBN BRKPA0_042027   DEBN BRKPA0 H752145                      364.909,08       0,01 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN MGLUA0_102026   DEBN MGLUA0 I338896                      164.514,63       0,00 10403 - Títulos Privados-Debêntures simples                  MGLU - MAGAZINE LUIZA SA                                    
DEBN MGLUA0_102026   DEBN MGLUA0 I338896                      164.514,63       0,00 10403 - Títulos Privados-Debêntures simples                  MGLU - MAGAZINE LUIZA SA                                    
DEBN MGLUA0_102026   DEBN MGLUA0 I338896                          985,12       0,00 10403 - Títulos Privados-Debêntures simples                  MGLU - MAGAZINE LUIZA SA                                    
DEBN MGLUA0_102026   DEBN MGLUA0 I338896                      207.859,80       0,00 10403 - Títulos Privados-Debêntures simples                  MGLU - MAGAZINE LUIZA SA                                    
DEBN MGLUA0_102026   DEBN MGLUA0 I338896                       26.598,17       0,00 10403 - Títulos Privados-Debêntures simples                  MGLU - MAGAZINE LUIZA SA                                    
DEBN MRVEB2_072025   DEBN MRVEB2 I650257                       75.876,07       0,00 10403 - Títulos Privados-Debêntures simples                  MRVE - MRV ENGENHARIA PARTICIPACOES SA                      
DEBN MRVEB2_072025   DEBN MRVEB2 I650257                        5.058,40       0,00 10403 - Títulos Privados-Debêntures simples                  MRVE - MRV ENGENHARIA PARTICIPACOES SA                      
DEBN MRVEB2_072025   DEBN MRVEB2 I650257                       35.408,83       0,00 10403 - Títulos Privados-Debêntures simples                  MRVE - MRV ENGENHARIA PARTICIPACOES SA                      
DEBN MRVEB2_072025   DEBN MRVEB2 I650257                       50.584,04       0,00 10403 - Títulos Privados-Debêntures simples                  MRVE - MRV ENGENHARIA PARTICIPACOES SA                      
DEBN MRVEB2_072025   DEBN MRVEB2 I650257                       30.350,43       0,00 10403 - Títulos Privados-Debêntures simples                  MRVE - MRV ENGENHARIA PARTICIPACOES SA                      
DEBN BRKPA0_042027   DEBN BRKPA0 H752145                      158.928,88       0,00 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN MRVEB2_072025   DEBN MRVEB2 I650257                      318.679,48       0,01 10403 - Títulos Privados-Debêntures simples                  MRVE - MRV ENGENHARIA PARTICIPACOES SA                      
DEBN MRVEB2_072025   DEBN MRVEB2 I650257                       30.350,43       0,00 10403 - Títulos Privados-Debêntures simples                  MRVE - MRV ENGENHARIA PARTICIPACOES SA                      
DEBN MRVEB2_072025   DEBN MRVEB2 I650257                      217.511,39       0,00 10403 - Títulos Privados-Debêntures simples                  MRVE - MRV ENGENHARIA PARTICIPACOES SA                      
DEBN MRVEB2_072025   DEBN MRVEB2 I650257                        5.058,40       0,00 10403 - Títulos Privados-Debêntures simples                  MRVE - MRV ENGENHARIA PARTICIPACOES SA                      
DEBN MRVEB2_072025   DEBN MRVEB2 I650257                       10.116,81       0,00 10403 - Títulos Privados-Debêntures simples                  MRVE - MRV ENGENHARIA PARTICIPACOES SA                      
DEBN MRVEB2_072025   DEBN MRVEB2 I650257                       70.817,66       0,00 10403 - Títulos Privados-Debêntures simples                  MRVE - MRV ENGENHARIA PARTICIPACOES SA                      
DEBN MRVEB2_072025   DEBN MRVEB2 I650257                        5.058,40       0,00 10403 - Títulos Privados-Debêntures simples                  MRVE - MRV ENGENHARIA PARTICIPACOES SA                      
DEBN MRVEB2_072025   DEBN MRVEB2 I650257                        5.058,40       0,00 10403 - Títulos Privados-Debêntures simples                  MRVE - MRV ENGENHARIA PARTICIPACOES SA                      
DEBN MRVEB2_072025   DEBN MRVEB2 I650257                        5.058,40       0,00 10403 - Títulos Privados-Debêntures simples                  MRVE - MRV ENGENHARIA PARTICIPACOES SA                      
DEBN MRVEB2_072025   DEBN MRVEB2 I650257                        5.058,40       0,00 10403 - Títulos Privados-Debêntures simples                  MRVE - MRV ENGENHARIA PARTICIPACOES SA                      
DEBN BRKPA0_042027   DEBN BRKPA0 H752145                      193.433,18       0,00 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN MRVEB2_072025   DEBN MRVEB2 I650257                        5.058,40       0,00 10403 - Títulos Privados-Debêntures simples                  MRVE - MRV ENGENHARIA PARTICIPACOES SA                      
DEBN MRVEB2_072025   DEBN MRVEB2 I650257                        5.058,40       0,00 10403 - Títulos Privados-Debêntures simples                  MRVE - MRV ENGENHARIA PARTICIPACOES SA                      
DEBN MRVEB2_072025   DEBN MRVEB2 I650257                       10.116,80       0,00 10403 - Títulos Privados-Debêntures simples                  MRVE - MRV ENGENHARIA PARTICIPACOES SA                      
DEBN MRVEB2_072025   DEBN MRVEB2 I650257                        5.058,40       0,00 10403 - Títulos Privados-Debêntures simples                  MRVE - MRV ENGENHARIA PARTICIPACOES SA                      
DEBN MRVEB2_072025   DEBN MRVEB2 I650257                        5.058,40       0,00 10403 - Títulos Privados-Debêntures simples                  MRVE - MRV ENGENHARIA PARTICIPACOES SA                      
DEBN MRVEB2_072025   DEBN MRVEB2 I650257                    1.340.477,16       0,02 10403 - Títulos Privados-Debêntures simples                  MRVE - MRV ENGENHARIA PARTICIPACOES SA                      
DEBN MRVEB2_072025   DEBN MRVEB2 I650257                       45.525,64       0,00 10403 - Títulos Privados-Debêntures simples                  MRVE - MRV ENGENHARIA PARTICIPACOES SA                      
DEBN MRVEB2_072025   DEBN MRVEB2 I650257                        5.058,40       0,00 10403 - Títulos Privados-Debêntures simples                  MRVE - MRV ENGENHARIA PARTICIPACOES SA                      
DEBN MRVEB2_072025   DEBN MRVEB2 I650257                        5.058,40       0,00 10403 - Títulos Privados-Debêntures simples                  MRVE - MRV ENGENHARIA PARTICIPACOES SA                      
DEBN MRVEB2_072025   DEBN MRVEB2 I650257                        5.058,40       0,00 10403 - Títulos Privados-Debêntures simples                  MRVE - MRV ENGENHARIA PARTICIPACOES SA                      
DEBN AEGPA0_052029   DEBN AEGPA0 H750651                       10.335,16       0,00 10440 - Títulos Privados-Debêntures Incent. (Lei 12.431)     AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN BRKPA0_042027   DEBN BRKPA0 H752145                       63.780,67       0,00 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN NIGP12_032032   DEBN NIGP12 I831258                    5.357.403,94       0,10 10403 - Títulos Privados-Debêntures simples                  NTSD - NOVA TRANSPORTADORA SUDESTE SA - NTS                 
DEBN NIGP12_032032   DEBN NIGP12 I831258                       30.206,87       0,00 10403 - Títulos Privados-Debêntures simples                  NTSD - NOVA TRANSPORTADORA SUDESTE SA - NTS                 
DEBN NIGP12_032032   DEBN NIGP12 I831258                        7.551,72       0,00 10403 - Títulos Privados-Debêntures simples                  NTSD - NOVA TRANSPORTADORA SUDESTE SA - NTS                 
DEBN NIGP12_032032   DEBN NIGP12 I831258                       21.576,33       0,00 10403 - Títulos Privados-Debêntures simples                  NTSD - NOVA TRANSPORTADORA SUDESTE SA - NTS                 
DEBN NIGP12_032032   DEBN NIGP12 I831258                       25.891,60       0,00 10403 - Títulos Privados-Debêntures simples                  NTSD - NOVA TRANSPORTADORA SUDESTE SA - NTS                 
DEBN NIGP12_032032   DEBN NIGP12 I831258                        8.630,53       0,00 10403 - Títulos Privados-Debêntures simples                  NTSD - NOVA TRANSPORTADORA SUDESTE SA - NTS                 
DEBN NIGP12_032032   DEBN NIGP12 I831258                       20.497,52       0,00 10403 - Títulos Privados-Debêntures simples                  NTSD - NOVA TRANSPORTADORA SUDESTE SA - NTS                 
DEBN NIGP12_032032   DEBN NIGP12 I831258                       22.655,15       0,00 10403 - Títulos Privados-Debêntures simples                  NTSD - NOVA TRANSPORTADORA SUDESTE SA - NTS                 
DEBN NIGP12_032032   DEBN NIGP12 I831258                        7.551,72       0,00 10403 - Títulos Privados-Debêntures simples                  NTSD - NOVA TRANSPORTADORA SUDESTE SA - NTS                 
DEBN NIGP12_032032   DEBN NIGP12 I831258                       25.891,60       0,00 10403 - Títulos Privados-Debêntures simples                  NTSD - NOVA TRANSPORTADORA SUDESTE SA - NTS                 
DEBN BRKPA0_042027   DEBN BRKPA0 H752145                       37.641,05       0,00 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN NIGP12_032032   DEBN NIGP12 I831258                       20.497,52       0,00 10403 - Títulos Privados-Debêntures simples                  NTSD - NOVA TRANSPORTADORA SUDESTE SA - NTS                 
DEBN NIGP12_032032   DEBN NIGP12 I831258                       38.837,40       0,00 10403 - Títulos Privados-Debêntures simples                  NTSD - NOVA TRANSPORTADORA SUDESTE SA - NTS                 
DEBN NIGP12_032032   DEBN NIGP12 I831258                       15.103,43       0,00 10403 - Títulos Privados-Debêntures simples                  NTSD - NOVA TRANSPORTADORA SUDESTE SA - NTS                 
DEBN NIGP12_032032   DEBN NIGP12 I831258                       12.945,80       0,00 10403 - Títulos Privados-Debêntures simples                  NTSD - NOVA TRANSPORTADORA SUDESTE SA - NTS                 
DEBN NIGP12_032032   DEBN NIGP12 I831258                        1.078,82       0,00 10403 - Títulos Privados-Debêntures simples                  NTSD - NOVA TRANSPORTADORA SUDESTE SA - NTS                 
DEBN NIGP12_032032   DEBN NIGP12 I831258                       49.625,57       0,00 10403 - Títulos Privados-Debêntures simples                  NTSD - NOVA TRANSPORTADORA SUDESTE SA - NTS                 
DEBN NIGP12_032032   DEBN NIGP12 I831258                       20.497,52       0,00 10403 - Títulos Privados-Debêntures simples                  NTSD - NOVA TRANSPORTADORA SUDESTE SA - NTS                 
DEBN NIGP12_032032   DEBN NIGP12 I831258                       45.310,30       0,00 10403 - Títulos Privados-Debêntures simples                  NTSD - NOVA TRANSPORTADORA SUDESTE SA - NTS                 
DEBN NIGP12_032032   DEBN NIGP12 I831258                       32.364,50       0,00 10403 - Títulos Privados-Debêntures simples                  NTSD - NOVA TRANSPORTADORA SUDESTE SA - NTS                 
DEBN NIGP12_032032   DEBN NIGP12 I831258                        4.315,27       0,00 10403 - Títulos Privados-Debêntures simples                  NTSD - NOVA TRANSPORTADORA SUDESTE SA - NTS                 
DEBN BRKPA0_042027   DEBN BRKPA0 H752145                       48.096,90       0,00 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN NIGP12_032032   DEBN NIGP12 I831258                       28.049,23       0,00 10403 - Títulos Privados-Debêntures simples                  NTSD - NOVA TRANSPORTADORA SUDESTE SA - NTS                 
DEBN NIGP12_032032   DEBN NIGP12 I831258                        6.472,90       0,00 10403 - Títulos Privados-Debêntures simples                  NTSD - NOVA TRANSPORTADORA SUDESTE SA - NTS                 
DEBN NIGP12_032032   DEBN NIGP12 I831258                       12.945,80       0,00 10403 - Títulos Privados-Debêntures simples                  NTSD - NOVA TRANSPORTADORA SUDESTE SA - NTS                 
DEBN NIGP12_032032   DEBN NIGP12 I831258                       20.497,52       0,00 10403 - Títulos Privados-Debêntures simples                  NTSD - NOVA TRANSPORTADORA SUDESTE SA - NTS                 
DEBN NIGP12_032032   DEBN NIGP12 I831258                       20.497,52       0,00 10403 - Títulos Privados-Debêntures simples                  NTSD - NOVA TRANSPORTADORA SUDESTE SA - NTS                 
DEBN NIGP12_032032   DEBN NIGP12 I831258                       15.103,43       0,00 10403 - Títulos Privados-Debêntures simples                  NTSD - NOVA TRANSPORTADORA SUDESTE SA - NTS                 
DEBN NIGP12_032032   DEBN NIGP12 I831258                    2.074.564,59       0,04 10403 - Títulos Privados-Debêntures simples                  NTSD - NOVA TRANSPORTADORA SUDESTE SA - NTS                 
DEBN NIGP12_032032   DEBN NIGP12 I831258                      491.940,43       0,01 10403 - Títulos Privados-Debêntures simples                  NTSD - NOVA TRANSPORTADORA SUDESTE SA - NTS                 
DEBN NIGP12_032032   DEBN NIGP12 I831258                      161.822,51       0,00 10403 - Títulos Privados-Debêntures simples                  NTSD - NOVA TRANSPORTADORA SUDESTE SA - NTS                 
DEBN NTSD25_092029   DEBN NTSD25 H924761                      161.320,93       0,00 10403 - Títulos Privados-Debêntures simples                  NTSD - NOVA TRANSPORTADORA SUDESTE SA - NTS                 
DEBN BRKPA0_042027   DEBN BRKPA0 H752145                      196.569,94       0,00 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN NTSD25_092029   DEBN NTSD25 H924761                       76.358,58       0,00 10403 - Títulos Privados-Debêntures simples                  NTSD - NOVA TRANSPORTADORA SUDESTE SA - NTS                 
DEBN NTSD25_092029   DEBN NTSD25 H924761                       18.283,04       0,00 10403 - Títulos Privados-Debêntures simples                  NTSD - NOVA TRANSPORTADORA SUDESTE SA - NTS                 
DEBN NTSD25_092029   DEBN NTSD25 H924761                        1.075,47       0,00 10403 - Títulos Privados-Debêntures simples                  NTSD - NOVA TRANSPORTADORA SUDESTE SA - NTS                 
DEBN NTSD25_092029   DEBN NTSD25 H924761                       98.943,51       0,00 10403 - Títulos Privados-Debêntures simples                  NTSD - NOVA TRANSPORTADORA SUDESTE SA - NTS                 
DEBN NTSD25_092029   DEBN NTSD25 H924761                      110.773,71       0,00 10403 - Títulos Privados-Debêntures simples                  NTSD - NOVA TRANSPORTADORA SUDESTE SA - NTS                 
DEBN NTSD25_092029   DEBN NTSD25 H924761                      100.018,98       0,00 10403 - Títulos Privados-Debêntures simples                  NTSD - NOVA TRANSPORTADORA SUDESTE SA - NTS                 
DEBN NTSD25_092029   DEBN NTSD25 H924761                       11.830,20       0,00 10403 - Títulos Privados-Debêntures simples                  NTSD - NOVA TRANSPORTADORA SUDESTE SA - NTS                 
DEBN NTSD25_092029   DEBN NTSD25 H924761                       37.641,55       0,00 10403 - Títulos Privados-Debêntures simples                  NTSD - NOVA TRANSPORTADORA SUDESTE SA - NTS                 
DEBN NTSD25_092029   DEBN NTSD25 H924761                       98.943,51       0,00 10403 - Títulos Privados-Debêntures simples                  NTSD - NOVA TRANSPORTADORA SUDESTE SA - NTS                 
DEBN NTSD25_092029   DEBN NTSD25 H924761                    4.940.722,51       0,09 10403 - Títulos Privados-Debêntures simples                  NTSD - NOVA TRANSPORTADORA SUDESTE SA - NTS                 
DEBN BRKPA0_042027   DEBN BRKPA0 H752145                       87.829,12       0,00 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN NTSD25_092029   DEBN NTSD25 H924761                      243.056,88       0,00 10403 - Títulos Privados-Debêntures simples                  NTSD - NOVA TRANSPORTADORA SUDESTE SA - NTS                 
DEBN NTSD25_092029   DEBN NTSD25 H924761                      125.830,33       0,00 10403 - Títulos Privados-Debêntures simples                  NTSD - NOVA TRANSPORTADORA SUDESTE SA - NTS                 
DEBN NTSD25_092029   DEBN NTSD25 H924761                       98.943,51       0,00 10403 - Títulos Privados-Debêntures simples                  NTSD - NOVA TRANSPORTADORA SUDESTE SA - NTS                 
DEBN NTSD25_092029   DEBN NTSD25 H924761                       35.490,61       0,00 10403 - Títulos Privados-Debêntures simples                  NTSD - NOVA TRANSPORTADORA SUDESTE SA - NTS                 
DEBN NTSD25_092029   DEBN NTSD25 H924761                      223.698,36       0,00 10403 - Títulos Privados-Debêntures simples                  NTSD - NOVA TRANSPORTADORA SUDESTE SA - NTS                 
DEBN NTSD25_092029   DEBN NTSD25 H924761                       34.415,13       0,00 10403 - Títulos Privados-Debêntures simples                  NTSD - NOVA TRANSPORTADORA SUDESTE SA - NTS                 
DEBN NTSD25_092029   DEBN NTSD25 H924761                      191.434,18       0,00 10403 - Títulos Privados-Debêntures simples                  NTSD - NOVA TRANSPORTADORA SUDESTE SA - NTS                 
DEBN NTSD25_092029   DEBN NTSD25 H924761                       45.169,86       0,00 10403 - Títulos Privados-Debêntures simples                  NTSD - NOVA TRANSPORTADORA SUDESTE SA - NTS                 
DEBN NTSD25_092029   DEBN NTSD25 H924761                      102.169,93       0,00 10403 - Títulos Privados-Debêntures simples                  NTSD - NOVA TRANSPORTADORA SUDESTE SA - NTS                 
DEBN NTSD25_092029   DEBN NTSD25 H924761                      139.811,47       0,00 10403 - Títulos Privados-Debêntures simples                  NTSD - NOVA TRANSPORTADORA SUDESTE SA - NTS                 
DEBN BRKPA0_042027   DEBN BRKPA0 H752145                       70.054,18       0,00 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN NTSD25_092029   DEBN NTSD25 H924761                      111.849,18       0,00 10403 - Títulos Privados-Debêntures simples                  NTSD - NOVA TRANSPORTADORA SUDESTE SA - NTS                 
DEBN NTSD25_092029   DEBN NTSD25 H924761                       75.283,10       0,00 10403 - Títulos Privados-Debêntures simples                  NTSD - NOVA TRANSPORTADORA SUDESTE SA - NTS                 
DEBN NTSD25_092029   DEBN NTSD25 H924761                      126.905,80       0,00 10403 - Títulos Privados-Debêntures simples                  NTSD - NOVA TRANSPORTADORA SUDESTE SA - NTS                 
DEBN NTSD35_092032   DEBN NTSD35 H924755                      130.314,12       0,00 10403 - Títulos Privados-Debêntures simples                  NTSD - NOVA TRANSPORTADORA SUDESTE SA - NTS                 
DEBN NTSD35_092032   DEBN NTSD35 H924755                       23.890,92       0,00 10403 - Títulos Privados-Debêntures simples                  NTSD - NOVA TRANSPORTADORA SUDESTE SA - NTS                 
DEBN NTSD35_092032   DEBN NTSD35 H924755                      180.267,86       0,00 10403 - Títulos Privados-Debêntures simples                  NTSD - NOVA TRANSPORTADORA SUDESTE SA - NTS                 
DEBN NTSD35_092032   DEBN NTSD35 H924755                       32.578,53       0,00 10403 - Títulos Privados-Debêntures simples                  NTSD - NOVA TRANSPORTADORA SUDESTE SA - NTS                 
DEBN NTSD35_092032   DEBN NTSD35 H924755                       96.649,64       0,00 10403 - Títulos Privados-Debêntures simples                  NTSD - NOVA TRANSPORTADORA SUDESTE SA - NTS                 
DEBN NTSD35_092032   DEBN NTSD35 H924755                      162.892,65       0,00 10403 - Títulos Privados-Debêntures simples                  NTSD - NOVA TRANSPORTADORA SUDESTE SA - NTS                 
DEBN NTSD35_092032   DEBN NTSD35 H924755                      106.423,19       0,00 10403 - Títulos Privados-Debêntures simples                  NTSD - NOVA TRANSPORTADORA SUDESTE SA - NTS                 
DEBN BRKPA0_042027   DEBN BRKPA0 H752145                      101.421,72       0,00 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN NTSD35_092032   DEBN NTSD35 H924755                    1.605.035,52       0,03 10403 - Títulos Privados-Debêntures simples                  NTSD - NOVA TRANSPORTADORA SUDESTE SA - NTS                 
DEBN NTSD35_092032   DEBN NTSD35 H924755                    4.150.504,58       0,07 10403 - Títulos Privados-Debêntures simples                  NTSD - NOVA TRANSPORTADORA SUDESTE SA - NTS                 
DEBN NTSD35_092032   DEBN NTSD35 H924755                    5.547.037,51       0,10 10403 - Títulos Privados-Debêntures simples                  NTSD - NOVA TRANSPORTADORA SUDESTE SA - NTS                 
DEBN NTSD35_092032   DEBN NTSD35 H924755                    1.918.875,35       0,03 10403 - Títulos Privados-Debêntures simples                  NTSD - NOVA TRANSPORTADORA SUDESTE SA - NTS                 
DEBN NTSD35_092032   DEBN NTSD35 H924755                       98.821,54       0,00 10403 - Títulos Privados-Debêntures simples                  NTSD - NOVA TRANSPORTADORA SUDESTE SA - NTS                 
DEBN NTSD35_092032   DEBN NTSD35 H924755                       22.804,97       0,00 10403 - Títulos Privados-Debêntures simples                  NTSD - NOVA TRANSPORTADORA SUDESTE SA - NTS                 
DEBN NTSD35_092032   DEBN NTSD35 H924755                    2.123.034,13       0,04 10403 - Títulos Privados-Debêntures simples                  NTSD - NOVA TRANSPORTADORA SUDESTE SA - NTS                 
DEBN NTSD35_092032   DEBN NTSD35 H924755                      731.930,95       0,01 10403 - Títulos Privados-Debêntures simples                  NTSD - NOVA TRANSPORTADORA SUDESTE SA - NTS                 
DEBN NTSD35_092032   DEBN NTSD35 H924755                      309.496,02       0,01 10403 - Títulos Privados-Debêntures simples                  NTSD - NOVA TRANSPORTADORA SUDESTE SA - NTS                 
DEBN NTSD35_092032   DEBN NTSD35 H924755                    2.672.525,32       0,05 10403 - Títulos Privados-Debêntures simples                  NTSD - NOVA TRANSPORTADORA SUDESTE SA - NTS                 
DEBN BRKPA0_042027   DEBN BRKPA0 H752145                      559.387,85       0,01 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN NTSD35_092032   DEBN NTSD35 H924755                   26.675.299,42       0,48 10403 - Títulos Privados-Debêntures simples                  NTSD - NOVA TRANSPORTADORA SUDESTE SA - NTS                 
DEBN NTSD35_092032   DEBN NTSD35 H924755                      148.775,28       0,00 10403 - Títulos Privados-Debêntures simples                  NTSD - NOVA TRANSPORTADORA SUDESTE SA - NTS                 
DEBN NTSD35_092032   DEBN NTSD35 H924755                      104.251,29       0,00 10403 - Títulos Privados-Debêntures simples                  NTSD - NOVA TRANSPORTADORA SUDESTE SA - NTS                 
DEBN NTSD35_092032   DEBN NTSD35 H924755                      612.476,34       0,01 10403 - Títulos Privados-Debêntures simples                  NTSD - NOVA TRANSPORTADORA SUDESTE SA - NTS                 
DEBN NTSD35_092032   DEBN NTSD35 H924755                      224.791,85       0,00 10403 - Títulos Privados-Debêntures simples                  NTSD - NOVA TRANSPORTADORA SUDESTE SA - NTS                 
DEBN NTSD35_092032   DEBN NTSD35 H924755                      118.368,65       0,00 10403 - Títulos Privados-Debêntures simples                  NTSD - NOVA TRANSPORTADORA SUDESTE SA - NTS                 
DEBN NTSD35_092032   DEBN NTSD35 H924755                      119.454,61       0,00 10403 - Títulos Privados-Debêntures simples                  NTSD - NOVA TRANSPORTADORA SUDESTE SA - NTS                 
DEBN NTSD35_092032   DEBN NTSD35 H924755                       43.438,04       0,00 10403 - Títulos Privados-Debêntures simples                  NTSD - NOVA TRANSPORTADORA SUDESTE SA - NTS                 
DEBN NTSD35_092032   DEBN NTSD35 H924755                       93.391,78       0,00 10403 - Títulos Privados-Debêntures simples                  NTSD - NOVA TRANSPORTADORA SUDESTE SA - NTS                 
DEBN NTSD35_092032   DEBN NTSD35 H924755                      103.165,34       0,00 10403 - Títulos Privados-Debêntures simples                  NTSD - NOVA TRANSPORTADORA SUDESTE SA - NTS                 
DEBN BRKPA0_042027   DEBN BRKPA0 H752145                    4.915.293,97       0,09 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN NTSD35_092032   DEBN NTSD35 H924755                      130.314,12       0,00 10403 - Títulos Privados-Debêntures simples                  NTSD - NOVA TRANSPORTADORA SUDESTE SA - NTS                 
DEBN NTSD35_092032   DEBN NTSD35 H924755                       34.750,43       0,00 10403 - Títulos Privados-Debêntures simples                  NTSD - NOVA TRANSPORTADORA SUDESTE SA - NTS                 
DEBN NTSD35_092032   DEBN NTSD35 H924755                       92.305,83       0,00 10403 - Títulos Privados-Debêntures simples                  NTSD - NOVA TRANSPORTADORA SUDESTE SA - NTS                 
DEBN NTSD35_092032   DEBN NTSD35 H924755                       69.500,86       0,00 10403 - Títulos Privados-Debêntures simples                  NTSD - NOVA TRANSPORTADORA SUDESTE SA - NTS                 
DEBN NTSD35_092032   DEBN NTSD35 H924755                      217.190,20       0,00 10403 - Títulos Privados-Debêntures simples                  NTSD - NOVA TRANSPORTADORA SUDESTE SA - NTS                 
DEBN NTSD35_092032   DEBN NTSD35 H924755                       70.586,81       0,00 10403 - Títulos Privados-Debêntures simples                  NTSD - NOVA TRANSPORTADORA SUDESTE SA - NTS                 
DEBN NTSD35_092032   DEBN NTSD35 H924755                        6.515,71       0,00 10403 - Títulos Privados-Debêntures simples                  NTSD - NOVA TRANSPORTADORA SUDESTE SA - NTS                 
DEBN NTSD35_092032   DEBN NTSD35 H924755                       56.469,45       0,00 10403 - Títulos Privados-Debêntures simples                  NTSD - NOVA TRANSPORTADORA SUDESTE SA - NTS                 
DEBN NTSD35_092032   DEBN NTSD35 H924755                       93.391,78       0,00 10403 - Títulos Privados-Debêntures simples                  NTSD - NOVA TRANSPORTADORA SUDESTE SA - NTS                 
DEBN NTSD35_092032   DEBN NTSD35 H924755                       32.578,53       0,00 10403 - Títulos Privados-Debêntures simples                  NTSD - NOVA TRANSPORTADORA SUDESTE SA - NTS                 
DEBN BRKPA0_042027   DEBN BRKPA0 H752145                      222.709,55       0,00 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN OMGE13_032029   DEBN OMGE13 H774669                    6.474.468,11       0,12 10403 - Títulos Privados-Debêntures simples                  OMGE - SERENA GERACAO S.A                                   
DEBN OMGE13_032029   DEBN OMGE13 H774669                       93.008,40       0,00 10403 - Títulos Privados-Debêntures simples                  OMGE - SERENA GERACAO S.A                                   
DEBN OMGE13_032029   DEBN OMGE13 H774669                    1.949.564,38       0,03 10403 - Títulos Privados-Debêntures simples                  OMGE - SERENA GERACAO S.A                                   
DEBN OMGE13_032029   DEBN OMGE13 H774669                       25.283,84       0,00 10403 - Títulos Privados-Debêntures simples                  OMGE - SERENA GERACAO S.A                                   
DEBN OMGE13_032029   DEBN OMGE13 H774669                      107.456,30       0,00 10403 - Títulos Privados-Debêntures simples                  OMGE - SERENA GERACAO S.A                                   
DEBN OMGE13_032029   DEBN OMGE13 H774669                       46.955,70       0,00 10403 - Títulos Privados-Debêntures simples                  OMGE - SERENA GERACAO S.A                                   
DEBN OMGE13_032029   DEBN OMGE13 H774669                      763.933,06       0,01 10403 - Títulos Privados-Debêntures simples                  OMGE - SERENA GERACAO S.A                                   
DEBN OMGE13_032029   DEBN OMGE13 H774669                    2.955.499,88       0,05 10403 - Títulos Privados-Debêntures simples                  OMGE - SERENA GERACAO S.A                                   
DEBN OMGE13_032029   DEBN OMGE13 H774669                   10.911.781,39       0,20 10403 - Títulos Privados-Debêntures simples                  OMGE - SERENA GERACAO S.A                                   
DEBN OMGE13_032029   DEBN OMGE13 H774669                    2.508.517,77       0,04 10403 - Títulos Privados-Debêntures simples                  OMGE - SERENA GERACAO S.A                                   
DEBN AEGPA0_052029   DEBN AEGPA0 H750651                       20.670,32       0,00 10440 - Títulos Privados-Debêntures Incent. (Lei 12.431)     AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN BRKPA0_042027   DEBN BRKPA0 H752145                      353.407,65       0,01 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN OMGE13_032029   DEBN OMGE13 H774669                    2.203.305,74       0,04 10403 - Títulos Privados-Debêntures simples                  OMGE - SERENA GERACAO S.A                                   
DEBN OMGE13_032029   DEBN OMGE13 H774669                       51.470,67       0,00 10403 - Títulos Privados-Debêntures simples                  OMGE - SERENA GERACAO S.A                                   
DEBN OMGE13_032029   DEBN OMGE13 H774669                      283.540,17       0,01 10403 - Títulos Privados-Debêntures simples                  OMGE - SERENA GERACAO S.A                                   
DEBN OMGE15_062029   DEBN OMGE15 I844374                      152.861,26       0,00 10403 - Títulos Privados-Debêntures simples                  OMGE - SERENA GERACAO S.A                                   
DEBN OMGE15_062029   DEBN OMGE15 I844374                       61.144,50       0,00 10403 - Títulos Privados-Debêntures simples                  OMGE - SERENA GERACAO S.A                                   
DEBN OMGE21_052026   DEBN OMGE21 I249209                    1.497.444,61       0,03 10403 - Títulos Privados-Debêntures simples                  OMGE - SERENA GERACAO S.A                                   
DEBN OMGE21_052026   DEBN OMGE21 I249209                      601.246,70       0,01 10403 - Títulos Privados-Debêntures simples                  OMGE - SERENA GERACAO S.A                                   
DEBN OMGE21_052026   DEBN OMGE21 I249209                      390.861,92       0,01 10403 - Títulos Privados-Debêntures simples                  OMGE - SERENA GERACAO S.A                                   
DEBN OMGE21_052026   DEBN OMGE21 I249209                       33.001,53       0,00 10403 - Títulos Privados-Debêntures simples                  OMGE - SERENA GERACAO S.A                                   
DEBN OMGE21_052026   DEBN OMGE21 I249209                       11.344,28       0,00 10403 - Títulos Privados-Debêntures simples                  OMGE - SERENA GERACAO S.A                                   
DEBN BRKPA0_042027   DEBN BRKPA0 H752145                       54.370,41       0,00 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN OMGE21_052026   DEBN OMGE21 I249209                       19.594,66       0,00 10403 - Títulos Privados-Debêntures simples                  OMGE - SERENA GERACAO S.A                                   
DEBN OMGE21_052026   DEBN OMGE21 I249209                       24.751,15       0,00 10403 - Títulos Privados-Debêntures simples                  OMGE - SERENA GERACAO S.A                                   
DEBN OMGE21_052026   DEBN OMGE21 I249209                      123.755,76       0,00 10403 - Títulos Privados-Debêntures simples                  OMGE - SERENA GERACAO S.A                                   
DEBN OMGE21_052026   DEBN OMGE21 I249209                       49.502,30       0,00 10403 - Títulos Privados-Debêntures simples                  OMGE - SERENA GERACAO S.A                                   
DEBN OMGE21_052026   DEBN OMGE21 I249209                        6.187,79       0,00 10403 - Títulos Privados-Debêntures simples                  OMGE - SERENA GERACAO S.A                                   
DEBN OMGE21_052026   DEBN OMGE21 I249209                       22.688,56       0,00 10403 - Títulos Privados-Debêntures simples                  OMGE - SERENA GERACAO S.A                                   
DEBN OMGE21_052026   DEBN OMGE21 I249209                       56.721,39       0,00 10403 - Títulos Privados-Debêntures simples                  OMGE - SERENA GERACAO S.A                                   
DEBN OMGE21_052026   DEBN OMGE21 I249209                       59.815,28       0,00 10403 - Títulos Privados-Debêntures simples                  OMGE - SERENA GERACAO S.A                                   
DEBN OMGE21_052026   DEBN OMGE21 I249209                       33.001,53       0,00 10403 - Títulos Privados-Debêntures simples                  OMGE - SERENA GERACAO S.A                                   
DEBN OMGE21_052026   DEBN OMGE21 I249209                        2.062,60       0,00 10403 - Títulos Privados-Debêntures simples                  OMGE - SERENA GERACAO S.A                                   
DEBN BRKPA0_042027   DEBN BRKPA0 H752145                      235.256,57       0,00 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN OMGE21_052026   DEBN OMGE21 I249209                      259.887,08       0,00 10403 - Títulos Privados-Debêntures simples                  OMGE - SERENA GERACAO S.A                                   
DEBN OMGE21_052026   DEBN OMGE21 I249209                       22.688,55       0,00 10403 - Títulos Privados-Debêntures simples                  OMGE - SERENA GERACAO S.A                                   
DEBN OMGE21_052026   DEBN OMGE21 I249209                       15.469,47       0,00 10403 - Títulos Privados-Debêntures simples                  OMGE - SERENA GERACAO S.A                                   
DEBN OMGE21_052026   DEBN OMGE21 I249209                      616.716,17       0,01 10403 - Títulos Privados-Debêntures simples                  OMGE - SERENA GERACAO S.A                                   
DEBN OMGE21_052026   DEBN OMGE21 I249209                       11.344,27       0,00 10403 - Títulos Privados-Debêntures simples                  OMGE - SERENA GERACAO S.A                                   
DEBN OMGE21_052026   DEBN OMGE21 I249209                    2.817.505,98       0,05 10403 - Títulos Privados-Debêntures simples                  OMGE - SERENA GERACAO S.A                                   
DEBN OMGE21_052026   DEBN OMGE21 I249209                       10.312,98       0,00 10403 - Títulos Privados-Debêntures simples                  OMGE - SERENA GERACAO S.A                                   
DEBN OMGE21_052026   DEBN OMGE21 I249209                      117.567,96       0,00 10403 - Títulos Privados-Debêntures simples                  OMGE - SERENA GERACAO S.A                                   
DEBN OMGE21_052026   DEBN OMGE21 I249209                       13.406,87       0,00 10403 - Títulos Privados-Debêntures simples                  OMGE - SERENA GERACAO S.A                                   
DEBN OMGE21_052026   DEBN OMGE21 I249209                      864.227,68       0,02 10403 - Títulos Privados-Debêntures simples                  OMGE - SERENA GERACAO S.A                                   
DEBN BRKPA0_042027   DEBN BRKPA0 H752145                       93.057,04       0,00 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN PSAN11_092025   DEBN PSAN11 I504450                      358.170,74       0,01 10403 - Títulos Privados-Debêntures simples                  PSAN - PARSAN S.A.                                          
DEBN PSAN11_092025   DEBN PSAN11 I504450                      172.727,31       0,00 10403 - Títulos Privados-Debêntures simples                  PSAN - PARSAN S.A.                                          
DEBN PSAN11_092025   DEBN PSAN11 I504450                      329.559,47       0,01 10403 - Títulos Privados-Debêntures simples                  PSAN - PARSAN S.A.                                          
DEBN PSAN11_092025   DEBN PSAN11 I504450                      486.391,63       0,01 10403 - Títulos Privados-Debêntures simples                  PSAN - PARSAN S.A.                                          
DEBN PSAN11_092025   DEBN PSAN11 I504450                      349.693,32       0,01 10403 - Títulos Privados-Debêntures simples                  PSAN - PARSAN S.A.                                          
DEBN PSAN11_092025   DEBN PSAN11 I504450                      253.262,74       0,00 10403 - Títulos Privados-Debêntures simples                  PSAN - PARSAN S.A.                                          
DEBN PSAN11_092025   DEBN PSAN11 I504450                      154.712,80       0,00 10403 - Títulos Privados-Debêntures simples                  PSAN - PARSAN S.A.                                          
DEBN PSAN11_092025   DEBN PSAN11 I504450                    5.625.823,80       0,10 10403 - Títulos Privados-Debêntures simples                  PSAN - PARSAN S.A.                                          
DEBN PSAN11_092025   DEBN PSAN11 I504450                      122.922,50       0,00 10403 - Títulos Privados-Debêntures simples                  PSAN - PARSAN S.A.                                          
DEBN PSAN11_092025   DEBN PSAN11 I504450                      223.591,79       0,00 10403 - Títulos Privados-Debêntures simples                  PSAN - PARSAN S.A.                                          
DEBN BRKPA0_042027   DEBN BRKPA0 H752145                      278.125,55       0,00 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN PSAN11_092025   DEBN PSAN11 I504450                    6.013.665,49       0,11 10403 - Títulos Privados-Debêntures simples                  PSAN - PARSAN S.A.                                          
DEBN PSAN11_092025   DEBN PSAN11 I504450                   13.520.415,51       0,24 10403 - Títulos Privados-Debêntures simples                  PSAN - PARSAN S.A.                                          
DEBN PSAN11_092025   DEBN PSAN11 I504450                    3.424.875,22       0,06 10403 - Títulos Privados-Debêntures simples                  PSAN - PARSAN S.A.                                          
DEBN PSAN11_092025   DEBN PSAN11 I504450                      235.248,24       0,00 10403 - Títulos Privados-Debêntures simples                  PSAN - PARSAN S.A.                                          
DEBN PSAN11_092025   DEBN PSAN11 I504450                      583.881,89       0,01 10403 - Títulos Privados-Debêntures simples                  PSAN - PARSAN S.A.                                          
DEBN PSAN11_092025   DEBN PSAN11 I504450                      222.532,11       0,00 10403 - Títulos Privados-Debêntures simples                  PSAN - PARSAN S.A.                                          
DEBN PSAN11_092025   DEBN PSAN11 I504450                      660.178,61       0,01 10403 - Títulos Privados-Debêntures simples                  PSAN - PARSAN S.A.                                          
DEBN PSAN11_092025   DEBN PSAN11 I504450                      327.440,11       0,01 10403 - Títulos Privados-Debêntures simples                  PSAN - PARSAN S.A.                                          
DEBN PSAN11_092025   DEBN PSAN11 I504450                      231.009,53       0,00 10403 - Títulos Privados-Debêntures simples                  PSAN - PARSAN S.A.                                          
DEBN PSAN11_092025   DEBN PSAN11 I504450                      434.467,46       0,01 10403 - Títulos Privados-Debêntures simples                  PSAN - PARSAN S.A.                                          
DEBN BRKPA0_042027   DEBN BRKPA0 H752145                      288.581,39       0,01 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN PSAN11_092025   DEBN PSAN11 I504450                      271.277,24       0,00 10403 - Títulos Privados-Debêntures simples                  PSAN - PARSAN S.A.                                          
DEBN PSAN11_092025   DEBN PSAN11 I504450                      209.815,99       0,00 10403 - Títulos Privados-Debêntures simples                  PSAN - PARSAN S.A.                                          
DEBN PSAN11_092025   DEBN PSAN11 I504450                    2.041.997,07       0,04 10403 - Títulos Privados-Debêntures simples                  PSAN - PARSAN S.A.                                          
DEBN PSAN11_092025   DEBN PSAN11 I504450                  158.023.233,87       2,82 10403 - Títulos Privados-Debêntures simples                  PSAN - PARSAN S.A.                                          
DEBN RBRA26_122027   DEBN RBRA26 I576091                      209.533,51       0,00 10403 - Títulos Privados-Debêntures simples                  RBRA - OPEA SECURITIZADORA S.A.                             
DEBN RBRA26_122027   DEBN RBRA26 I576091                   47.572.489,00       0,85 10403 - Títulos Privados-Debêntures simples                  RBRA - OPEA SECURITIZADORA S.A.                             
DEBN RBRA26_122027   DEBN RBRA26 I576091                      274.189,57       0,00 10403 - Títulos Privados-Debêntures simples                  RBRA - OPEA SECURITIZADORA S.A.                             
DEBN RBRA26_122027   DEBN RBRA26 I576091                      372.370,99       0,01 10403 - Títulos Privados-Debêntures simples                  RBRA - OPEA SECURITIZADORA S.A.                             
DEBN RBRA26_122027   DEBN RBRA26 I576091                      366.384,32       0,01 10403 - Títulos Privados-Debêntures simples                  RBRA - OPEA SECURITIZADORA S.A.                             
DEBN RBRA26_122027   DEBN RBRA26 I576091                   15.828.760,31       0,28 10403 - Títulos Privados-Debêntures simples                  RBRA - OPEA SECURITIZADORA S.A.                             
DEBN BRKPA0_042027   DEBN BRKPA0 H752145                      159.974,47       0,00 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN RBRA26_122027   DEBN RBRA26 I576091                   10.823.902,66       0,19 10403 - Títulos Privados-Debêntures simples                  RBRA - OPEA SECURITIZADORA S.A.                             
DEBN RBRA26_122027   DEBN RBRA26 I576091                      632.192,54       0,01 10403 - Títulos Privados-Debêntures simples                  RBRA - OPEA SECURITIZADORA S.A.                             
DEBN RBRA26_122027   DEBN RBRA26 I576091                      416.672,36       0,01 10403 - Títulos Privados-Debêntures simples                  RBRA - OPEA SECURITIZADORA S.A.                             
DEBN RBRA26_122027   DEBN RBRA26 I576091                      378.357,66       0,01 10403 - Títulos Privados-Debêntures simples                  RBRA - OPEA SECURITIZADORA S.A.                             
DEBN RBRA26_122027   DEBN RBRA26 I576091                   61.563.341,06       1,10 10403 - Títulos Privados-Debêntures simples                  RBRA - OPEA SECURITIZADORA S.A.                             
DEBN RBRA26_122027   DEBN RBRA26 I576091                      539.997,80       0,01 10403 - Títulos Privados-Debêntures simples                  RBRA - OPEA SECURITIZADORA S.A.                             
DEBN RBRA26_122027   DEBN RBRA26 I576091                      381.949,66       0,01 10403 - Títulos Privados-Debêntures simples                  RBRA - OPEA SECURITIZADORA S.A.                             
DEBN RBRA26_122027   DEBN RBRA26 I576091                      286.162,91       0,01 10403 - Títulos Privados-Debêntures simples                  RBRA - OPEA SECURITIZADORA S.A.                             
DEBN RBRA26_122027   DEBN RBRA26 I576091                      281.373,58       0,01 10403 - Títulos Privados-Debêntures simples                  RBRA - OPEA SECURITIZADORA S.A.                             
DEBN RBRA26_122027   DEBN RBRA26 I576091                      381.949,66       0,01 10403 - Títulos Privados-Debêntures simples                  RBRA - OPEA SECURITIZADORA S.A.                             
DEBN BRKPA0_042027   DEBN BRKPA0 H752145                       53.324,82       0,00 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN RBRA26_122027   DEBN RBRA26 I576091                    3.364.509,57       0,06 10403 - Títulos Privados-Debêntures simples                  RBRA - OPEA SECURITIZADORA S.A.                             
DEBN RBRA26_122027   DEBN RBRA26 I576091                    3.177.725,41       0,06 10403 - Títulos Privados-Debêntures simples                  RBRA - OPEA SECURITIZADORA S.A.                             
DEBN RBRA26_122027   DEBN RBRA26 I576091                    5.684.943,57       0,10 10403 - Títulos Privados-Debêntures simples                  RBRA - OPEA SECURITIZADORA S.A.                             
DEBN RBRA26_122027   DEBN RBRA26 I576091                    8.813.578,26       0,16 10403 - Títulos Privados-Debêntures simples                  RBRA - OPEA SECURITIZADORA S.A.                             
DEBN RBRA26_122027   DEBN RBRA26 I576091                      383.147,00       0,01 10403 - Títulos Privados-Debêntures simples                  RBRA - OPEA SECURITIZADORA S.A.                             
DEBN RBRA26_122027   DEBN RBRA26 I576091                    4.751.022,77       0,08 10403 - Títulos Privados-Debêntures simples                  RBRA - OPEA SECURITIZADORA S.A.                             
DEBN RBRA26_122027   DEBN RBRA26 I576091                      555.563,15       0,01 10403 - Títulos Privados-Debêntures simples                  RBRA - OPEA SECURITIZADORA S.A.                             
DEBN RBRA26_122027   DEBN RBRA26 I576091                      716.005,95       0,01 10403 - Títulos Privados-Debêntures simples                  RBRA - OPEA SECURITIZADORA S.A.                             
DEBN RBRA26_122027   DEBN RBRA26 I576091                      475.341,74       0,01 10403 - Títulos Privados-Debêntures simples                  RBRA - OPEA SECURITIZADORA S.A.                             
DEBN RBRA26_122027   DEBN RBRA26 I576091                      523.235,12       0,01 10403 - Títulos Privados-Debêntures simples                  RBRA - OPEA SECURITIZADORA S.A.                             
DEBN BRKPA0_042027   DEBN BRKPA0 H752145                      571.934,86       0,01 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN RBRA26_122027   DEBN RBRA26 I576091                      750.728,65       0,01 10403 - Títulos Privados-Debêntures simples                  RBRA - OPEA SECURITIZADORA S.A.                             
DEBN RDORB3_052032   DEBN RDORB3 I30424                     1.802.954,00       0,03 10403 - Títulos Privados-Debêntures simples                  RDOR - REDE D OR SAO LUIZ SA                                
DEBN RDORB3_052032   DEBN RDORB3 I30424                     2.405.682,67       0,04 10403 - Títulos Privados-Debêntures simples                  RDOR - REDE D OR SAO LUIZ SA                                
DEBN RDORB3_052032   DEBN RDORB3 I30424                        16.742,46       0,00 10403 - Títulos Privados-Debêntures simples                  RDOR - REDE D OR SAO LUIZ SA                                
DEBN RDORB3_052032   DEBN RDORB3 I30424                        84.758,72       0,00 10403 - Títulos Privados-Debêntures simples                  RDOR - REDE D OR SAO LUIZ SA                                
DEBN RDORB3_052032   DEBN RDORB3 I30424                       277.297,05       0,00 10403 - Títulos Privados-Debêntures simples                  RDOR - REDE D OR SAO LUIZ SA                                
DEBN RDORB3_052032   DEBN RDORB3 I30424                     1.603.090,84       0,03 10403 - Títulos Privados-Debêntures simples                  RDOR - REDE D OR SAO LUIZ SA                                
DEBN RDORB3_052032   DEBN RDORB3 I30424                     4.922.284,15       0,09 10403 - Títulos Privados-Debêntures simples                  RDOR - REDE D OR SAO LUIZ SA                                
DEBN RDORB3_052032   DEBN RDORB3 I30424                    20.465.568,34       0,37 10403 - Títulos Privados-Debêntures simples                  RDOR - REDE D OR SAO LUIZ SA                                
DEBN RDORB3_052032   DEBN RDORB3 I30424                        19.881,67       0,00 10403 - Títulos Privados-Debêntures simples                  RDOR - REDE D OR SAO LUIZ SA                                
DEBN BRKPA0_042027   DEBN BRKPA0 H752145                      604.347,99       0,01 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN RDORB9_082031   DEBN RDORB9 H917455                   25.154.487,28       0,45 10403 - Títulos Privados-Debêntures simples                  RDOR - REDE D OR SAO LUIZ SA                                
DEBN RDORB9_082031   DEBN RDORB9 H917455                      832.858,41       0,01 10403 - Títulos Privados-Debêntures simples                  RDOR - REDE D OR SAO LUIZ SA                                
DEBN RDORB9_082031   DEBN RDORB9 H917455                    5.951.151,92       0,11 10403 - Títulos Privados-Debêntures simples                  RDOR - REDE D OR SAO LUIZ SA                                
DEBN RDORB9_082031   DEBN RDORB9 H917455                    3.794.373,12       0,07 10403 - Títulos Privados-Debêntures simples                  RDOR - REDE D OR SAO LUIZ SA                                
DEBN RDORB9_082031   DEBN RDORB9 H917455                      131.959,38       0,00 10403 - Títulos Privados-Debêntures simples                  RDOR - REDE D OR SAO LUIZ SA                                
DEBN RDORB9_082031   DEBN RDORB9 H917455                      163.326,78       0,00 10403 - Títulos Privados-Debêntures simples                  RDOR - REDE D OR SAO LUIZ SA                                
DEBN RDORB9_082031   DEBN RDORB9 H917455                       73.551,13       0,00 10403 - Títulos Privados-Debêntures simples                  RDOR - REDE D OR SAO LUIZ SA                                
DEBN RDORB9_082031   DEBN RDORB9 H917455                      164.408,41       0,00 10403 - Títulos Privados-Debêntures simples                  RDOR - REDE D OR SAO LUIZ SA                                
DEBN RDORB9_082031   DEBN RDORB9 H917455                    9.132.238,39       0,16 10403 - Títulos Privados-Debêntures simples                  RDOR - REDE D OR SAO LUIZ SA                                
DEBN RDORB9_082031   DEBN RDORB9 H917455                      442.388,43       0,01 10403 - Títulos Privados-Debêntures simples                  RDOR - REDE D OR SAO LUIZ SA                                
DEBN AEGPA0_052029   DEBN AEGPA0 H750651                        3.100,55       0,00 10440 - Títulos Privados-Debêntures Incent. (Lei 12.431)     AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN BRKPA0_042027   DEBN BRKPA0 H752145                       10.455,85       0,00 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN RDORB9_082031   DEBN RDORB9 H917455                       32.449,03       0,00 10403 - Títulos Privados-Debêntures simples                  RDOR - REDE D OR SAO LUIZ SA                                
DEBN RDORB9_082031   DEBN RDORB9 H917455                      108.163,43       0,00 10403 - Títulos Privados-Debêntures simples                  RDOR - REDE D OR SAO LUIZ SA                                
DEBN RDORC1_102031   DEBN RDORC1 I646266                      676.934,57       0,01 10403 - Títulos Privados-Debêntures simples                  RDOR - REDE D OR SAO LUIZ SA                                
DEBN RDORC1_102031   DEBN RDORC1 I646266                       10.660,39       0,00 10403 - Títulos Privados-Debêntures simples                  RDOR - REDE D OR SAO LUIZ SA                                
DEBN RDORC1_102031   DEBN RDORC1 I646266                      313.415,38       0,01 10403 - Títulos Privados-Debêntures simples                  RDOR - REDE D OR SAO LUIZ SA                                
DEBN RDORC1_102031   DEBN RDORC1 I646266                    2.633.115,58       0,05 10403 - Títulos Privados-Debêntures simples                  RDOR - REDE D OR SAO LUIZ SA                                
DEBN RDORC1_102031   DEBN RDORC1 I646266                       35.179,28       0,00 10403 - Títulos Privados-Debêntures simples                  RDOR - REDE D OR SAO LUIZ SA                                
DEBN RDORC1_102031   DEBN RDORC1 I646266                    2.547.832,48       0,05 10403 - Títulos Privados-Debêntures simples                  RDOR - REDE D OR SAO LUIZ SA                                
DEBN RDORC1_102031   DEBN RDORC1 I646266                    1.125.736,86       0,02 10403 - Títulos Privados-Debêntures simples                  RDOR - REDE D OR SAO LUIZ SA                                
DEBN RDORC1_102031   DEBN RDORC1 I646266                   13.788.144,49       0,25 10403 - Títulos Privados-Debêntures simples                  RDOR - REDE D OR SAO LUIZ SA                                
DEBN BRKPA0_042027   DEBN BRKPA0 H752145                       19.866,11       0,00 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN RDORC3_052032   DEBN RDORC3 H919413                       29.312,20       0,00 10403 - Títulos Privados-Debêntures simples                  RDOR - REDE D OR SAO LUIZ SA                                
DEBN RDORC3_052032   DEBN RDORC3 H919413                       36.640,25       0,00 10403 - Títulos Privados-Debêntures simples                  RDOR - REDE D OR SAO LUIZ SA                                
DEBN RDORC3_052032   DEBN RDORC3 H919413                      557.978,61       0,01 10403 - Títulos Privados-Debêntures simples                  RDOR - REDE D OR SAO LUIZ SA                                
DEBN RDORC3_052032   DEBN RDORC3 H919413                       54.436,94       0,00 10403 - Títulos Privados-Debêntures simples                  RDOR - REDE D OR SAO LUIZ SA                                
DEBN RDORC3_052032   DEBN RDORC3 H919413                      107.827,01       0,00 10403 - Títulos Privados-Debêntures simples                  RDOR - REDE D OR SAO LUIZ SA                                
DEBN RDORC3_052032   DEBN RDORC3 H919413                      147.607,85       0,00 10403 - Títulos Privados-Debêntures simples                  RDOR - REDE D OR SAO LUIZ SA                                
DEBN RDORC3_052032   DEBN RDORC3 H919413                      108.873,88       0,00 10403 - Títulos Privados-Debêntures simples                  RDOR - REDE D OR SAO LUIZ SA                                
DEBN RDORC3_052032   DEBN RDORC3 H919413                       24.077,88       0,00 10403 - Títulos Privados-Debêntures simples                  RDOR - REDE D OR SAO LUIZ SA                                
DEBN RDORC3_052032   DEBN RDORC3 H919413                       36.640,25       0,00 10403 - Títulos Privados-Debêntures simples                  RDOR - REDE D OR SAO LUIZ SA                                
DEBN RDORC3_052032   DEBN RDORC3 H919413                      192.623,01       0,00 10403 - Títulos Privados-Debêntures simples                  RDOR - REDE D OR SAO LUIZ SA                                
DEBN BRKPA0_042027   DEBN BRKPA0 H752145                       41.823,39       0,00 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN RDORC3_052032   DEBN RDORC3 H919413                       24.077,88       0,00 10403 - Títulos Privados-Debêntures simples                  RDOR - REDE D OR SAO LUIZ SA                                
DEBN RDORC3_052032   DEBN RDORC3 H919413                       15.702,96       0,00 10403 - Títulos Privados-Debêntures simples                  RDOR - REDE D OR SAO LUIZ SA                                
DEBN RDORC3_052032   DEBN RDORC3 H919413                    1.476.078,50       0,03 10403 - Títulos Privados-Debêntures simples                  RDOR - REDE D OR SAO LUIZ SA                                
DEBN RDORC3_052032   DEBN RDORC3 H919413                      221.935,21       0,00 10403 - Títulos Privados-Debêntures simples                  RDOR - REDE D OR SAO LUIZ SA                                
DEBN RDORC3_052032   DEBN RDORC3 H919413                    4.140.347,84       0,07 10403 - Títulos Privados-Debêntures simples                  RDOR - REDE D OR SAO LUIZ SA                                
DEBN RDORC3_052032   DEBN RDORC3 H919413                       14.656,10       0,00 10403 - Títulos Privados-Debêntures simples                  RDOR - REDE D OR SAO LUIZ SA                                
DEBN RDORC3_052032   DEBN RDORC3 H919413                    1.613.217,71       0,03 10403 - Títulos Privados-Debêntures simples                  RDOR - REDE D OR SAO LUIZ SA                                
DEBN RDORC3_052032   DEBN RDORC3 H919413                       68.046,17       0,00 10403 - Títulos Privados-Debêntures simples                  RDOR - REDE D OR SAO LUIZ SA                                
DEBN RDORC3_052032   DEBN RDORC3 H919413                    2.522.942,68       0,05 10403 - Títulos Privados-Debêntures simples                  RDOR - REDE D OR SAO LUIZ SA                                
DEBN RDORC3_052032   DEBN RDORC3 H919413                      450.151,60       0,01 10403 - Títulos Privados-Debêntures simples                  RDOR - REDE D OR SAO LUIZ SA                                
DEBN BRKPA0_042027   DEBN BRKPA0 H752145                       62.735,09       0,00 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN RDORC3_052032   DEBN RDORC3 H919413                      163.310,81       0,00 10403 - Títulos Privados-Debêntures simples                  RDOR - REDE D OR SAO LUIZ SA                                
DEBN RDORC3_052032   DEBN RDORC3 H919413                       63.858,72       0,00 10403 - Títulos Privados-Debêntures simples                  RDOR - REDE D OR SAO LUIZ SA                                
DEBN RDORC3_052032   DEBN RDORC3 H919413                       31.405,93       0,00 10403 - Títulos Privados-Debêntures simples                  RDOR - REDE D OR SAO LUIZ SA                                
DEBN RDORC3_052032   DEBN RDORC3 H919413                       49.202,62       0,00 10403 - Títulos Privados-Debêntures simples                  RDOR - REDE D OR SAO LUIZ SA                                
DEBN RDORC3_052032   DEBN RDORC3 H919413                       18.843,56       0,00 10403 - Títulos Privados-Debêntures simples                  RDOR - REDE D OR SAO LUIZ SA                                
DEBN RDORC3_052032   DEBN RDORC3 H919413                      247.059,95       0,00 10403 - Títulos Privados-Debêntures simples                  RDOR - REDE D OR SAO LUIZ SA                                
DEBN RDORC3_052032   DEBN RDORC3 H919413                      157.029,63       0,00 10403 - Títulos Privados-Debêntures simples                  RDOR - REDE D OR SAO LUIZ SA                                
DEBN RDORC3_052032   DEBN RDORC3 H919413                      163.310,81       0,00 10403 - Títulos Privados-Debêntures simples                  RDOR - REDE D OR SAO LUIZ SA                                
DEBN RDORC3_052032   DEBN RDORC3 H919413                       99.452,10       0,00 10403 - Títulos Privados-Debêntures simples                  RDOR - REDE D OR SAO LUIZ SA                                
DEBN RDORC3_052032   DEBN RDORC3 H919413                      185.294,96       0,00 10403 - Títulos Privados-Debêntures simples                  RDOR - REDE D OR SAO LUIZ SA                                
DEBN BRKPA0_042027   DEBN BRKPA0 H752145                       33.458,71       0,00 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN RDORC3_052032   DEBN RDORC3 H919413                       30.359,06       0,00 10403 - Títulos Privados-Debêntures simples                  RDOR - REDE D OR SAO LUIZ SA                                
DEBN RDORC3_052032   DEBN RDORC3 H919413                      212.513,43       0,00 10403 - Títulos Privados-Debêntures simples                  RDOR - REDE D OR SAO LUIZ SA                                
DEBN RDORC3_052032   DEBN RDORC3 H919413                       88.983,46       0,00 10403 - Títulos Privados-Debêntures simples                  RDOR - REDE D OR SAO LUIZ SA                                
DEBN RDORC3_052032   DEBN RDORC3 H919413                      154.935,90       0,00 10403 - Títulos Privados-Debêntures simples                  RDOR - REDE D OR SAO LUIZ SA                                
DEBN RDORC3_052032   DEBN RDORC3 H919413                      269.044,10       0,00 10403 - Títulos Privados-Debêntures simples                  RDOR - REDE D OR SAO LUIZ SA                                
DEBN RDORC3_052032   DEBN RDORC3 H919413                      160.170,22       0,00 10403 - Títulos Privados-Debêntures simples                  RDOR - REDE D OR SAO LUIZ SA                                
DEBN RDORC3_052032   DEBN RDORC3 H919413                      435.495,50       0,01 10403 - Títulos Privados-Debêntures simples                  RDOR - REDE D OR SAO LUIZ SA                                
DEBN RDORC3_052032   DEBN RDORC3 H919413                      194.716,74       0,00 10403 - Títulos Privados-Debêntures simples                  RDOR - REDE D OR SAO LUIZ SA                                
DEBN RDORC7_062029   DEBN RDORC7                                9.103,23       0,00 10403 - Títulos Privados-Debêntures simples                  RDOR - REDE D OR SAO LUIZ SA                                
DEBN RDORC7_062029   DEBN RDORC7                            2.694.555,45       0,05 10403 - Títulos Privados-Debêntures simples                  RDOR - REDE D OR SAO LUIZ SA                                
DEBN BRKPA0_042027   DEBN BRKPA0 H752145                       15.683,77       0,00 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN RDORC7_062029   DEBN RDORC7                                6.068,82       0,00 10403 - Títulos Privados-Debêntures simples                  RDOR - REDE D OR SAO LUIZ SA                                
DEBN RDORC9_082031   DEBN RDORC9 H647375                    2.287.527,94       0,04 10403 - Títulos Privados-Debêntures simples                  RDOR - REDE D OR SAO LUIZ SA                                
DEBN RDORC9_082031   DEBN RDORC9 H647375                       52.947,03       0,00 10403 - Títulos Privados-Debêntures simples                  RDOR - REDE D OR SAO LUIZ SA                                
DEBN RDORC9_082031   DEBN RDORC9 H647375                      669.942,05       0,01 10403 - Títulos Privados-Debêntures simples                  RDOR - REDE D OR SAO LUIZ SA                                
DEBN RDORC9_082031   DEBN RDORC9 H647375                    6.030.559,03       0,11 10403 - Títulos Privados-Debêntures simples                  RDOR - REDE D OR SAO LUIZ SA                                
DEBN RDORC9_082031   DEBN RDORC9 H647375                    5.724.762,90       0,10 10403 - Títulos Privados-Debêntures simples                  RDOR - REDE D OR SAO LUIZ SA                                
DEBN RDORD9_072031   DEBN RDORD9 I317802                       34.185,02       0,00 10403 - Títulos Privados-Debêntures simples                  RDOR - REDE D OR SAO LUIZ SA                                
DEBN RDORD9_072031   DEBN RDORD9 I317802                      314.916,51       0,01 10403 - Títulos Privados-Debêntures simples                  RDOR - REDE D OR SAO LUIZ SA                                
DEBN RDORD9_072031   DEBN RDORD9 I317802                       53.867,30       0,00 10403 - Títulos Privados-Debêntures simples                  RDOR - REDE D OR SAO LUIZ SA                                
DEBN RDORD9_072031   DEBN RDORD9 I317802                      261.049,21       0,00 10403 - Títulos Privados-Debêntures simples                  RDOR - REDE D OR SAO LUIZ SA                                
DEBN BRKPA0_042027   DEBN BRKPA0 H752145                      121.287,84       0,00 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN RDORD9_072031   DEBN RDORD9 I317802                      709.598,06       0,01 10403 - Títulos Privados-Debêntures simples                  RDOR - REDE D OR SAO LUIZ SA                                
DEBN RDORD9_072031   DEBN RDORD9 I317802                      331.491,07       0,01 10403 - Títulos Privados-Debêntures simples                  RDOR - REDE D OR SAO LUIZ SA                                
DEBN RDORD9_072031   DEBN RDORD9 I317802                      397.789,28       0,01 10403 - Títulos Privados-Debêntures simples                  RDOR - REDE D OR SAO LUIZ SA                                
DEBN RDORD9_072031   DEBN RDORD9 I317802                    6.990.317,85       0,12 10403 - Títulos Privados-Debêntures simples                  RDOR - REDE D OR SAO LUIZ SA                                
DEBN RDORD9_072031   DEBN RDORD9 I317802                      145.027,34       0,00 10403 - Títulos Privados-Debêntures simples                  RDOR - REDE D OR SAO LUIZ SA                                
DEBN RDORD9_072031   DEBN RDORD9 I317802                      109.806,41       0,00 10403 - Títulos Privados-Debêntures simples                  RDOR - REDE D OR SAO LUIZ SA                                
DEBN RDORD9_072031   DEBN RDORD9 I317802                       49.723,66       0,00 10403 - Títulos Privados-Debêntures simples                  RDOR - REDE D OR SAO LUIZ SA                                
DEBN RDORD9_072031   DEBN RDORD9 I317802                      566.642,54       0,01 10403 - Títulos Privados-Debêntures simples                  RDOR - REDE D OR SAO LUIZ SA                                
DEBN RDORD9_072031   DEBN RDORD9 I317802                      349.101,53       0,01 10403 - Títulos Privados-Debêntures simples                  RDOR - REDE D OR SAO LUIZ SA                                
DEBN RDORD9_072031   DEBN RDORD9 I317802                      234.115,57       0,00 10403 - Títulos Privados-Debêntures simples                  RDOR - REDE D OR SAO LUIZ SA                                
DEBN BRKPA0_042027   DEBN BRKPA0 H752145                      157.883,30       0,00 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN RDORD9_072031   DEBN RDORD9 I317802                      189.571,45       0,00 10403 - Títulos Privados-Debêntures simples                  RDOR - REDE D OR SAO LUIZ SA                                
DEBN RDORD9_072031   DEBN RDORD9 I317802                    3.071.471,90       0,05 10403 - Títulos Privados-Debêntures simples                  RDOR - REDE D OR SAO LUIZ SA                                
DEBN RDORD9_072031   DEBN RDORD9 I317802                      117.057,78       0,00 10403 - Títulos Privados-Debêntures simples                  RDOR - REDE D OR SAO LUIZ SA                                
DEBN RDORD9_072031   DEBN RDORD9 I317802                      474.446,59       0,01 10403 - Títulos Privados-Debêntures simples                  RDOR - REDE D OR SAO LUIZ SA                                
DEBN RDORD9_072031   DEBN RDORD9 I317802                       62.154,57       0,00 10403 - Títulos Privados-Debêntures simples                  RDOR - REDE D OR SAO LUIZ SA                                
DEBN RDORD9_072031   DEBN RDORD9 I317802                      229.971,93       0,00 10403 - Títulos Privados-Debêntures simples                  RDOR - REDE D OR SAO LUIZ SA                                
DEBN RDORD9_072031   DEBN RDORD9 I317802                      853.589,49       0,02 10403 - Títulos Privados-Debêntures simples                  RDOR - REDE D OR SAO LUIZ SA                                
DEBN RDORD9_072031   DEBN RDORD9 I317802                       51.795,48       0,00 10403 - Títulos Privados-Debêntures simples                  RDOR - REDE D OR SAO LUIZ SA                                
DEBN RDORD9_072031   DEBN RDORD9 I317802                      297.306,05       0,01 10403 - Títulos Privados-Debêntures simples                  RDOR - REDE D OR SAO LUIZ SA                                
DEBN RDORD9_072031   DEBN RDORD9 I317802                    1.986.874,57       0,04 10403 - Títulos Privados-Debêntures simples                  RDOR - REDE D OR SAO LUIZ SA                                
DEBN BRKPA0_042027   DEBN BRKPA0 H752145                       71.099,76       0,00 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN RDORD9_072031   DEBN RDORD9 I317802                       18.646,37       0,00 10403 - Títulos Privados-Debêntures simples                  RDOR - REDE D OR SAO LUIZ SA                                
DEBN RDORD9_072031   DEBN RDORD9 I317802                       77.693,22       0,00 10403 - Títulos Privados-Debêntures simples                  RDOR - REDE D OR SAO LUIZ SA                                
DEBN RDORD9_072031   DEBN RDORD9 I317802                       78.729,13       0,00 10403 - Títulos Privados-Debêntures simples                  RDOR - REDE D OR SAO LUIZ SA                                
DEBN RENTA5_082033   DEBN RENTA5 I333477                      348.578,53       0,01 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN RENTA5_082033   DEBN RENTA5 I333477                      772.319,32       0,01 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN RENTA5_082033   DEBN RENTA5 I333477                      419.383,55       0,01 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN RENTA5_082033   DEBN RENTA5 I333477                      331.149,61       0,01 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN RENTA5_082033   DEBN RENTA5 I333477                      152.503,11       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN RENTA5_082033   DEBN RENTA5 I333477                      115.466,64       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN RENTA5_082033   DEBN RENTA5 I333477                       52.286,78       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN BRKPA1_032028   DEBN BRKPA1 I128038                       44.582,44       0,00 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN RENTA5_082033   DEBN RENTA5 I333477                      594.762,13       0,01 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN RENTA5_082033   DEBN RENTA5 I333477                      394.329,47       0,01 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN RENTA5_082033   DEBN RENTA5 I333477                      144.877,95       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN RENTA5_082033   DEBN RENTA5 I333477                       81.698,09       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN RENTA5_082033   DEBN RENTA5 I333477                       22.875,47       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN RENTA5_082033   DEBN RENTA5 I333477                      241.826,36       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN RENTA5_082033   DEBN RENTA5 I333477                    2.089.292,59       0,04 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN RENTA5_082033   DEBN RENTA5 I333477                      312.631,37       0,01 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN RENTA5_082033   DEBN RENTA5 I333477                    3.227.619,37       0,06 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN RENTA5_082033   DEBN RENTA5 I333477                      897.589,73       0,02 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN AEGPA0_052029   DEBN AEGPA0 H750651                        4.134,06       0,00 10440 - Títulos Privados-Debêntures Incent. (Lei 12.431)     AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN BRKPA1_032028   DEBN BRKPA1 I128038                       14.135,90       0,00 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN RENTA5_082033   DEBN RENTA5 I333477                       82.787,40       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN RENTA5_082033   DEBN RENTA5 I333477                    4.572.914,65       0,08 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN RENTA5_082033   DEBN RENTA5 I333477                      123.091,79       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN RENTA5_082033   DEBN RENTA5 I333477                      498.903,02       0,01 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN RENTA5_082033   DEBN RENTA5 I333477                       65.358,48       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN RENTA5_082033   DEBN RENTA5 I333477                      246.183,59       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN RENTA5_082033   DEBN RENTA5 I333477                       82.787,40       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN RENTA5_082033   DEBN RENTA5 I333477                       54.465,40       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN RENTA5_082033   DEBN RENTA5 I333477                       35.947,16       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN RENTA5_082033   DEBN RENTA5 I333477                      173.199,96       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN BRKPA1_032028   DEBN BRKPA1 I128038                       11.961,14       0,00 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN RENTA5_082033   DEBN RENTA5 I333477                       41.393,70       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN RENTC4_112028   DEBN RENTC4_112028 J77548              1.975.353,29       0,04 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN RENTC4_112028   DEBN RENTC4_112028 J77548                  3.105,90       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN RENTC8_022029   DEBN RENTC8 I678639                    1.613.113,05       0,03 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN RENTC8_022029   DEBN RENTC8 I678639                       15.971,42       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN RENTC8_022029   DEBN RENTC8 I678639                      144.807,51       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN RENTC8_022029   DEBN RENTC8 I678639                    2.292.430,62       0,04 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN RENTC8_022029   DEBN RENTC8 I678639                      227.858,87       0,00 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN RENTC8_022029   DEBN RENTC8 I678639                    5.226.912,19       0,09 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN RENTC8_022029   DEBN RENTC8 I678639                    5.842.344,10       0,10 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN BRKPA1_032028   DEBN BRKPA1 I128038                      825.318,87       0,01 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN RENTC8_022029   DEBN RENTC8 I678639                      543.028,16       0,01 10403 - Títulos Privados-Debêntures simples                  RENT - LOCALIZA RENT A CAR SA                               
DEBN SAELA4_092029   DEBN SAELA4_092029 I979499                 1.046,95       0,00 10403 - Títulos Privados-Debêntures simples                  SAEL - ENERGISA PARAIBA DISTRIBUIDORA ENERGIA SA            
DEBN SAELA4_092029   DEBN SAELA4_092029 I979499                 3.140,85       0,00 10403 - Títulos Privados-Debêntures simples                  SAEL - ENERGISA PARAIBA DISTRIBUIDORA ENERGIA SA            
DEBN SAELA4_092029   DEBN SAELA4_092029 I979499                 9.422,55       0,00 10403 - Títulos Privados-Debêntures simples                  SAEL - ENERGISA PARAIBA DISTRIBUIDORA ENERGIA SA            
DEBN SAELA4_092029   DEBN SAELA4_092029 I979499                 3.140,85       0,00 10403 - Títulos Privados-Debêntures simples                  SAEL - ENERGISA PARAIBA DISTRIBUIDORA ENERGIA SA            
DEBN SAELA4_092029   DEBN SAELA4_092029 I979499                 9.422,55       0,00 10403 - Títulos Privados-Debêntures simples                  SAEL - ENERGISA PARAIBA DISTRIBUIDORA ENERGIA SA            
DEBN SAELA4_092029   DEBN SAELA4_092029 I979499                 4.187,80       0,00 10403 - Títulos Privados-Debêntures simples                  SAEL - ENERGISA PARAIBA DISTRIBUIDORA ENERGIA SA            
DEBN SAELA4_092029   DEBN SAELA4_092029 I979499             1.324.392,60       0,02 10403 - Títulos Privados-Debêntures simples                  SAEL - ENERGISA PARAIBA DISTRIBUIDORA ENERGIA SA            
DEBN SAELA4_092029   DEBN SAELA4_092029 I979499                 5.234,75       0,00 10403 - Títulos Privados-Debêntures simples                  SAEL - ENERGISA PARAIBA DISTRIBUIDORA ENERGIA SA            
DEBN SAELA4_092029   DEBN SAELA4_092029 I979499                 6.281,70       0,00 10403 - Títulos Privados-Debêntures simples                  SAEL - ENERGISA PARAIBA DISTRIBUIDORA ENERGIA SA            
DEBN BRKPA1_032028   DEBN BRKPA1 I128038                      194.640,42       0,00 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN SAELA4_092029   DEBN SAELA4_092029 I979499                11.516,46       0,00 10403 - Títulos Privados-Debêntures simples                  SAEL - ENERGISA PARAIBA DISTRIBUIDORA ENERGIA SA            
DEBN SAELA4_092029   DEBN SAELA4_092029 I979499                 2.093,90       0,00 10403 - Títulos Privados-Debêntures simples                  SAEL - ENERGISA PARAIBA DISTRIBUIDORA ENERGIA SA            
DEBN SAELA4_092029   DEBN SAELA4_092029 I979499                 2.093,90       0,00 10403 - Títulos Privados-Debêntures simples                  SAEL - ENERGISA PARAIBA DISTRIBUIDORA ENERGIA SA            
DEBN SAELA4_092029   DEBN SAELA4_092029 I979499                 2.093,90       0,00 10403 - Títulos Privados-Debêntures simples                  SAEL - ENERGISA PARAIBA DISTRIBUIDORA ENERGIA SA            
DEBN SAELA4_092029   DEBN SAELA4_092029 I979499                 5.234,75       0,00 10403 - Títulos Privados-Debêntures simples                  SAEL - ENERGISA PARAIBA DISTRIBUIDORA ENERGIA SA            
DEBN SAELA4_092029   DEBN SAELA4_092029 I979499                 4.187,80       0,00 10403 - Títulos Privados-Debêntures simples                  SAEL - ENERGISA PARAIBA DISTRIBUIDORA ENERGIA SA            
DEBN SAELA4_092029   DEBN SAELA4_092029 I979499                 4.187,80       0,00 10403 - Títulos Privados-Debêntures simples                  SAEL - ENERGISA PARAIBA DISTRIBUIDORA ENERGIA SA            
DEBN SAELA4_092029   DEBN SAELA4_092029 I979499                 3.140,85       0,00 10403 - Títulos Privados-Debêntures simples                  SAEL - ENERGISA PARAIBA DISTRIBUIDORA ENERGIA SA            
DEBN SAELA4_092029   DEBN SAELA4_092029 I979499                 4.187,80       0,00 10403 - Títulos Privados-Debêntures simples                  SAEL - ENERGISA PARAIBA DISTRIBUIDORA ENERGIA SA            
DEBN SAELA4_092029   DEBN SAELA4_092029 I979499                 6.281,70       0,00 10403 - Títulos Privados-Debêntures simples                  SAEL - ENERGISA PARAIBA DISTRIBUIDORA ENERGIA SA            
DEBN BRKPA1_032028   DEBN BRKPA1 I128038                     -144.621,09       0,00 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN SAELA4_092029   DEBN SAELA4_092029 I979499                 1.046,95       0,00 10403 - Títulos Privados-Debêntures simples                  SAEL - ENERGISA PARAIBA DISTRIBUIDORA ENERGIA SA            
DEBN SBFC12_052025   DEBN SBFC12 I168246                        5.166,66       0,00 10403 - Títulos Privados-Debêntures simples                  SBFC - SBF COMERCIO DE PRODUTOS ESPORTIVOS S.A.             
DEBN SBFC12_052025   DEBN SBFC12 I168246                        6.199,99       0,00 10403 - Títulos Privados-Debêntures simples                  SBFC - SBF COMERCIO DE PRODUTOS ESPORTIVOS S.A.             
DEBN SBFC12_052025   DEBN SBFC12 I168246                        3.444,44       0,00 10403 - Títulos Privados-Debêntures simples                  SBFC - SBF COMERCIO DE PRODUTOS ESPORTIVOS S.A.             
DEBN SBFC12_052025   DEBN SBFC12 I168246                       11.022,21       0,00 10403 - Títulos Privados-Debêntures simples                  SBFC - SBF COMERCIO DE PRODUTOS ESPORTIVOS S.A.             
DEBN SBFC12_052025   DEBN SBFC12 I168246                        5.511,10       0,00 10403 - Títulos Privados-Debêntures simples                  SBFC - SBF COMERCIO DE PRODUTOS ESPORTIVOS S.A.             
DEBN SBFC12_052025   DEBN SBFC12 I168246                       98.510,98       0,00 10403 - Títulos Privados-Debêntures simples                  SBFC - SBF COMERCIO DE PRODUTOS ESPORTIVOS S.A.             
DEBN SBFC12_052025   DEBN SBFC12 I168246                        5.166,66       0,00 10403 - Títulos Privados-Debêntures simples                  SBFC - SBF COMERCIO DE PRODUTOS ESPORTIVOS S.A.             
DEBN SBFC12_052025   DEBN SBFC12 I168246                        2.755,55       0,00 10403 - Títulos Privados-Debêntures simples                  SBFC - SBF COMERCIO DE PRODUTOS ESPORTIVOS S.A.             
DEBN SBFC12_052025   DEBN SBFC12 I168246                        6.544,44       0,00 10403 - Títulos Privados-Debêntures simples                  SBFC - SBF COMERCIO DE PRODUTOS ESPORTIVOS S.A.             
DEBN BRKPA1_032028   DEBN BRKPA1 I128038                       32.621,30       0,00 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN SBFC12_052025   DEBN SBFC12 I168246                        7.577,77       0,00 10403 - Títulos Privados-Debêntures simples                  SBFC - SBF COMERCIO DE PRODUTOS ESPORTIVOS S.A.             
DEBN SBFC12_052025   DEBN SBFC12 I168246                        4.133,33       0,00 10403 - Títulos Privados-Debêntures simples                  SBFC - SBF COMERCIO DE PRODUTOS ESPORTIVOS S.A.             
DEBN SBFC12_052025   DEBN SBFC12 I168246                        7.922,21       0,00 10403 - Títulos Privados-Debêntures simples                  SBFC - SBF COMERCIO DE PRODUTOS ESPORTIVOS S.A.             
DEBN SBFC12_052025   DEBN SBFC12 I168246                       13.777,76       0,00 10403 - Títulos Privados-Debêntures simples                  SBFC - SBF COMERCIO DE PRODUTOS ESPORTIVOS S.A.             
DEBN SBFC12_052025   DEBN SBFC12 I168246                        7.233,32       0,00 10403 - Títulos Privados-Debêntures simples                  SBFC - SBF COMERCIO DE PRODUTOS ESPORTIVOS S.A.             
DEBN SBFC12_052025   DEBN SBFC12 I168246                        6.888,88       0,00 10403 - Títulos Privados-Debêntures simples                  SBFC - SBF COMERCIO DE PRODUTOS ESPORTIVOS S.A.             
DEBN SBFC12_052025   DEBN SBFC12 I168246                        5.511,10       0,00 10403 - Títulos Privados-Debêntures simples                  SBFC - SBF COMERCIO DE PRODUTOS ESPORTIVOS S.A.             
DEBN SBFC12_052025   DEBN SBFC12 I168246                       15.499,98       0,00 10403 - Títulos Privados-Debêntures simples                  SBFC - SBF COMERCIO DE PRODUTOS ESPORTIVOS S.A.             
DEBN SBFC12_052025   DEBN SBFC12 I168246                        1.033,33       0,00 10403 - Títulos Privados-Debêntures simples                  SBFC - SBF COMERCIO DE PRODUTOS ESPORTIVOS S.A.             
DEBN SBFC12_052025   DEBN SBFC12 I168246                          344,44       0,00 10403 - Títulos Privados-Debêntures simples                  SBFC - SBF COMERCIO DE PRODUTOS ESPORTIVOS S.A.             
DEBN BRKPA1_032028   DEBN BRKPA1 I128038                       95.689,14       0,00 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN SBFC12_052025   DEBN SBFC12 I168246                      119.866,50       0,00 10403 - Títulos Privados-Debêntures simples                  SBFC - SBF COMERCIO DE PRODUTOS ESPORTIVOS S.A.             
DEBN SBFC12_052025   DEBN SBFC12 I168246                      491.521,57       0,01 10403 - Títulos Privados-Debêntures simples                  SBFC - SBF COMERCIO DE PRODUTOS ESPORTIVOS S.A.             
DEBN SBFC12_052025   DEBN SBFC12 I168246                        3.100,00       0,00 10403 - Títulos Privados-Debêntures simples                  SBFC - SBF COMERCIO DE PRODUTOS ESPORTIVOS S.A.             
DEBN SBFC12_052025   DEBN SBFC12 I168246                       37.199,95       0,00 10403 - Títulos Privados-Debêntures simples                  SBFC - SBF COMERCIO DE PRODUTOS ESPORTIVOS S.A.             
DEBN SBFC12_052025   DEBN SBFC12 I168246                        5.511,10       0,00 10403 - Títulos Privados-Debêntures simples                  SBFC - SBF COMERCIO DE PRODUTOS ESPORTIVOS S.A.             
DEBN SBFC12_052025   DEBN SBFC12 I168246                      -20.322,20       0,00 10403 - Títulos Privados-Debêntures simples                  SBFC - SBF COMERCIO DE PRODUTOS ESPORTIVOS S.A.             
DEBN SBFC12_052025   DEBN SBFC12 I168246                      449.154,94       0,01 10403 - Títulos Privados-Debêntures simples                  SBFC - SBF COMERCIO DE PRODUTOS ESPORTIVOS S.A.             
DEBN SBFC12_052025   DEBN SBFC12 I168246                       10.333,32       0,00 10403 - Títulos Privados-Debêntures simples                  SBFC - SBF COMERCIO DE PRODUTOS ESPORTIVOS S.A.             
DEBN SBFC12_052025   DEBN SBFC12 I168246                        2.411,11       0,00 10403 - Títulos Privados-Debêntures simples                  SBFC - SBF COMERCIO DE PRODUTOS ESPORTIVOS S.A.             
DEBN SBFC12_052025   DEBN SBFC12 I168246                       45.811,05       0,00 10403 - Títulos Privados-Debêntures simples                  SBFC - SBF COMERCIO DE PRODUTOS ESPORTIVOS S.A.             
DEBN BRKPA1_032028   DEBN BRKPA1 I128038                       98.951,27       0,00 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN SBFC12_052025   DEBN SBFC12 I168246                       83.699,89       0,00 10403 - Títulos Privados-Debêntures simples                  SBFC - SBF COMERCIO DE PRODUTOS ESPORTIVOS S.A.             
DEBN SBFC12_052025   DEBN SBFC12 I168246                      183.244,20       0,00 10403 - Títulos Privados-Debêntures simples                  SBFC - SBF COMERCIO DE PRODUTOS ESPORTIVOS S.A.             
DEBN SBSPC2_022025   DEBN SBSPC2 I455789                        1.527,09       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SBSPC2_022025   DEBN SBSPC2 I455789                          763,54       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SBSPC2_022025   DEBN SBSPC2 I455789                       88.571,04       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SBSPC2_022025   DEBN SBSPC2 I455789                        2.290,63       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SBSPC2_022025   DEBN SBSPC2 I455789                          763,54       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SBSPC2_022025   DEBN SBSPC2 I455789                          763,54       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SBSPC2_022025   DEBN SBSPC2 I455789                      158.817,04       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SBSPC2_022025   DEBN SBSPC2 I455789                        1.527,09       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN BRKPA1_032028   DEBN BRKPA1 I128038                       54.368,83       0,00 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN SBSPC2_022025   DEBN SBSPC2 I455789                        2.290,63       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SBSPC2_022025   DEBN SBSPC2 I455789                        2.290,63       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SBSPC2_022025   DEBN SBSPC2 I455789                          763,54       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SBSPC2_022025   DEBN SBSPC2 I455789                       13.743,78       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SBSPC2_022025   DEBN SBSPC2 I455789                       50.393,87       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SBSPC2_022025   DEBN SBSPC2 I455789                        2.290,63       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SBSPC2_022025   DEBN SBSPC2 I455789                          763,54       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SBSPC2_022025   DEBN SBSPC2 I455789                      539.825,24       0,01 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SBSPC2_022025   DEBN SBSPC2 I455789                        2.290,63       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SBSPC2_022025   DEBN SBSPC2 I455789                          763,54       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN BRKPA1_032028   DEBN BRKPA1 I128038                       23.922,29       0,00 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN SBSPC2_022025   DEBN SBSPC2 I455789                        2.290,63       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SBSPC2_022025   DEBN SBSPC2 I455789                        1.527,09       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SBSPC2_022025   DEBN SBSPC2 I455789                        2.290,63       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SBSPC2_022025   DEBN SBSPC2 I455789                        2.290,63       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SBSPC2_022025   DEBN SBSPC2 I455789                        9.926,07       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SBSPC2_022025   DEBN SBSPC2 I455789                        2.290,63       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SBSPC2_022025   DEBN SBSPC2 I455789                        2.290,63       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SBSPC2_022025   DEBN SBSPC2 I455789                          763,54       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SBSPC2_022025   DEBN SBSPC2 I455789                          763,54       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SBSPC2_022025   DEBN SBSPC2 I455789                        2.290,63       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
CRI_23F1240696       CRI_23F1240696 CRI  I265126               54.690,37       0,00 10429 - Títulos Privados-Cert.Receb. Imobiliários (CRI)      APCS - TRUE SECURITIZADORA S.A.                             
DEBN AEGPA0_052029   DEBN AEGPA0 H750651                        1.033,52       0,00 10440 - Títulos Privados-Debêntures Incent. (Lei 12.431)     AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN BRKPA1_032028   DEBN BRKPA1 I128038                       41.320,31       0,00 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN SBSPC2_022025   DEBN SBSPC2 I455789                      161.107,67       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SBSPC2_022025   DEBN SBSPC2 I455789                        5.344,81       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SBSPC2_022025   DEBN SBSPC2 I455789                        4.581,26       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SBSPC2_022025   DEBN SBSPC2 I455789                        1.527,09       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SBSPC2_022025   DEBN SBSPC2 I455789                        2.290,63       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SBSPC2_022025   DEBN SBSPC2 I455789                        3.817,72       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SBSPC2_022025   DEBN SBSPC2 I455789                        1.527,09       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SBSPF8_072028   DEBN SBSPF8 I128043                       24.650,27       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SBSPF8_072028   DEBN SBSPF8 I128043                        2.054,19       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SBSPF8_072028   DEBN SBSPF8 I128043                        7.189,66       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN BRKPA1_032028   DEBN BRKPA1 I128038                       41.320,32       0,00 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN SBSPF8_072028   DEBN SBSPF8 I128043                        3.081,28       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SBSPF8_072028   DEBN SBSPF8 I128043                        6.162,57       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SBSPF8_072028   DEBN SBSPF8 I128043                       13.352,23       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SBSPF8_072028   DEBN SBSPF8 I128043                       10.270,95       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SBSPF8_072028   DEBN SBSPF8 I128043                       23.623,18       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SBSPF8_072028   DEBN SBSPF8 I128043                        7.189,66       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SBSPF8_072028   DEBN SBSPF8 I128043                       19.514,80       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SBSPF8_072028   DEBN SBSPF8 I128043                       14.379,32       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SBSPF8_072028   DEBN SBSPF8 I128043                       14.379,33       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SBSPF8_072028   DEBN SBSPF8 I128043                        4.108,38       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN BRKPA1_032028   DEBN BRKPA1 I128038                       55.456,21       0,00 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN SBSPF8_072028   DEBN SBSPF8 I128043                       11.298,04       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SBSPF8_072028   DEBN SBSPF8 I128043                       10.270,95       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SBSPF8_072028   DEBN SBSPF8 I128043                        4.108,38       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SBSPF8_072028   DEBN SBSPF8 I128043                       13.352,23       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SBSPF8_072028   DEBN SBSPF8 I128043                       10.270,95       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SBSPF8_072028   DEBN SBSPF8 I128043                       53.408,93       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SBSPF8_072028   DEBN SBSPF8 I128043                       32.867,03       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SBSPF8_072028   DEBN SBSPF8 I128043                      272.180,13       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SBSPF8_072028   DEBN SBSPF8 I128043                      397.485,70       0,01 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SBSPF8_072028   DEBN SBSPF8 I128043                        6.162,57       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN BRKPA1_032028   DEBN BRKPA1 I128038                    1.293.978,19       0,02 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN SBSPF8_072028   DEBN SBSPF8 I128043                        4.108,38       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SBSPF8_072028   DEBN SBSPF8 I128043                    2.515.355,25       0,04 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SBSPF8_072028   DEBN SBSPF8 I128043                       15.406,42       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SBSPF8_072028   DEBN SBSPF8 I128043                        3.081,28       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SBSPF8_072028   DEBN SBSPF8 I128043                       13.352,23       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SBSPF8_072028   DEBN SBSPF8 I128043                       10.270,95       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SBSPF8_072028   DEBN SBSPF8 I128043                       17.460,61       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SBSPF8_072028   DEBN SBSPF8 I128043                      103.736,57       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SBSPF8_072028   DEBN SBSPF8 I128043                       66.761,16       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SBSPG0_032027   DEBN SBSPG0 I62104                         4.745,40       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN BRKPA1_032028   DEBN BRKPA1 I128038                      364.271,17       0,01 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN SBSPG0_032027   DEBN SBSPG0 I62104                         4.745,40       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SBSPG0_032027   DEBN SBSPG0 I62104                        12.654,39       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SBSPG0_032027   DEBN SBSPG0 I62104                         1.581,80       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SBSPG0_032027   DEBN SBSPG0 I62104                         2.372,70       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SBSPG0_032027   DEBN SBSPG0 I62104                        11.863,49       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SBSPG0_032027   DEBN SBSPG0 I62104                           790,90       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SBSPG0_032027   DEBN SBSPG0 I62104                         3.163,60       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SBSPG0_032027   DEBN SBSPG0 I62104                         7.118,09       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SBSPG0_032027   DEBN SBSPG0 I62104                         7.908,99       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SBSPG0_032027   DEBN SBSPG0 I62104                       229.360,82       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN BRKPA1_032028   DEBN BRKPA1 I128038                       38.058,18       0,00 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN SBSPG0_032027   DEBN SBSPG0 I62104                        30.054,18       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SBSPG0_032027   DEBN SBSPG0 I62104                         3.163,60       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SBSPG0_032027   DEBN SBSPG0 I62104                         7.908,99       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SBSPG0_032027   DEBN SBSPG0 I62104                     1.190.303,57       0,02 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SBSPG0_032027   DEBN SBSPG0 I62104                         5.536,30       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SBSPG0_032027   DEBN SBSPG0 I62104                         2.372,70       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SBSPG0_032027   DEBN SBSPG0 I62104                        10.281,69       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SBSPG0_032027   DEBN SBSPG0 I62104                         7.909,00       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SBSPG0_032027   DEBN SBSPG0 I62104                         3.954,50       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SBSPG0_032027   DEBN SBSPG0 I62104                         1.581,80       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN BRKPA1_032028   DEBN BRKPA1 I128038                      206.601,56       0,00 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN SBSPG0_032027   DEBN SBSPG0 I62104                        31.635,98       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SBSPG0_032027   DEBN SBSPG0 I62104                       149.479,98       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SBSPG0_032027   DEBN SBSPG0 I62104                       130.498,40       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SBSPG0_032027   DEBN SBSPG0 I62104                         6.327,20       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SBSPG0_032027   DEBN SBSPG0 I62104                         5.536,30       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SBSPG0_032027   DEBN SBSPG0 I62104                         4.745,40       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SBSPG0_032027   DEBN SBSPG0 I62104                        15.817,99       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SBSPG0_032027   DEBN SBSPG0 I62104                         2.372,70       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SBSPG0_032027   DEBN SBSPG0 I62104                         7.118,10       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SBSPG0_032027   DEBN SBSPG0 I62104                         7.118,09       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN BRKPA1_032028   DEBN BRKPA1 I128038                      198.989,92       0,00 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN SBSPG0_032027   DEBN SBSPG0 I62104                         3.954,50       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SBSPH0_032029   DEBN SBSPH0 I156926                       16.063,25       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SBSPH0_032029   DEBN SBSPH0 I156926                      399.439,49       0,01 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SBSPH0_032029   DEBN SBSPH0 I156926                       47.118,87       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SBSPH0_032029   DEBN SBSPH0 I156926                       16.063,25       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SBSPH0_032029   DEBN SBSPH0 I156926                       35.339,15       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SBSPH0_032029   DEBN SBSPH0 I156926                       11.779,72       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SBSPH0_032029   DEBN SBSPH0 I156926                       26.772,08       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SBSPH0_032029   DEBN SBSPH0 I156926                        5.354,42       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SBSPH0_032029   DEBN SBSPH0 I156926                       29.984,73       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN BRKPA1_032028   DEBN BRKPA1 I128038                       23.922,29       0,00 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN SBSPH0_032029   DEBN SBSPH0 I156926                        5.354,42       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SBSPH0_032029   DEBN SBSPH0 I156926                       14.992,37       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SBSPH0_032029   DEBN SBSPH0 I156926                       20.346,78       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SBSPH0_032029   DEBN SBSPH0 I156926                       22.488,55       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SBSPH0_032029   DEBN SBSPH0 I156926                       35.339,15       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SBSPH0_032029   DEBN SBSPH0 I156926                        5.354,42       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SBSPH0_032029   DEBN SBSPH0 I156926                       14.992,37       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SBSPH0_032029   DEBN SBSPH0 I156926                       19.275,90       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SBSPH0_032029   DEBN SBSPH0 I156926                        5.354,42       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SBSPH0_032029   DEBN SBSPH0 I156926                        9.637,95       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN BRKPA1_032028   DEBN BRKPA1 I128038                       23.922,29       0,00 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN SBSPH0_032029   DEBN SBSPH0 I156926                        7.496,18       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SBSPH0_032029   DEBN SBSPH0 I156926                       19.275,90       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SBSPH0_032029   DEBN SBSPH0 I156926                       10.708,83       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SBSPH0_032029   DEBN SBSPH0 I156926                      582.560,54       0,01 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SBSPH0_032029   DEBN SBSPH0 I156926                       54.615,05       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SBSPH0_032029   DEBN SBSPH0 I156926                       21.417,67       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SBSPH0_032029   DEBN SBSPH0 I156926                        8.567,07       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SBSPH0_032029   DEBN SBSPH0 I156926                       20.346,78       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SBSPH0_032029   DEBN SBSPH0 I156926                    3.717.036,09       0,07 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SBSPH0_032029   DEBN SBSPH0 I156926                      134.931,30       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN AEGPA0_052029   DEBN AEGPA0 H750651                        5.167,58       0,00 10440 - Títulos Privados-Debêntures Incent. (Lei 12.431)     AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN BRKPA1_032028   DEBN BRKPA1 I128038                       19.572,78       0,00 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN SBSPH0_032029   DEBN SBSPH0 I156926                       97.450,38       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SBSPH0_032029   DEBN SBSPH0 I156926                        1.070,88       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SBSPH0_032029   DEBN SBSPH0 I156926                      133.860,42       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SBSPH0_032029   DEBN SBSPH0 I156926                       17.134,13       0,00 10403 - Títulos Privados-Debêntures simples                  SBSP - COMPANHIA SANEAMENTO BASICO ESTADO SAO PAULO SABES   
DEBN SMFT18_102030   DEBN SMFT18 I497389                   15.393.615,14       0,28 10403 - Títulos Privados-Debêntures simples                  SMFT - SMARTFIT ESCOLA GINASTICA DANCA SA                   
DEBN SMFT18_102030   DEBN SMFT18 I497389                   12.518.294,43       0,22 10403 - Títulos Privados-Debêntures simples                  SMFT - SMARTFIT ESCOLA GINASTICA DANCA SA                   
DEBN SMFT18_102030   DEBN SMFT18 I497389                       41.532,41       0,00 10403 - Títulos Privados-Debêntures simples                  SMFT - SMARTFIT ESCOLA GINASTICA DANCA SA                   
DEBN SMFT18_102030   DEBN SMFT18 I497389                    4.298.072,00       0,08 10403 - Títulos Privados-Debêntures simples                  SMFT - SMARTFIT ESCOLA GINASTICA DANCA SA                   
DEBN SMFT18_102030   DEBN SMFT18 I497389                      307.765,81       0,01 10403 - Títulos Privados-Debêntures simples                  SMFT - SMARTFIT ESCOLA GINASTICA DANCA SA                   
DEBN SMFT18_102030   DEBN SMFT18 I497389                      724.154,85       0,01 10403 - Títulos Privados-Debêntures simples                  SMFT - SMARTFIT ESCOLA GINASTICA DANCA SA                   
DEBN BRKPA1_032028   DEBN BRKPA1 I128038                      166.368,63       0,00 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN SMFT18_102030   DEBN SMFT18 I497389                       40.467,48       0,00 10403 - Títulos Privados-Debêntures simples                  SMFT - SMARTFIT ESCOLA GINASTICA DANCA SA                   
DEBN SMFT18_102030   DEBN SMFT18 I497389                      169.324,44       0,00 10403 - Títulos Privados-Debêntures simples                  SMFT - SMARTFIT ESCOLA GINASTICA DANCA SA                   
DEBN SMFT18_102030   DEBN SMFT18 I497389                    6.612.172,70       0,12 10403 - Títulos Privados-Debêntures simples                  SMFT - SMARTFIT ESCOLA GINASTICA DANCA SA                   
DEBN SMFT18_102030   DEBN SMFT18 I497389                      111.818,03       0,00 10403 - Títulos Privados-Debêntures simples                  SMFT - SMARTFIT ESCOLA GINASTICA DANCA SA                   
DEBN SMFT18_102030   DEBN SMFT18 I497389                    2.812.489,63       0,05 10403 - Títulos Privados-Debêntures simples                  SMFT - SMARTFIT ESCOLA GINASTICA DANCA SA                   
DEBN SMFT18_102030   DEBN SMFT18 I497389                       89.454,42       0,00 10403 - Títulos Privados-Debêntures simples                  SMFT - SMARTFIT ESCOLA GINASTICA DANCA SA                   
DEBN SNGO10_062027   DEBN SNGO10 I343607                        4.916,82       0,00 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN SNGO10_062027   DEBN SNGO10 I343607                      177.825,08       0,00 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN SNGO10_062027   DEBN SNGO10 I343607                        2.458,41       0,00 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN SNGO10_062027   DEBN SNGO10 I343607                        3.277,88       0,00 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN BRKPA1_032028   DEBN BRKPA1 I128038                    1.750.676,38       0,03 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN SNGO10_062027   DEBN SNGO10 I343607                        7.375,23       0,00 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN SNGO10_062027   DEBN SNGO10 I343607                          819,47       0,00 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN SNGO10_062027   DEBN SNGO10 I343607                        9.833,64       0,00 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN SNGO10_062027   DEBN SNGO10 I343607                       18.028,35       0,00 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN SNGO10_062027   DEBN SNGO10 I343607                        1.638,94       0,00 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN SNGO10_062027   DEBN SNGO10 I343607                        4.916,82       0,00 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN SNGO10_062027   DEBN SNGO10 I343607                       50.807,17       0,00 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN SNGO10_062027   DEBN SNGO10 I343607                        6.555,76       0,00 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN SNGO10_062027   DEBN SNGO10 I343607                        1.638,94       0,00 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN SNGO10_062027   DEBN SNGO10 I343607                        1.638,94       0,00 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN BRKPA1_032028   DEBN BRKPA1 I128038                        7.611,63       0,00 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN SNGO10_062027   DEBN SNGO10 I343607                       40.154,05       0,00 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN SNGO10_062027   DEBN SNGO10 I343607                        4.916,82       0,00 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN SNGO10_062027   DEBN SNGO10 I343607                        4.097,35       0,00 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN SNGO10_062027   DEBN SNGO10 I343607                    1.241.497,68       0,02 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN SNGO10_062027   DEBN SNGO10 I343607                        6.555,76       0,00 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN SNGO10_062027   DEBN SNGO10 I343607                        3.277,88       0,00 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN SNGO10_062027   DEBN SNGO10 I343607                        3.277,88       0,00 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN SNGO10_062027   DEBN SNGO10 I343607                      116.364,80       0,00 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN SNGO10_062027   DEBN SNGO10 I343607                        4.916,82       0,00 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN SNGO10_062027   DEBN SNGO10 I343607                       10.653,11       0,00 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN BRKPA1_032028   DEBN BRKPA1 I128038                      241.397,61       0,00 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN SNGO10_062027   DEBN SNGO10 I343607                        4.916,82       0,00 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN SNGO10_062027   DEBN SNGO10 I343607                       12.292,05       0,00 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN SNGO10_062027   DEBN SNGO10 I343607                        3.277,88       0,00 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN SNGO10_062027   DEBN SNGO10 I343607                        1.638,94       0,00 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN SNGO10_062027   DEBN SNGO10 I343607                        3.277,88       0,00 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN SNGO10_062027   DEBN SNGO10 I343607                        6.555,76       0,00 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN SNGO10_062027   DEBN SNGO10 I343607                        4.916,82       0,00 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN SNGO10_062027   DEBN SNGO10 I343607                        1.638,94       0,00 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN SNGO10_062027   DEBN SNGO10 I343607                        6.555,76       0,00 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN SNGO10_062027   DEBN SNGO10 I343607                        4.916,82       0,00 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN BRKPA1_032028   DEBN BRKPA1 I128038                       67.417,35       0,00 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN SNGO18_112025   DEBN SNGO18 H813705                        1.968,74       0,00 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN SNGO18_112025   DEBN SNGO18 H813705                        5.624,97       0,00 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN SNGO18_112025   DEBN SNGO18 H813705                        2.812,48       0,00 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN SNGO18_112025   DEBN SNGO18 H813705                       13.781,17       0,00 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN SNGO18_112025   DEBN SNGO18 H813705                        7.874,96       0,00 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN SNGO18_112025   DEBN SNGO18 H813705                        8.156,21       0,00 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN SNGO18_112025   DEBN SNGO18 H813705                       20.812,38       0,00 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN SNGO18_112025   DEBN SNGO18 H813705                       13.781,18       0,00 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN SNGO18_112025   DEBN SNGO18 H813705                        5.906,22       0,00 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN SNGO18_112025   DEBN SNGO18 H813705                       10.124,95       0,00 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN BRKPA1_032028   DEBN BRKPA1 I128038                       45.669,82       0,00 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN SNGO18_112025   DEBN SNGO18 H813705                      588.090,58       0,01 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN SNGO18_112025   DEBN SNGO18 H813705                        7.312,46       0,00 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN SNGO18_112025   DEBN SNGO18 H813705                        1.968,74       0,00 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN SNGO18_112025   DEBN SNGO18 H813705                        3.093,73       0,00 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN SNGO18_112025   DEBN SNGO18 H813705                      673.027,62       0,01 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN SNGO18_112025   DEBN SNGO18 H813705                       10.124,95       0,00 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN SNGO18_112025   DEBN SNGO18 H813705                        2.531,24       0,00 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN SNGO18_112025   DEBN SNGO18 H813705                        5.906,22       0,00 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN SNGO18_112025   DEBN SNGO18 H813705                        6.468,72       0,00 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN SNGO18_112025   DEBN SNGO18 H813705                        2.249,99       0,00 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN BRKPA1_032028   DEBN BRKPA1 I128038                      519.766,04       0,01 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN SNGO18_112025   DEBN SNGO18 H813705                        5.906,22       0,00 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN SNGO18_112025   DEBN SNGO18 H813705                        7.593,71       0,00 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN SNGO18_112025   DEBN SNGO18 H813705                        4.499,98       0,00 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN SNGO18_112025   DEBN SNGO18 H813705                        4.218,73       0,00 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN SNGO18_112025   DEBN SNGO18 H813705                       11.249,94       0,00 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN SNGO19_082026   DEBN SNGO19 I158982                       31.209,04       0,00 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN SNGO19_082026   DEBN SNGO19 I158982                        4.842,78       0,00 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN SNGO19_082026   DEBN SNGO19 I158982                        8.609,39       0,00 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN SNGO19_082026   DEBN SNGO19 I158982                        4.842,78       0,00 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN SNGO19_082026   DEBN SNGO19 I158982                       12.914,09       0,00 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN BRKPA1_032028   DEBN BRKPA1 I128038                       30.446,55       0,00 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN SNGO19_082026   DEBN SNGO19 I158982                       17.218,78       0,00 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN SNGO19_082026   DEBN SNGO19 I158982                       10.223,65       0,00 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN SNGO19_082026   DEBN SNGO19 I158982                       23.137,74       0,00 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN SNGO19_082026   DEBN SNGO19 I158982                       32.285,21       0,00 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN SNGO19_082026   DEBN SNGO19 I158982                       10.223,65       0,00 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN SNGO19_082026   DEBN SNGO19 I158982                       18.294,96       0,00 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN SNGO19_082026   DEBN SNGO19 I158982                       18.833,05       0,00 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN SNGO19_082026   DEBN SNGO19 I158982                       13.452,17       0,00 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN SNGO19_082026   DEBN SNGO19 I158982                        4.842,78       0,00 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN SNGO19_082026   DEBN SNGO19 I158982                       13.452,17       0,00 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN BRKPA1_032028   DEBN BRKPA1 I128038                        2.174,75       0,00 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN SNGO19_082026   DEBN SNGO19 I158982                       19.909,22       0,00 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN SNGO19_082026   DEBN SNGO19 I158982                        5.918,96       0,00 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN SNGO19_082026   DEBN SNGO19 I158982                        1.614,26       0,00 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN SNGO19_082026   DEBN SNGO19 I158982                       15.066,43       0,00 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN SNGO19_082026   DEBN SNGO19 I158982                       17.218,78       0,00 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN SNGO19_082026   DEBN SNGO19 I158982                        9.685,56       0,00 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN SNGO19_082026   DEBN SNGO19 I158982                      244.291,47       0,00 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN SNGO19_082026   DEBN SNGO19 I158982                       86.093,91       0,00 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN SNGO19_082026   DEBN SNGO19 I158982                       64.032,35       0,00 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN SNGO19_082026   DEBN SNGO19 I158982                      358.903,98       0,01 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN AEGPA0_052029   DEBN AEGPA0 H750651                        4.134,06       0,00 10440 - Títulos Privados-Debêntures Incent. (Lei 12.431)     AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN BRKPA1_032028   DEBN BRKPA1 I128038                       22.834,91       0,00 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN SNGO19_082026   DEBN SNGO19 I158982                       43.046,95       0,00 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN SNGO19_082026   DEBN SNGO19 I158982                      593.509,88       0,01 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN SNGO19_082026   DEBN SNGO19 I158982                       13.990,26       0,00 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN SNGO19_082026   DEBN SNGO19 I158982                        7.533,22       0,00 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN SNGO19_082026   DEBN SNGO19 I158982                       25.828,17       0,00 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN SNGO19_082026   DEBN SNGO19 I158982                      419.707,81       0,01 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN SNGO19_082026   DEBN SNGO19 I158982                        8.071,30       0,00 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN SNGO19_082026   DEBN SNGO19 I158982                    3.317.844,01       0,06 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN SNGO19_082026   DEBN SNGO19 I158982                      171.649,73       0,00 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN SNGO19_082026   DEBN SNGO19 I158982                       18.833,04       0,00 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN BRKPA1_032028   DEBN BRKPA1 I128038                       23.922,29       0,00 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN SNGO19_082026   DEBN SNGO19 I158982                       13.990,26       0,00 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN SNGO19_082026   DEBN SNGO19 I158982                        4.304,70       0,00 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN SNGOA1_082028   DEBN SNGOA1 I390399                      131.979,88       0,00 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN SNGOA1_082028   DEBN SNGOA1 I390399                      104.140,38       0,00 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN SNGOA1_082028   DEBN SNGOA1 I390399                      253.648,84       0,00 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN SNGOA1_082028   DEBN SNGOA1 I390399                       36.088,25       0,00 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN SNGOA1_082028   DEBN SNGOA1 I390399                    5.718.440,84       0,10 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN SNGOA1_082028   DEBN SNGOA1 I390399                      513.484,23       0,01 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN SNGOA1_082028   DEBN SNGOA1 I390399                    2.612.789,23       0,05 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN SNGOA1_082028   DEBN SNGOA1 I390399                      794.972,57       0,01 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN BRKPA1_032028   DEBN BRKPA1 I128038                       60.893,10       0,00 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN SNGOA1_082028   DEBN SNGOA1 I390399                       20.621,86       0,00 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN SNGOA1_082028   DEBN SNGOA1 I390399                      153.632,83       0,00 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN SNGOA1_082028   DEBN SNGOA1 I390399                   28.044.693,91       0,50 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN SNGOA1_082028   DEBN SNGOA1 I390399                      104.140,38       0,00 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN SNGOA1_082028   DEBN SNGOA1 I390399                      107.233,65       0,00 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN SNGOA1_082028   DEBN SNGOA1 I390399                       37.119,34       0,00 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN SNGOA1_082028   DEBN SNGOA1 I390399                      200.032,01       0,00 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN SNGOA1_082028   DEBN SNGOA1 I390399                       62.896,66       0,00 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN SNGOA1_082028   DEBN SNGOA1 I390399                    4.587.332,01       0,08 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN SNGOA1_082028   DEBN SNGOA1 I390399                      168.068,14       0,00 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN BRKPA1_032028   DEBN BRKPA1 I128038                       30.446,55       0,00 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN SNGOA1_082028   DEBN SNGOA1 I390399                       80.425,24       0,00 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN SNGOA1_082028   DEBN SNGOA1 I390399                      234.058,07       0,00 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN SNGOA1_082028   DEBN SNGOA1 I390399                      103.109,28       0,00 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN SNGOA1_082028   DEBN SNGOA1 I390399                        7.217,65       0,00 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN SNGOA1_082028   DEBN SNGOA1 I390399                       64.958,85       0,00 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN SNGOA1_082028   DEBN SNGOA1 I390399                    1.709.551,91       0,03 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN SNGOA1_082028   DEBN SNGOA1 I390399                      104.140,38       0,00 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN SNGOA1_082028   DEBN SNGOA1 I390399                      100.016,00       0,00 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN SNGOA1_082028   DEBN SNGOA1 I390399                      144.353,00       0,00 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN SNGOA1_082028   DEBN SNGOA1 I390399                      117.544,59       0,00 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN BRKPA1_032028   DEBN BRKPA1 I128038                       15.223,27       0,00 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN SNGOA1_082028   DEBN SNGOA1 I390399                       78.363,06       0,00 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN SNGOA1_082028   DEBN SNGOA1 I390399                      134.042,07       0,00 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN SNGOA1_082028   DEBN SNGOA1 I390399                       47.430,27       0,00 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN SNGOA1_082028   DEBN SNGOA1 I390399                       39.181,53       0,00 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN SNGOA1_082028   DEBN SNGOA1 I390399                    3.218.040,73       0,06 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN SNGOA1_082028   DEBN SNGOA1 I390399                      115.482,40       0,00 10403 - Títulos Privados-Debêntures simples                  SNGO - SANEAMENTO GOIAS SA SANEAGO                          
DEBN TAEEA1_052028   DEBN TAEEA1 I158973                       23.207,08       0,00 10403 - Títulos Privados-Debêntures simples                  TAEE - TRANSMISSORA ALIANCA ENERGIA ELETRICA SA             
DEBN TAEEA1_052028   DEBN TAEEA1 I158973                        8.438,94       0,00 10403 - Títulos Privados-Debêntures simples                  TAEE - TRANSMISSORA ALIANCA ENERGIA ELETRICA SA             
DEBN TAEEA1_052028   DEBN TAEEA1 I158973                       27.426,55       0,00 10403 - Títulos Privados-Debêntures simples                  TAEE - TRANSMISSORA ALIANCA ENERGIA ELETRICA SA             
DEBN TAEEA1_052028   DEBN TAEEA1 I158973                       17.932,74       0,00 10403 - Títulos Privados-Debêntures simples                  TAEE - TRANSMISSORA ALIANCA ENERGIA ELETRICA SA             
DEBN BRKPA1_032028   DEBN BRKPA1 I128038                       13.048,52       0,00 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN TAEEA1_052028   DEBN TAEEA1 I158973                       30.591,14       0,00 10403 - Títulos Privados-Debêntures simples                  TAEE - TRANSMISSORA ALIANCA ENERGIA ELETRICA SA             
DEBN TAEEA1_052028   DEBN TAEEA1 I158973                       10.548,67       0,00 10403 - Títulos Privados-Debêntures simples                  TAEE - TRANSMISSORA ALIANCA ENERGIA ELETRICA SA             
DEBN TAEEA1_052028   DEBN TAEEA1 I158973                       13.713,27       0,00 10403 - Títulos Privados-Debêntures simples                  TAEE - TRANSMISSORA ALIANCA ENERGIA ELETRICA SA             
DEBN TAEEA1_052028   DEBN TAEEA1 I158973                       26.371,68       0,00 10403 - Títulos Privados-Debêntures simples                  TAEE - TRANSMISSORA ALIANCA ENERGIA ELETRICA SA             
DEBN TAEEA1_052028   DEBN TAEEA1 I158973                        8.438,94       0,00 10403 - Títulos Privados-Debêntures simples                  TAEE - TRANSMISSORA ALIANCA ENERGIA ELETRICA SA             
DEBN TAEEA1_052028   DEBN TAEEA1 I158973                       33.755,75       0,00 10403 - Títulos Privados-Debêntures simples                  TAEE - TRANSMISSORA ALIANCA ENERGIA ELETRICA SA             
DEBN TAEEA1_052028   DEBN TAEEA1 I158973                       29.536,28       0,00 10403 - Títulos Privados-Debêntures simples                  TAEE - TRANSMISSORA ALIANCA ENERGIA ELETRICA SA             
DEBN TAEEA1_052028   DEBN TAEEA1 I158973                       58.017,69       0,00 10403 - Títulos Privados-Debêntures simples                  TAEE - TRANSMISSORA ALIANCA ENERGIA ELETRICA SA             
DEBN TAEEA1_052028   DEBN TAEEA1 I158973                        1.054,87       0,00 10403 - Títulos Privados-Debêntures simples                  TAEE - TRANSMISSORA ALIANCA ENERGIA ELETRICA SA             
DEBN TAEEA1_052028   DEBN TAEEA1 I158973                       24.261,94       0,00 10403 - Títulos Privados-Debêntures simples                  TAEE - TRANSMISSORA ALIANCA ENERGIA ELETRICA SA             
DEBN BRKPA1_032028   DEBN BRKPA1 I128038                       22.834,91       0,00 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN TAEEA1_052028   DEBN TAEEA1 I158973                       45.359,28       0,00 10403 - Títulos Privados-Debêntures simples                  TAEE - TRANSMISSORA ALIANCA ENERGIA ELETRICA SA             
DEBN TAEEA1_052028   DEBN TAEEA1 I158973                        8.438,94       0,00 10403 - Títulos Privados-Debêntures simples                  TAEE - TRANSMISSORA ALIANCA ENERGIA ELETRICA SA             
DEBN TAEEA1_052028   DEBN TAEEA1 I158973                       24.261,94       0,00 10403 - Títulos Privados-Debêntures simples                  TAEE - TRANSMISSORA ALIANCA ENERGIA ELETRICA SA             
DEBN TAEEA1_052028   DEBN TAEEA1 I158973                       23.207,08       0,00 10403 - Títulos Privados-Debêntures simples                  TAEE - TRANSMISSORA ALIANCA ENERGIA ELETRICA SA             
DEBN TAEEA1_052028   DEBN TAEEA1 I158973                    5.791.220,15       0,10 10403 - Títulos Privados-Debêntures simples                  TAEE - TRANSMISSORA ALIANCA ENERGIA ELETRICA SA             
DEBN TAEEA1_052028   DEBN TAEEA1 I158973                       34.810,61       0,00 10403 - Títulos Privados-Debêntures simples                  TAEE - TRANSMISSORA ALIANCA ENERGIA ELETRICA SA             
DEBN TAEEA1_052028   DEBN TAEEA1 I158973                       13.713,27       0,00 10403 - Títulos Privados-Debêntures simples                  TAEE - TRANSMISSORA ALIANCA ENERGIA ELETRICA SA             
DEBN TAEEA1_052028   DEBN TAEEA1 I158973                      140.297,32       0,00 10403 - Títulos Privados-Debêntures simples                  TAEE - TRANSMISSORA ALIANCA ENERGIA ELETRICA SA             
DEBN TAEEA1_052028   DEBN TAEEA1 I158973                        4.219,47       0,00 10403 - Títulos Privados-Debêntures simples                  TAEE - TRANSMISSORA ALIANCA ENERGIA ELETRICA SA             
DEBN TAEEA1_052028   DEBN TAEEA1 I158973                       23.207,08       0,00 10403 - Títulos Privados-Debêntures simples                  TAEE - TRANSMISSORA ALIANCA ENERGIA ELETRICA SA             
DEBN BRKPA1_032028   DEBN BRKPA1 I128038                      154.407,48       0,00 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN TAEEA1_052028   DEBN TAEEA1 I158973                       52.743,36       0,00 10403 - Títulos Privados-Debêntures simples                  TAEE - TRANSMISSORA ALIANCA ENERGIA ELETRICA SA             
DEBN TAEEA1_052028   DEBN TAEEA1 I158973                       17.932,74       0,00 10403 - Títulos Privados-Debêntures simples                  TAEE - TRANSMISSORA ALIANCA ENERGIA ELETRICA SA             
DEBN TAEEA1_052028   DEBN TAEEA1 I158973                       40.084,95       0,00 10403 - Títulos Privados-Debêntures simples                  TAEE - TRANSMISSORA ALIANCA ENERGIA ELETRICA SA             
DEBN TAEEA5_032029   DEBN TAEEA5_032029 J72316                  1.043,08       0,00 10403 - Títulos Privados-Debêntures simples                  TAEE - TRANSMISSORA ALIANCA ENERGIA ELETRICA SA             
DEBN TAEEA5_032029   DEBN TAEEA5_032029 J72316                 10.430,82       0,00 10403 - Títulos Privados-Debêntures simples                  TAEE - TRANSMISSORA ALIANCA ENERGIA ELETRICA SA             
DEBN TAEEA5_032029   DEBN TAEEA5_032029 J72316                  8.344,66       0,00 10403 - Títulos Privados-Debêntures simples                  TAEE - TRANSMISSORA ALIANCA ENERGIA ELETRICA SA             
DEBN TAEEA5_032029   DEBN TAEEA5_032029 J72316                  3.129,25       0,00 10403 - Títulos Privados-Debêntures simples                  TAEE - TRANSMISSORA ALIANCA ENERGIA ELETRICA SA             
DEBN TAEEA5_032029   DEBN TAEEA5_032029 J72316                  5.215,41       0,00 10403 - Títulos Privados-Debêntures simples                  TAEE - TRANSMISSORA ALIANCA ENERGIA ELETRICA SA             
DEBN TAEEA5_032029   DEBN TAEEA5_032029 J72316                  2.086,16       0,00 10403 - Títulos Privados-Debêntures simples                  TAEE - TRANSMISSORA ALIANCA ENERGIA ELETRICA SA             
DEBN TAEEA5_032029   DEBN TAEEA5_032029 J72316              1.057.685,17       0,02 10403 - Títulos Privados-Debêntures simples                  TAEE - TRANSMISSORA ALIANCA ENERGIA ELETRICA SA             
DEBN BRKPA1_032028   DEBN BRKPA1 I128038                       26.097,04       0,00 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN TAEEA5_032029   DEBN TAEEA5_032029 J72316                  6.258,49       0,00 10403 - Títulos Privados-Debêntures simples                  TAEE - TRANSMISSORA ALIANCA ENERGIA ELETRICA SA             
DEBN TAEEC1_012027   DEBN TAEEC1 H649969                       19.719,26       0,00 10403 - Títulos Privados-Debêntures simples                  TAEE - TRANSMISSORA ALIANCA ENERGIA ELETRICA SA             
DEBN TAEEC1_012027   DEBN TAEEC1 H649969                       63.237,64       0,00 10403 - Títulos Privados-Debêntures simples                  TAEE - TRANSMISSORA ALIANCA ENERGIA ELETRICA SA             
DEBN TAEEC1_012027   DEBN TAEEC1 H649969                        2.039,92       0,00 10403 - Títulos Privados-Debêntures simples                  TAEE - TRANSMISSORA ALIANCA ENERGIA ELETRICA SA             
DEBN TAEEC1_012027   DEBN TAEEC1 H649969                        7.479,72       0,00 10403 - Títulos Privados-Debêntures simples                  TAEE - TRANSMISSORA ALIANCA ENERGIA ELETRICA SA             
DEBN TAEEC1_012027   DEBN TAEEC1 H649969                        6.119,77       0,00 10403 - Títulos Privados-Debêntures simples                  TAEE - TRANSMISSORA ALIANCA ENERGIA ELETRICA SA             
DEBN TAEEC1_012027   DEBN TAEEC1 H649969                        3.399,87       0,00 10403 - Títulos Privados-Debêntures simples                  TAEE - TRANSMISSORA ALIANCA ENERGIA ELETRICA SA             
DEBN TAEEC1_012027   DEBN TAEEC1 H649969                        6.799,75       0,00 10403 - Títulos Privados-Debêntures simples                  TAEE - TRANSMISSORA ALIANCA ENERGIA ELETRICA SA             
DEBN TAEEC1_012027   DEBN TAEEC1 H649969                        4.079,85       0,00 10403 - Títulos Privados-Debêntures simples                  TAEE - TRANSMISSORA ALIANCA ENERGIA ELETRICA SA             
DEBN TAEEC1_012027   DEBN TAEEC1 H649969                        5.439,80       0,00 10403 - Títulos Privados-Debêntures simples                  TAEE - TRANSMISSORA ALIANCA ENERGIA ELETRICA SA             
DEBN BRKPA1_032028   DEBN BRKPA1 I128038                       30.446,55       0,00 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN TAEEC1_012027   DEBN TAEEC1 H649969                        1.359,95       0,00 10403 - Títulos Privados-Debêntures simples                  TAEE - TRANSMISSORA ALIANCA ENERGIA ELETRICA SA             
DEBN TAEEC1_012027   DEBN TAEEC1 H649969                        1.359,95       0,00 10403 - Títulos Privados-Debêntures simples                  TAEE - TRANSMISSORA ALIANCA ENERGIA ELETRICA SA             
DEBN TAEEC1_012027   DEBN TAEEC1 H649969                          679,97       0,00 10403 - Títulos Privados-Debêntures simples                  TAEE - TRANSMISSORA ALIANCA ENERGIA ELETRICA SA             
DEBN TAEEC1_012027   DEBN TAEEC1 H649969                       12.239,54       0,00 10403 - Títulos Privados-Debêntures simples                  TAEE - TRANSMISSORA ALIANCA ENERGIA ELETRICA SA             
DEBN TAEEC1_012027   DEBN TAEEC1 H649969                        4.759,82       0,00 10403 - Títulos Privados-Debêntures simples                  TAEE - TRANSMISSORA ALIANCA ENERGIA ELETRICA SA             
DEBN TAEEC1_012027   DEBN TAEEC1 H649969                       10.879,59       0,00 10403 - Títulos Privados-Debêntures simples                  TAEE - TRANSMISSORA ALIANCA ENERGIA ELETRICA SA             
DEBN TAEEC1_012027   DEBN TAEEC1 H649969                      122.395,43       0,00 10403 - Títulos Privados-Debêntures simples                  TAEE - TRANSMISSORA ALIANCA ENERGIA ELETRICA SA             
DEBN TAEEC1_012027   DEBN TAEEC1 H649969                        8.159,70       0,00 10403 - Títulos Privados-Debêntures simples                  TAEE - TRANSMISSORA ALIANCA ENERGIA ELETRICA SA             
DEBN TAEEC1_012027   DEBN TAEEC1 H649969                        4.759,82       0,00 10403 - Títulos Privados-Debêntures simples                  TAEE - TRANSMISSORA ALIANCA ENERGIA ELETRICA SA             
DEBN TAEEC1_012027   DEBN TAEEC1 H649969                        7.479,72       0,00 10403 - Títulos Privados-Debêntures simples                  TAEE - TRANSMISSORA ALIANCA ENERGIA ELETRICA SA             
DEBN AEGPA0_052029   DEBN AEGPA0 H750651                        7.234,61       0,00 10440 - Títulos Privados-Debêntures Incent. (Lei 12.431)     AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN BRKPA1_032028   DEBN BRKPA1 I128038                       10.873,77       0,00 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN TAEEC1_012027   DEBN TAEEC1 H649969                        4.759,82       0,00 10403 - Títulos Privados-Debêntures simples                  TAEE - TRANSMISSORA ALIANCA ENERGIA ELETRICA SA             
DEBN TAEEC1_012027   DEBN TAEEC1 H649969                        5.439,80       0,00 10403 - Títulos Privados-Debêntures simples                  TAEE - TRANSMISSORA ALIANCA ENERGIA ELETRICA SA             
DEBN TAEEC1_012027   DEBN TAEEC1 H649969                    1.302.831,38       0,02 10403 - Títulos Privados-Debêntures simples                  TAEE - TRANSMISSORA ALIANCA ENERGIA ELETRICA SA             
DEBN TAEEC1_012027   DEBN TAEEC1 H649969                        2.719,90       0,00 10403 - Títulos Privados-Debêntures simples                  TAEE - TRANSMISSORA ALIANCA ENERGIA ELETRICA SA             
DEBN TAEEC1_012027   DEBN TAEEC1 H649969                       40.798,48       0,00 10403 - Títulos Privados-Debêntures simples                  TAEE - TRANSMISSORA ALIANCA ENERGIA ELETRICA SA             
DEBN TAEEC1_012027   DEBN TAEEC1 H649969                        6.119,77       0,00 10403 - Títulos Privados-Debêntures simples                  TAEE - TRANSMISSORA ALIANCA ENERGIA ELETRICA SA             
DEBN TAEEC1_012027   DEBN TAEEC1 H649969                        9.519,64       0,00 10403 - Títulos Privados-Debêntures simples                  TAEE - TRANSMISSORA ALIANCA ENERGIA ELETRICA SA             
DEBN TAEEC1_012027   DEBN TAEEC1 H649969                        1.359,95       0,00 10403 - Títulos Privados-Debêntures simples                  TAEE - TRANSMISSORA ALIANCA ENERGIA ELETRICA SA             
DEBN TAEEC1_012027   DEBN TAEEC1 H649969                        2.719,90       0,00 10403 - Títulos Privados-Debêntures simples                  TAEE - TRANSMISSORA ALIANCA ENERGIA ELETRICA SA             
DEBN TAEEC1_012027   DEBN TAEEC1 H649969                        5.439,80       0,00 10403 - Títulos Privados-Debêntures simples                  TAEE - TRANSMISSORA ALIANCA ENERGIA ELETRICA SA             
DEBN BRKPA1_032028   DEBN BRKPA1 I128038                        1.087,38       0,00 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN TAEEC1_012027   DEBN TAEEC1 H649969                        2.039,92       0,00 10403 - Títulos Privados-Debêntures simples                  TAEE - TRANSMISSORA ALIANCA ENERGIA ELETRICA SA             
DEBN UNDAC2_042027   DEBN UNDAC2                               10.411,43       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN UNDAC2_042027   DEBN UNDAC2                                2.082,29       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN UNDAC2_042027   DEBN UNDAC2                                7.288,00       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN UNDAC2_042027   DEBN UNDAC2                               12.493,71       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN UNDAC2_042027   DEBN UNDAC2                                9.370,28       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN UNDAC2_042027   DEBN UNDAC2                                5.205,71       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN UNDAC2_042027   DEBN UNDAC2                                5.205,71       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN UNDAC2_042027   DEBN UNDAC2                                3.123,43       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN UNDAC2_042027   DEBN UNDAC2                                2.082,29       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN BRKPA1_032028   DEBN BRKPA1 I128038                       17.398,03       0,00 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN UNDAC2_042027   DEBN UNDAC2                                8.329,14       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN UNDAC2_042027   DEBN UNDAC2                                4.164,57       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN UNDAC2_042027   DEBN UNDAC2                               65.591,99       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN UNDAC2_042027   DEBN UNDAC2                                8.329,14       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN UNDAC2_042027   DEBN UNDAC2                                9.370,28       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN UNDAC2_042027   DEBN UNDAC2                               10.411,43       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN UNDAC2_042027   DEBN UNDAC2                               13.534,86       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN UNDAC2_042027   DEBN UNDAC2                                1.041,14       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN UNDAC2_042027   DEBN UNDAC2                                8.329,14       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN UNDAC2_042027   DEBN UNDAC2                                4.164,57       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN BRKPA1_032028   DEBN BRKPA1 I128038                       34.796,05       0,00 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN UNDAC2_042027   DEBN UNDAC2                                8.329,14       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN UNDAC2_042027   DEBN UNDAC2                                1.041,14       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN UNDAC2_042027   DEBN UNDAC2                                1.041,14       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN UNDAC2_042027   DEBN UNDAC2                                2.082,29       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN UNDAC2_042027   DEBN UNDAC2                                1.041,14       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN UNDAC2_042027   DEBN UNDAC2                               10.411,43       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN UNDAC2_042027   DEBN UNDAC2                                2.082,29       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN UNDAC2_042027   DEBN UNDAC2                                5.205,71       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN UNDAC2_042027   DEBN UNDAC2                                2.082,29       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN UNDAC2_042027   DEBN UNDAC2                                6.246,86       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN BRKPA1_032028   DEBN BRKPA1 I128038                        4.349,51       0,00 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN UNDAC2_042027   DEBN UNDAC2                                6.246,86       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN UNDAC2_042027   DEBN UNDAC2                               14.576,00       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN UNDAC2_042027   DEBN UNDAC2                                7.288,00       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN UNDAC2_042027   DEBN UNDAC2                                5.205,71       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN UNDAC2_042027   DEBN UNDAC2                               30.193,14       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN UNDAC2_042027   DEBN UNDAC2                                1.041,14       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN UNDAC2_042027   DEBN UNDAC2                                7.288,00       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN UNDAC2_042027   DEBN UNDAC2                                7.288,00       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN UNDAC2_042027   DEBN UNDAC2                                3.123,43       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN UNDAC2_042027   DEBN UNDAC2                               45.810,28       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN BRKPA1_032028   DEBN BRKPA1 I128038                       34.796,06       0,00 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN UNDAC2_042027   DEBN UNDAC2                                2.082,29       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN UNDAC2_042027   DEBN UNDAC2                               20.822,86       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN UNDAC2_042027   DEBN UNDAC2                                3.123,43       0,00 10403 - Títulos Privados-Debêntures simples                  LCAM - COMPANHIA LOCACAO AMERICAS                           
DEBN UQFN15_062031   DEBN UQFN15 I904641                      108.428,20       0,00 10403 - Títulos Privados-Debêntures simples                  UQFN - UNIAO QUIMICA FARMACEUTICA NACIONAL SA               
DEBN UQFN15_062031   DEBN UQFN15 I904641                      262.199,11       0,00 10403 - Títulos Privados-Debêntures simples                  UQFN - UNIAO QUIMICA FARMACEUTICA NACIONAL SA               
DEBN UQFN15_062031   DEBN UQFN15 I904641                      261.213,40       0,00 10403 - Títulos Privados-Debêntures simples                  UQFN - UNIAO QUIMICA FARMACEUTICA NACIONAL SA               
DEBN UQFN15_062031   DEBN UQFN15 I904641                      203.056,45       0,00 10403 - Títulos Privados-Debêntures simples                  UQFN - UNIAO QUIMICA FARMACEUTICA NACIONAL SA               
DEBN UQFN15_062031   DEBN UQFN15 I904641                       12.814,24       0,00 10403 - Títulos Privados-Debêntures simples                  UQFN - UNIAO QUIMICA FARMACEUTICA NACIONAL SA               
DEBN UQFN15_062031   DEBN UQFN15 I904641                       75.899,74       0,00 10403 - Títulos Privados-Debêntures simples                  UQFN - UNIAO QUIMICA FARMACEUTICA NACIONAL SA               
DEBN UQFN15_062031   DEBN UQFN15 I904641                      227.699,23       0,00 10403 - Títulos Privados-Debêntures simples                  UQFN - UNIAO QUIMICA FARMACEUTICA NACIONAL SA               
DEBN BRKPA1_032028   DEBN BRKPA1 I128038                       30.446,54       0,00 10403 - Títulos Privados-Debêntures simples                  BRKP - BRK AMBIENTAL PARTICIPACOES S.A.                     
DEBN UQFN15_062031   DEBN UQFN15 I904641                      204.042,17       0,00 10403 - Títulos Privados-Debêntures simples                  UQFN - UNIAO QUIMICA FARMACEUTICA NACIONAL SA               
DEBN UQFN15_062031   DEBN UQFN15 I904641                      358.798,78       0,01 10403 - Títulos Privados-Debêntures simples                  UQFN - UNIAO QUIMICA FARMACEUTICA NACIONAL SA               
DEBN UQFN15_062031   DEBN UQFN15 I904641                      428.784,26       0,01 10403 - Títulos Privados-Debêntures simples                  UQFN - UNIAO QUIMICA FARMACEUTICA NACIONAL SA               
DEBN UQFN15_062031   DEBN UQFN15 I904641                      203.056,45       0,00 10403 - Títulos Privados-Debêntures simples                  UQFN - UNIAO QUIMICA FARMACEUTICA NACIONAL SA               
DEBN UQFN15_062031   DEBN UQFN15 I904641                      416.955,73       0,01 10403 - Títulos Privados-Debêntures simples                  UQFN - UNIAO QUIMICA FARMACEUTICA NACIONAL SA               
DEBN UQFN15_062031   DEBN UQFN15 I904641                      154.756,62       0,00 10403 - Títulos Privados-Debêntures simples                  UQFN - UNIAO QUIMICA FARMACEUTICA NACIONAL SA               
DEBN UQFN15_062031   DEBN UQFN15 I904641                       72.942,61       0,00 10403 - Títulos Privados-Debêntures simples                  UQFN - UNIAO QUIMICA FARMACEUTICA NACIONAL SA               
DEBN UQFN15_062031   DEBN UQFN15 I904641                      153.770,91       0,00 10403 - Títulos Privados-Debêntures simples                  UQFN - UNIAO QUIMICA FARMACEUTICA NACIONAL SA               
DEBN UQFN15_062031   DEBN UQFN15 I904641                      283.884,76       0,01 10403 - Títulos Privados-Debêntures simples                  UQFN - UNIAO QUIMICA FARMACEUTICA NACIONAL SA               
DEBN UQFN15_062031   DEBN UQFN15 I904641                      284.870,47       0,01 10403 - Títulos Privados-Debêntures simples                  UQFN - UNIAO QUIMICA FARMACEUTICA NACIONAL SA               
DEBN BVPL11_092028   DEBN BVPL11 I636945                       14.648,61       0,00 10403 - Títulos Privados-Debêntures simples                  BVPL - BORRACHAS VIPAL SA                                   
DEBN UQFN15_062031   DEBN UQFN15 I904641                       93.642,54       0,00 10403 - Títulos Privados-Debêntures simples                  UQFN - UNIAO QUIMICA FARMACEUTICA NACIONAL SA               
DEBN UQFN15_062031   DEBN UQFN15 I904641                       70.971,19       0,00 10403 - Títulos Privados-Debêntures simples                  UQFN - UNIAO QUIMICA FARMACEUTICA NACIONAL SA               
DEBN UQFN15_062031   DEBN UQFN15 I904641                    2.334.163,52       0,04 10403 - Títulos Privados-Debêntures simples                  UQFN - UNIAO QUIMICA FARMACEUTICA NACIONAL SA               
DEBN UQFN15_062031   DEBN UQFN15 I904641                      395.270,09       0,01 10403 - Títulos Privados-Debêntures simples                  UQFN - UNIAO QUIMICA FARMACEUTICA NACIONAL SA               
DEBN UQFN15_062031   DEBN UQFN15 I904641                       52.242,68       0,00 10403 - Títulos Privados-Debêntures simples                  UQFN - UNIAO QUIMICA FARMACEUTICA NACIONAL SA               
DEBN UQFN15_062031   DEBN UQFN15 I904641                      211.927,85       0,00 10403 - Títulos Privados-Debêntures simples                  UQFN - UNIAO QUIMICA FARMACEUTICA NACIONAL SA               
DEBN UQFN15_062031   DEBN UQFN15 I904641                      232.627,78       0,00 10403 - Títulos Privados-Debêntures simples                  UQFN - UNIAO QUIMICA FARMACEUTICA NACIONAL SA               
DEBN UQFN15_062031   DEBN UQFN15 I904641                   58.151.031,43       1,04 10403 - Títulos Privados-Debêntures simples                  UQFN - UNIAO QUIMICA FARMACEUTICA NACIONAL SA               
DEBN URBS17_032029   DEBN URBS17 I705514                       31.465,08       0,00 10403 - Títulos Privados-Debêntures simples                  URBS - URBA DESENVOLVIMENTO URBANO S.A.                     
DEBN URBS17_032029   DEBN URBS17 I705514                       53.490,63       0,00 10403 - Títulos Privados-Debêntures simples                  URBS - URBA DESENVOLVIMENTO URBANO S.A.                     
DEBN BVPL11_092028   DEBN BVPL11 I636945                       65.918,72       0,00 10403 - Títulos Privados-Debêntures simples                  BVPL - BORRACHAS VIPAL SA                                   
DEBN URBS17_032029   DEBN URBS17 I705514                       63.978,99       0,00 10403 - Títulos Privados-Debêntures simples                  URBS - URBA DESENVOLVIMENTO URBANO S.A.                     
DEBN URBS17_032029   DEBN URBS17 I705514                       54.539,47       0,00 10403 - Títulos Privados-Debêntures simples                  URBS - URBA DESENVOLVIMENTO URBANO S.A.                     
DEBN URBS17_032029   DEBN URBS17 I705514                       43.002,27       0,00 10403 - Títulos Privados-Debêntures simples                  URBS - URBA DESENVOLVIMENTO URBANO S.A.                     
DEBN URBS17_032029   DEBN URBS17 I705514                       43.002,27       0,00 10403 - Títulos Privados-Debêntures simples                  URBS - URBA DESENVOLVIMENTO URBANO S.A.                     
DEBN URBS17_032029   DEBN URBS17 I705514                       81.809,20       0,00 10403 - Títulos Privados-Debêntures simples                  URBS - URBA DESENVOLVIMENTO URBANO S.A.                     
DEBN URBS17_032029   DEBN URBS17 I705514                      936.610,48       0,02 10403 - Títulos Privados-Debêntures simples                  URBS - URBA DESENVOLVIMENTO URBANO S.A.                     
DEBN URBS17_032029   DEBN URBS17 I705514                       60.832,48       0,00 10403 - Títulos Privados-Debêntures simples                  URBS - URBA DESENVOLVIMENTO URBANO S.A.                     
DEBN URBS17_032029   DEBN URBS17 I705514                      123.762,64       0,00 10403 - Títulos Privados-Debêntures simples                  URBS - URBA DESENVOLVIMENTO URBANO S.A.                     
DEBN URBS17_032029   DEBN URBS17 I705514                      551.687,70       0,01 10403 - Títulos Privados-Debêntures simples                  URBS - URBA DESENVOLVIMENTO URBANO S.A.                     
DEBN URBS17_032029   DEBN URBS17 I705514                       92.297,56       0,00 10403 - Títulos Privados-Debêntures simples                  URBS - URBA DESENVOLVIMENTO URBANO S.A.                     
DEBN BVPL11_092028   DEBN BVPL11 I636945                       88.807,17       0,00 10403 - Títulos Privados-Debêntures simples                  BVPL - BORRACHAS VIPAL SA                                   
DEBN URBS17_032029   DEBN URBS17 I705514                       28.318,57       0,00 10403 - Títulos Privados-Debêntures simples                  URBS - URBA DESENVOLVIMENTO URBANO S.A.                     
DEBN URBS17_032029   DEBN URBS17 I705514                       23.074,39       0,00 10403 - Títulos Privados-Debêntures simples                  URBS - URBA DESENVOLVIMENTO URBANO S.A.                     
DEBN URBS17_032029   DEBN URBS17 I705514                       43.002,27       0,00 10403 - Títulos Privados-Debêntures simples                  URBS - URBA DESENVOLVIMENTO URBANO S.A.                     
DEBN URBS17_032029   DEBN URBS17 I705514                    3.288.100,63       0,06 10403 - Títulos Privados-Debêntures simples                  URBS - URBA DESENVOLVIMENTO URBANO S.A.                     
DEBN URBS17_032029   DEBN URBS17 I705514                      299.967,08       0,01 10403 - Títulos Privados-Debêntures simples                  URBS - URBA DESENVOLVIMENTO URBANO S.A.                     
DEBN URBS17_032029   DEBN URBS17 I705514                       47.197,62       0,00 10403 - Títulos Privados-Debêntures simples                  URBS - URBA DESENVOLVIMENTO URBANO S.A.                     
DEBN URBS17_032029   DEBN URBS17 I705514                      109.078,94       0,00 10403 - Títulos Privados-Debêntures simples                  URBS - URBA DESENVOLVIMENTO URBANO S.A.                     
DEBN URBS17_032029   DEBN URBS17 I705514                       35.660,42       0,00 10403 - Títulos Privados-Debêntures simples                  URBS - URBA DESENVOLVIMENTO URBANO S.A.                     
DEBN URBS17_032029   DEBN URBS17 I705514                       40.904,60       0,00 10403 - Títulos Privados-Debêntures simples                  URBS - URBA DESENVOLVIMENTO URBANO S.A.                     
DEBN URBS17_032029   DEBN URBS17 I705514                       43.002,27       0,00 10403 - Títulos Privados-Debêntures simples                  URBS - URBA DESENVOLVIMENTO URBANO S.A.                     
DEBN AEGPA0_052029   DEBN AEGPA0 H750651                        3.100,55       0,00 10440 - Títulos Privados-Debêntures Incent. (Lei 12.431)     AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN BVPL11_092028   DEBN BVPL11 I636945                      112.611,15       0,00 10403 - Títulos Privados-Debêntures simples                  BVPL - BORRACHAS VIPAL SA                                   
DEBN URBS17_032029   DEBN URBS17 I705514                      356.604,22       0,01 10403 - Títulos Privados-Debêntures simples                  URBS - URBA DESENVOLVIMENTO URBANO S.A.                     
DEBN URBS17_032029   DEBN URBS17 I705514                       17.830,21       0,00 10403 - Títulos Privados-Debêntures simples                  URBS - URBA DESENVOLVIMENTO URBANO S.A.                     
DEBN URBS17_032029   DEBN URBS17 I705514                      437.364,58       0,01 10403 - Títulos Privados-Debêntures simples                  URBS - URBA DESENVOLVIMENTO URBANO S.A.                     
DEBN URBS17_032029   DEBN URBS17 I705514                    1.508.226,06       0,03 10403 - Títulos Privados-Debêntures simples                  URBS - URBA DESENVOLVIMENTO URBANO S.A.                     
DEBN URBS17_032029   DEBN URBS17 I705514                    2.415.469,14       0,04 10403 - Títulos Privados-Debêntures simples                  URBS - URBA DESENVOLVIMENTO URBANO S.A.                     
DEBN URBS17_032029   DEBN URBS17 I705514                      657.620,13       0,01 10403 - Títulos Privados-Debêntures simples                  URBS - URBA DESENVOLVIMENTO URBANO S.A.                     
DEBN VAMO14_102028   DEBN VAMO14 I874556                       75.016,82       0,00 10403 - Títulos Privados-Debêntures simples                  VAMO - VAMOS LOCACAO DE CAMINHOES, MAQUINAS E EQUIPAMENTO   
DEBN VBBR14_112028   DEBN VBBR14 I146770A                      43.908,82       0,00 10403 - Títulos Privados-Debêntures simples                  VBBR - VIBRA ENERGIA SA                                     
DEBN VBBR14_112028   DEBN VBBR14 I146770A                     101.408,48       0,00 10403 - Títulos Privados-Debêntures simples                  VBBR - VIBRA ENERGIA SA                                     
DEBN VBBR14_112028   DEBN VBBR14 I146770A                      15.681,72       0,00 10403 - Títulos Privados-Debêntures simples                  VBBR - VIBRA ENERGIA SA                                     
DEBN BVPL11_092028   DEBN BVPL11 I636945                      108.949,00       0,00 10403 - Títulos Privados-Debêntures simples                  BVPL - BORRACHAS VIPAL SA                                   
DEBN VBBR14_112028   DEBN VBBR14 I146770A                     137.999,16       0,00 10403 - Títulos Privados-Debêntures simples                  VBBR - VIBRA ENERGIA SA                                     
DEBN VBBR14_112028   DEBN VBBR14 I146770A                     110.817,51       0,00 10403 - Títulos Privados-Debêntures simples                  VBBR - VIBRA ENERGIA SA                                     
DEBN VBBR14_112028   DEBN VBBR14 I146770A                      19.863,52       0,00 10403 - Títulos Privados-Debêntures simples                  VBBR - VIBRA ENERGIA SA                                     
DEBN VBBR14_112028   DEBN VBBR14 I146770A                      56.454,20       0,00 10403 - Títulos Privados-Debêntures simples                  VBBR - VIBRA ENERGIA SA                                     
DEBN VBBR14_112028   DEBN VBBR14 I146770A                      79.454,07       0,00 10403 - Títulos Privados-Debêntures simples                  VBBR - VIBRA ENERGIA SA                                     
DEBN VBBR14_112028   DEBN VBBR14 I146770A                      59.590,55       0,00 10403 - Títulos Privados-Debêntures simples                  VBBR - VIBRA ENERGIA SA                                     
DEBN VBBR14_112028   DEBN VBBR14 I146770A                      79.454,07       0,00 10403 - Títulos Privados-Debêntures simples                  VBBR - VIBRA ENERGIA SA                                     
DEBN VBBR14_112028   DEBN VBBR14 I146770A                      20.908,96       0,00 10403 - Títulos Privados-Debêntures simples                  VBBR - VIBRA ENERGIA SA                                     
DEBN VBBR14_112028   DEBN VBBR14 I146770A                      43.908,82       0,00 10403 - Títulos Privados-Debêntures simples                  VBBR - VIBRA ENERGIA SA                                     
DEBN VBBR14_112028   DEBN VBBR14 I146770A                      73.181,37       0,00 10403 - Títulos Privados-Debêntures simples                  VBBR - VIBRA ENERGIA SA                                     
DEBN BVPL11_092028   DEBN BVPL11 I636945                      129.090,83       0,00 10403 - Títulos Privados-Debêntures simples                  BVPL - BORRACHAS VIPAL SA                                   
DEBN VBBR14_112028   DEBN VBBR14 I146770A                      27.181,65       0,00 10403 - Títulos Privados-Debêntures simples                  VBBR - VIBRA ENERGIA SA                                     
DEBN VBBR14_112028   DEBN VBBR14 I146770A                      57.499,65       0,00 10403 - Títulos Privados-Debêntures simples                  VBBR - VIBRA ENERGIA SA                                     
DEBN VBBR14_112028   DEBN VBBR14 I146770A                      64.817,79       0,00 10403 - Títulos Privados-Debêntures simples                  VBBR - VIBRA ENERGIA SA                                     
DEBN VBBR14_112028   DEBN VBBR14 I146770A                      57.499,65       0,00 10403 - Títulos Privados-Debêntures simples                  VBBR - VIBRA ENERGIA SA                                     
DEBN VBBR14_112028   DEBN VBBR14 I146770A                      37.636,14       0,00 10403 - Títulos Privados-Debêntures simples                  VBBR - VIBRA ENERGIA SA                                     
DEBN VBBR14_112028   DEBN VBBR14 I146770A                   1.613.126,56       0,03 10403 - Títulos Privados-Debêntures simples                  VBBR - VIBRA ENERGIA SA                                     
DEBN VBBR14_112028   DEBN VBBR14 I146770A                      90.953,99       0,00 10403 - Títulos Privados-Debêntures simples                  VBBR - VIBRA ENERGIA SA                                     
DEBN VBBR14_112028   DEBN VBBR14 I146770A                  15.791.494,99       0,28 10403 - Títulos Privados-Debêntures simples                  VBBR - VIBRA ENERGIA SA                                     
DEBN VBBR14_112028   DEBN VBBR14 I146770A                       3.136,34       0,00 10403 - Títulos Privados-Debêntures simples                  VBBR - VIBRA ENERGIA SA                                     
DEBN VBBR14_112028   DEBN VBBR14 I146770A                      67.954,13       0,00 10403 - Títulos Privados-Debêntures simples                  VBBR - VIBRA ENERGIA SA                                     
DEBN BVPL11_092028   DEBN BVPL11 I636945                      113.526,69       0,00 10403 - Títulos Privados-Debêntures simples                  BVPL - BORRACHAS VIPAL SA                                   
DEBN VBBR14_112028   DEBN VBBR14 I146770A                     493.451,55       0,01 10403 - Títulos Privados-Debêntures simples                  VBBR - VIBRA ENERGIA SA                                     
DEBN VBBR14_112028   DEBN VBBR14 I146770A                   6.031.190,64       0,11 10403 - Títulos Privados-Debêntures simples                  VBBR - VIBRA ENERGIA SA                                     
DEBN VBBR14_112028   DEBN VBBR14 I146770A                     379.497,69       0,01 10403 - Títulos Privados-Debêntures simples                  VBBR - VIBRA ENERGIA SA                                     
DEBN VBBR14_112028   DEBN VBBR14 I146770A                     134.862,82       0,00 10403 - Títulos Privados-Debêntures simples                  VBBR - VIBRA ENERGIA SA                                     
DEBN VBBR14_112028   DEBN VBBR14 I146770A                      74.226,82       0,00 10403 - Títulos Privados-Debêntures simples                  VBBR - VIBRA ENERGIA SA                                     
DEBN VBBR14_112028   DEBN VBBR14 I146770A                      20.908,96       0,00 10403 - Títulos Privados-Debêntures simples                  VBBR - VIBRA ENERGIA SA                                     
DEBN VBBR14_112028   DEBN VBBR14 I146770A                      35.545,24       0,00 10403 - Títulos Privados-Debêntures simples                  VBBR - VIBRA ENERGIA SA                                     
DEBN VBBR24_112031   DEBN VBBR24 I133492                       53.523,27       0,00 10403 - Títulos Privados-Debêntures simples                  VBBR - VIBRA ENERGIA SA                                     
DEBN VBBR24_112031   DEBN VBBR24 I133492                      185.757,23       0,00 10403 - Títulos Privados-Debêntures simples                  VBBR - VIBRA ENERGIA SA                                     
DEBN VBBR24_112031   DEBN VBBR24 I133492                       52.473,79       0,00 10403 - Títulos Privados-Debêntures simples                  VBBR - VIBRA ENERGIA SA                                     
DEBN BVPL11_092028   DEBN BVPL11 I636945                      249.026,29       0,00 10403 - Títulos Privados-Debêntures simples                  BVPL - BORRACHAS VIPAL SA                                   
DEBN VBBR24_112031   DEBN VBBR24 I133492                       52.473,79       0,00 10403 - Títulos Privados-Debêntures simples                  VBBR - VIBRA ENERGIA SA                                     
DEBN VBBR24_112031   DEBN VBBR24 I133492                      143.778,19       0,00 10403 - Títulos Privados-Debêntures simples                  VBBR - VIBRA ENERGIA SA                                     
DEBN VBBR24_112031   DEBN VBBR24 I133492                      150.075,05       0,00 10403 - Títulos Privados-Debêntures simples                  VBBR - VIBRA ENERGIA SA                                     
DEBN VBBR24_112031   DEBN VBBR24 I133492                   17.206.156,61       0,31 10403 - Títulos Privados-Debêntures simples                  VBBR - VIBRA ENERGIA SA                                     
DEBN VBBR24_112031   DEBN VBBR24 I133492                      152.174,00       0,00 10403 - Títulos Privados-Debêntures simples                  VBBR - VIBRA ENERGIA SA                                     
DEBN VBBR24_112031   DEBN VBBR24 I133492                       50.374,84       0,00 10403 - Títulos Privados-Debêntures simples                  VBBR - VIBRA ENERGIA SA                                     
DEBN VBBR24_112031   DEBN VBBR24 I133492                      281.259,53       0,01 10403 - Títulos Privados-Debêntures simples                  VBBR - VIBRA ENERGIA SA                                     
DEBN VBBR24_112031   DEBN VBBR24 I133492                       30.434,80       0,00 10403 - Títulos Privados-Debêntures simples                  VBBR - VIBRA ENERGIA SA                                     
DEBN VBBR24_112031   DEBN VBBR24 I133492                        9.445,28       0,00 10403 - Títulos Privados-Debêntures simples                  VBBR - VIBRA ENERGIA SA                                     
DEBN VBBR24_112031   DEBN VBBR24 I133492                      340.030,17       0,01 10403 - Títulos Privados-Debêntures simples                  VBBR - VIBRA ENERGIA SA                                     
DEBN BVPL11_092028   DEBN BVPL11 I636945                       88.807,17       0,00 10403 - Títulos Privados-Debêntures simples                  BVPL - BORRACHAS VIPAL SA                                   
DEBN VBBR24_112031   DEBN VBBR24 I133492                      111.244,44       0,00 10403 - Títulos Privados-Debêntures simples                  VBBR - VIBRA ENERGIA SA                                     
DEBN VBBR24_112031   DEBN VBBR24 I133492                      252.923,68       0,00 10403 - Títulos Privados-Debêntures simples                  VBBR - VIBRA ENERGIA SA                                     
DEBN VBBR24_112031   DEBN VBBR24 I133492                       88.155,97       0,00 10403 - Títulos Privados-Debêntures simples                  VBBR - VIBRA ENERGIA SA                                     
DEBN VBBR24_112031   DEBN VBBR24 I133492                       66.116,98       0,00 10403 - Títulos Privados-Debêntures simples                  VBBR - VIBRA ENERGIA SA                                     
DEBN VBBR24_112031   DEBN VBBR24 I133492                      144.827,67       0,00 10403 - Títulos Privados-Debêntures simples                  VBBR - VIBRA ENERGIA SA                                     
DEBN VBBR24_112031   DEBN VBBR24 I133492                      108.096,01       0,00 10403 - Títulos Privados-Debêntures simples                  VBBR - VIBRA ENERGIA SA                                     
DEBN VBBR24_112031   DEBN VBBR24 I133492                      186.806,70       0,00 10403 - Títulos Privados-Debêntures simples                  VBBR - VIBRA ENERGIA SA                                     
DEBN VBBR24_112031   DEBN VBBR24 I133492                      162.668,76       0,00 10403 - Títulos Privados-Debêntures simples                  VBBR - VIBRA ENERGIA SA                                     
DEBN VBBR24_112031   DEBN VBBR24 I133492                      203.598,32       0,00 10403 - Títulos Privados-Debêntures simples                  VBBR - VIBRA ENERGIA SA                                     
DEBN VBBR24_112031   DEBN VBBR24 I133492                      202.548,84       0,00 10403 - Títulos Privados-Debêntures simples                  VBBR - VIBRA ENERGIA SA                                     
DEBN BVPL11_092028   DEBN BVPL11 I636945                       86.060,56       0,00 10403 - Títulos Privados-Debêntures simples                  BVPL - BORRACHAS VIPAL SA                                   
DEBN VBBR24_112031   DEBN VBBR24 I133492                      144.827,67       0,00 10403 - Títulos Privados-Debêntures simples                  VBBR - VIBRA ENERGIA SA                                     
DEBN VBBR24_112031   DEBN VBBR24 I133492                      348.425,98       0,01 10403 - Títulos Privados-Debêntures simples                  VBBR - VIBRA ENERGIA SA                                     
DEBN VVEO15_072027   DEBN VVEO15 I346092                       53.476,68       0,00 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN VVEO15_072027   DEBN VVEO15 I346092                      136.718,68       0,00 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN VVEO15_072027   DEBN VVEO15 I346092                       81.728,51       0,00 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN VVEO15_072027   DEBN VVEO15 I346092                      497.434,03       0,01 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN VVEO15_072027   DEBN VVEO15 I346092                    5.343.632,13       0,10 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN VVEO15_072027   DEBN VVEO15 I346092                      599.342,43       0,01 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN VVEO15_072027   DEBN VVEO15 I346092                       88.286,98       0,00 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN VVEO15_072027   DEBN VVEO15 I346092                      103.421,89       0,00 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN BVPL11_092028   DEBN BVPL11 I636945                        5.493,23       0,00 10403 - Títulos Privados-Debêntures simples                  BVPL - BORRACHAS VIPAL SA                                   
DEBN VVEO15_072027   DEBN VVEO15 I346092                       90.809,46       0,00 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN VVEO15_072027   DEBN VVEO15 I346092                       11.098,93       0,00 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN VVEO15_072027   DEBN VVEO15 I346092                      181.114,42       0,00 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN VVEO15_072027   DEBN VVEO15 I346092                    1.565.958,66       0,03 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN VVEO15_072027   DEBN VVEO15 I346092                       59.026,15       0,00 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN VVEO15_072027   DEBN VVEO15 I346092                          504,50       0,00 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN VVEO15_072027   DEBN VVEO15 I346092                      134.196,20       0,00 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN VVEO15_072027   DEBN VVEO15 I346092                       71.638,57       0,00 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN VVEO15_072027   DEBN VVEO15 I346092                       71.638,57       0,00 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN VVEO15_072027   DEBN VVEO15 I346092                       71.134,08       0,00 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN BVPL11_092028   DEBN BVPL11 I636945                    1.951.926,65       0,03 10403 - Títulos Privados-Debêntures simples                  BVPL - BORRACHAS VIPAL SA                                   
DEBN VVEO15_072027   DEBN VVEO15 I346092                       47.927,21       0,00 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN VVEO15_072027   DEBN VVEO15 I346092                       37.837,27       0,00 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN VVEO15_072027   DEBN VVEO15 I346092                       70.125,08       0,00 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN VVEO15_072027   DEBN VVEO15 I346092                      522.154,39       0,01 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN VVEO15_072027   DEBN VVEO15 I346092                       78.701,53       0,00 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN VVEO15_072027   DEBN VVEO15 I346092                       90.809,46       0,00 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN VVEO15_072027   DEBN VVEO15 I346092                       34.810,29       0,00 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN VVEO15_072027   DEBN VVEO15 I346092                    1.169.424,03       0,02 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN VVEO15_072027   DEBN VVEO15 I346092                       93.331,94       0,00 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN VVEO15_072027   DEBN VVEO15 I346092                       24.215,86       0,00 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN BVPL11_092028   DEBN BVPL11 I636945                      167.543,42       0,00 10403 - Títulos Privados-Debêntures simples                  BVPL - BORRACHAS VIPAL SA                                   
DEBN VVEO15_072027   DEBN VVEO15 I346092                    2.351.964,97       0,04 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN VVEO15_072027   DEBN VVEO15 I346092                      726.980,16       0,01 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN VVEO15_072027   DEBN VVEO15 I346092                    6.528.695,56       0,12 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN VVEO15_072027   DEBN VVEO15 I346092                       15.134,91       0,00 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN VVEO15_072027   DEBN VVEO15 I346092                    1.092.235,99       0,02 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN VVEO15_072027   DEBN VVEO15 I346092                       68.611,59       0,00 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN VVEO15_072027   DEBN VVEO15 I346092                      199.276,31       0,00 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN VVEO15_072027   DEBN VVEO15 I346092                        4.540,47       0,00 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN VVEO16_102027   DEBN VVEO16 I656609                      263.632,09       0,00 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN VVEO16_102027   DEBN VVEO16 I656609                        9.504,76       0,00 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN AEGPA0_052029   DEBN AEGPA0 H750651                       10.335,16       0,00 10440 - Títulos Privados-Debêntures Incent. (Lei 12.431)     AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN BVPL11_092028   DEBN BVPL11 I636945                       86.060,56       0,00 10403 - Títulos Privados-Debêntures simples                  BVPL - BORRACHAS VIPAL SA                                   
DEBN VVEO16_102027   DEBN VVEO16 I656609                       65.032,58       0,00 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN VVEO16_102027   DEBN VVEO16 I656609                        9.504,76       0,00 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN VVEO16_102027   DEBN VVEO16 I656609                        7.503,76       0,00 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN VVEO16_102027   DEBN VVEO16 I656609                      657.329,36       0,01 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN VVEO16_102027   DEBN VVEO16 I656609                       77.038,60       0,00 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN VVEO16_102027   DEBN VVEO16 I656609                      143.571,94       0,00 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN VVEO16_102027   DEBN VVEO16 I656609                        3.001,50       0,00 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN VVEO16_102027   DEBN VVEO16 I656609                       95.547,87       0,00 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN VVEO16_102027   DEBN VVEO16 I656609                      323.161,92       0,01 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN VVEO16_102027   DEBN VVEO16 I656609                       18.009,02       0,00 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN BVPL11_092028   DEBN BVPL11 I636945                      115.357,77       0,00 10403 - Títulos Privados-Debêntures simples                  BVPL - BORRACHAS VIPAL SA                                   
DEBN VVEO16_102027   DEBN VVEO16 I656609                        9.504,76       0,00 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN VVEO16_102027   DEBN VVEO16 I656609                       24.012,03       0,00 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN VVEO16_102027   DEBN VVEO16 I656609                       12.006,02       0,00 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN VVEO16_102027   DEBN VVEO16 I656609                        7.003,51       0,00 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN VVEO16_102027   DEBN VVEO16 I656609                       22.511,28       0,00 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN VVEO16_102027   DEBN VVEO16 I656609                       11.505,77       0,00 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN VVEO16_102027   DEBN VVEO16 I656609                       11.505,77       0,00 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN VVEO16_102027   DEBN VVEO16 I656609                        1.500,75       0,00 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN VVEO16_102027   DEBN VVEO16 I656609                        9.004,51       0,00 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN VVEO16_102027   DEBN VVEO16 I656609                      204.102,27       0,00 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN BVPL11_092028   DEBN BVPL11 I636945                       86.976,09       0,00 10403 - Títulos Privados-Debêntures simples                  BVPL - BORRACHAS VIPAL SA                                   
DEBN VVEO16_102027   DEBN VVEO16 I656609                       17.508,77       0,00 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN VVEO16_102027   DEBN VVEO16 I656609                       13.506,77       0,00 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN VVEO16_102027   DEBN VVEO16 I656609                       26.013,04       0,00 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN VVEO16_102027   DEBN VVEO16 I656609                          500,25       0,00 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN VVEO16_102027   DEBN VVEO16 I656609                       12.006,02       0,00 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN VVEO16_102027   DEBN VVEO16 I656609                        9.504,76       0,00 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN VVEO16_102027   DEBN VVEO16 I656609                       10.005,01       0,00 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN VVEO16_102027   DEBN VVEO16 I656609                       40.020,05       0,00 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN VVEO16_102027   DEBN VVEO16 I656609                        6.003,01       0,00 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN VVEO16_102027   DEBN VVEO16 I656609                        5.002,51       0,00 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN BVPL11_092028   DEBN BVPL11 I636945                      206.911,55       0,00 10403 - Títulos Privados-Debêntures simples                  BVPL - BORRACHAS VIPAL SA                                   
LF0021008AF 24062025 LF0021008AF 24062025 I302120              77.037,58       0,00 10435 - Titulos Privados-Letras Financeiras (LF)             BBDC - BCO BRADESCO SA                                      
LF0021008AF 24062025 LF0021008AF 24062025 I302120              77.037,58       0,00 10435 - Titulos Privados-Letras Financeiras (LF)             BBDC - BCO BRADESCO SA                                      
LF0021008AF 24062025 LF0021008AF 24062025 I302120              77.037,58       0,00 10435 - Titulos Privados-Letras Financeiras (LF)             BBDC - BCO BRADESCO SA                                      
LF0021008AF 24062025 LF0021008AF 24062025 I302120           2.850.390,41       0,05 10435 - Titulos Privados-Letras Financeiras (LF)             BBDC - BCO BRADESCO SA                                      
LF0021008AF 24062025 LF0021008AF 24062025 I302120              77.037,58       0,00 10435 - Titulos Privados-Letras Financeiras (LF)             BBDC - BCO BRADESCO SA                                      
LF0021008AF 24062025 LF0021008AF 24062025 I302120              77.037,58       0,00 10435 - Titulos Privados-Letras Financeiras (LF)             BBDC - BCO BRADESCO SA                                      
LF0021008AF 24062025 LF0021008AF 24062025 I302120             385.187,89       0,01 10435 - Titulos Privados-Letras Financeiras (LF)             BBDC - BCO BRADESCO SA                                      
LF0021008AF 24062025 LF0021008AF 24062025 I302120             308.150,31       0,01 10435 - Titulos Privados-Letras Financeiras (LF)             BBDC - BCO BRADESCO SA                                      
LF0021008AF 24062025 LF0021008AF 24062025 I302120              77.037,58       0,00 10435 - Titulos Privados-Letras Financeiras (LF)             BBDC - BCO BRADESCO SA                                      
LF0021008AF 24062025 LF0021008AF 24062025 I302120              77.037,58       0,00 10435 - Titulos Privados-Letras Financeiras (LF)             BBDC - BCO BRADESCO SA                                      
DEBN BVPL11_092028   DEBN BVPL11 I636945                       54.932,27       0,00 10403 - Títulos Privados-Debêntures simples                  BVPL - BORRACHAS VIPAL SA                                   
LF0021008AF 24062025 LF0021008AF 24062025 I302120             154.075,16       0,00 10435 - Titulos Privados-Letras Financeiras (LF)             BBDC - BCO BRADESCO SA                                      
LF0021008AH 24062025 LF0021008AH 24062025 I302077              77.037,58       0,00 10435 - Titulos Privados-Letras Financeiras (LF)             BBDC - BCO BRADESCO SA                                      
LF0021008AH 24062025 LF0021008AH 24062025 I302077             385.187,89       0,01 10435 - Titulos Privados-Letras Financeiras (LF)             BBDC - BCO BRADESCO SA                                      
LF0021008AH 24062025 LF0021008AH 24062025 I302077             308.150,31       0,01 10435 - Titulos Privados-Letras Financeiras (LF)             BBDC - BCO BRADESCO SA                                      
LF0021008AH 24062025 LF0021008AH 24062025 I302077           3.158.540,73       0,06 10435 - Titulos Privados-Letras Financeiras (LF)             BBDC - BCO BRADESCO SA                                      
LF0021008AH 24062025 LF0021008AH 24062025 I302077              77.037,58       0,00 10435 - Titulos Privados-Letras Financeiras (LF)             BBDC - BCO BRADESCO SA                                      
LF0021008AH 24062025 LF0021008AH 24062025 I302077              77.037,58       0,00 10435 - Titulos Privados-Letras Financeiras (LF)             BBDC - BCO BRADESCO SA                                      
LF0021008AH 24062025 LF0021008AH 24062025 I302077              77.037,58       0,00 10435 - Titulos Privados-Letras Financeiras (LF)             BBDC - BCO BRADESCO SA                                      
LF0021008AH 24062025 LF0021008AH 24062025 I302077              77.037,58       0,00 10435 - Titulos Privados-Letras Financeiras (LF)             BBDC - BCO BRADESCO SA                                      
LF0021008AI 24062025 LF0021008AI 24062025 I302122             231.112,74       0,00 10435 - Titulos Privados-Letras Financeiras (LF)             BBDC - BCO BRADESCO SA                                      
DEBN BVPL11_092028   DEBN BVPL11 I636945                      156.556,97       0,00 10403 - Títulos Privados-Debêntures simples                  BVPL - BORRACHAS VIPAL SA                                   
LF0021008AI 24062025 LF0021008AI 24062025 I302122              77.037,58       0,00 10435 - Titulos Privados-Letras Financeiras (LF)             BBDC - BCO BRADESCO SA                                      
LF0021008B2 24062025 LF0021008B2 24062025 I302133              77.037,58       0,00 10435 - Titulos Privados-Letras Financeiras (LF)             BBDC - BCO BRADESCO SA                                      
LF0021008B2 24062025 LF0021008B2 24062025 I302133              77.037,58       0,00 10435 - Titulos Privados-Letras Financeiras (LF)             BBDC - BCO BRADESCO SA                                      
LF0021008B2 24062025 LF0021008B2 24062025 I302133             693.338,21       0,01 10435 - Titulos Privados-Letras Financeiras (LF)             BBDC - BCO BRADESCO SA                                      
LF0022003G5 01022027 LF0022003G5 01022027 I302103              75.007,71       0,00 10435 - Titulos Privados-Letras Financeiras (LF)             BBDC - BCO BRADESCO SA                                      
LF0022003G5 01022027 LF0022003G5 01022027 I302103              75.007,71       0,00 10435 - Titulos Privados-Letras Financeiras (LF)             BBDC - BCO BRADESCO SA                                      
LF0022003G5 01022027 LF0022003G5 01022027 I302103             150.015,42       0,00 10435 - Titulos Privados-Letras Financeiras (LF)             BBDC - BCO BRADESCO SA                                      
LF0022003G5 01022027 LF0022003G5 01022027 I302103             150.015,42       0,00 10435 - Titulos Privados-Letras Financeiras (LF)             BBDC - BCO BRADESCO SA                                      
LF0022003G5 01022027 LF0022003G5 01022027 I302103              75.007,71       0,00 10435 - Titulos Privados-Letras Financeiras (LF)             BBDC - BCO BRADESCO SA                                      
LF0022003G5 01022027 LF0022003G5 01022027 I302103              75.007,71       0,00 10435 - Titulos Privados-Letras Financeiras (LF)             BBDC - BCO BRADESCO SA                                      
DEBN BVPL11_092028   DEBN BVPL11 I636945                       47.607,97       0,00 10403 - Títulos Privados-Debêntures simples                  BVPL - BORRACHAS VIPAL SA                                   
LF0022003G5 01022027 LF0022003G5 01022027 I302103              75.007,71       0,00 10435 - Titulos Privados-Letras Financeiras (LF)             BBDC - BCO BRADESCO SA                                      
LF0022003G5 01022027 LF0022003G5 01022027 I302103              75.007,71       0,00 10435 - Titulos Privados-Letras Financeiras (LF)             BBDC - BCO BRADESCO SA                                      
LF0022003G5 01022027 LF0022003G5 01022027 I302103              75.007,71       0,00 10435 - Titulos Privados-Letras Financeiras (LF)             BBDC - BCO BRADESCO SA                                      
LF0022003G5 01022027 LF0022003G5 01022027 I302103              75.007,71       0,00 10435 - Titulos Privados-Letras Financeiras (LF)             BBDC - BCO BRADESCO SA                                      
LF0022003G5 01022027 LF0022003G5 01022027 I302103             225.023,12       0,00 10435 - Titulos Privados-Letras Financeiras (LF)             BBDC - BCO BRADESCO SA                                      
LF0022003G5 01022027 LF0022003G5 01022027 I302103           6.300.647,23       0,11 10435 - Titulos Privados-Letras Financeiras (LF)             BBDC - BCO BRADESCO SA                                      
LF0022003G5 01022027 LF0022003G5 01022027 I302103             150.015,41       0,00 10435 - Titulos Privados-Letras Financeiras (LF)             BBDC - BCO BRADESCO SA                                      
LF0022003G5 01022027 LF0022003G5 01022027 I302103             600.061,64       0,01 10435 - Titulos Privados-Letras Financeiras (LF)             BBDC - BCO BRADESCO SA                                      
LF0022003G5 01022027 LF0022003G5 01022027 I302103              75.007,71       0,00 10435 - Titulos Privados-Letras Financeiras (LF)             BBDC - BCO BRADESCO SA                                      
LF0022003G5 01022027 LF0022003G5 01022027 I302103             825.084,76       0,01 10435 - Titulos Privados-Letras Financeiras (LF)             BBDC - BCO BRADESCO SA                                      
DEBN BVPL11_092028   DEBN BVPL11 I636945                       97.962,55       0,00 10403 - Títulos Privados-Debêntures simples                  BVPL - BORRACHAS VIPAL SA                                   
LF0022003G5 01022027 LF0022003G5 01022027 I302103              75.007,71       0,00 10435 - Titulos Privados-Letras Financeiras (LF)             BBDC - BCO BRADESCO SA                                      
LF002307IJ6 09102025 LF002307IJ6 09102025 I448541              60.084,77       0,00 10435 - Titulos Privados-Letras Financeiras (LF)             AGBK - BANCO AGIBANK S.A.                                   
LF002307IJ6 09102025 LF002307IJ6 09102025 I448541              60.084,77       0,00 10435 - Titulos Privados-Letras Financeiras (LF)             AGBK - BANCO AGIBANK S.A.                                   
LF002307IJ6 09102025 LF002307IJ6 09102025 I448541             120.169,54       0,00 10435 - Titulos Privados-Letras Financeiras (LF)             AGBK - BANCO AGIBANK S.A.                                   
LF002307IJ6 09102025 LF002307IJ6 09102025 I448541              60.084,77       0,00 10435 - Titulos Privados-Letras Financeiras (LF)             AGBK - BANCO AGIBANK S.A.                                   
LF002307IJ6 09102025 LF002307IJ6 09102025 I448541             120.169,54       0,00 10435 - Titulos Privados-Letras Financeiras (LF)             AGBK - BANCO AGIBANK S.A.                                   
LF002307IJ6 09102025 LF002307IJ6 09102025 I448541          10.454.749,55       0,19 10435 - Titulos Privados-Letras Financeiras (LF)             AGBK - BANCO AGIBANK S.A.                                   
LF002307IJ6 09102025 LF002307IJ6 09102025 I448541             120.169,54       0,00 10435 - Titulos Privados-Letras Financeiras (LF)             AGBK - BANCO AGIBANK S.A.                                   
LF002307IJ6 09102025 LF002307IJ6 09102025 I448541              60.084,77       0,00 10435 - Titulos Privados-Letras Financeiras (LF)             AGBK - BANCO AGIBANK S.A.                                   
LF002308HPR 30112026 LF002308HPR 30112026 I563028             117.901,62       0,00 10435 - Titulos Privados-Letras Financeiras (LF)             AGBK - BANCO AGIBANK S.A.                                   
DEBN BVPL11_092028   DEBN BVPL11 I636945                      693.062,14       0,01 10403 - Títulos Privados-Debêntures simples                  BVPL - BORRACHAS VIPAL SA                                   
LF002308HPR 30112026 LF002308HPR 30112026 I563028           3.949.704,49       0,07 10435 - Titulos Privados-Letras Financeiras (LF)             AGBK - BANCO AGIBANK S.A.                                   
LF002308I16 03122026 LF002308I16 03122026 I564907             117.788,72       0,00 10435 - Titulos Privados-Letras Financeiras (LF)             AGBK - BANCO AGIBANK S.A.                                   
LF0024002HE 19012026 LF0024002HE 19012026 J213386         100.179.250,31       1,79 10435 - Titulos Privados-Letras Financeiras (LF)             BBDC - BCO BRADESCO SA                                      
LF0024002HE 19012026 LF0024002HE 19012026 J213386          10.124.797,84       0,18 10435 - Titulos Privados-Letras Financeiras (LF)             BBDC - BCO BRADESCO SA                                      
LF0024002OK 22012026 LF0024002OK 22012026 J213631          90.092.280,34       1,61 10435 - Titulos Privados-Letras Financeiras (LF)             BBDC - BCO BRADESCO SA                                      
LF002400BWI 29042027 LF002400BWI 29042027 I762608              55.757,18       0,00 10435 - Titulos Privados-Letras Financeiras (LF)             AGBK - BANCO AGIBANK S.A.                                   
LF002400BWI 29042027 LF002400BWI 29042027 I762608           1.561.201,03       0,03 10435 - Titulos Privados-Letras Financeiras (LF)             AGBK - BANCO AGIBANK S.A.                                   
LF002400BWI 29042027 LF002400BWI 29042027 I762608           6.021.775,38       0,11 10435 - Titulos Privados-Letras Financeiras (LF)             AGBK - BANCO AGIBANK S.A.                                   
LF002400BWI 29042027 LF002400BWI 29042027 I762608              55.757,18       0,00 10435 - Titulos Privados-Letras Financeiras (LF)             AGBK - BANCO AGIBANK S.A.                                   
LF002400DFI 17052027 LF002400DFI 17052027 I790953             773.648,83       0,01 10435 - Titulos Privados-Letras Financeiras (LF)             AGBK - BANCO AGIBANK S.A.                                   
DEBN CAMLA1_102028   DEBN CAMLA1 I601775                        1.029,97       0,00 10403 - Títulos Privados-Debêntures simples                  CAML - CAMIL ALIMENTOS SA                                   
LF002400DFO 17052027 LF002400DFO 17052027 I790939             110.521,26       0,00 10435 - Titulos Privados-Letras Financeiras (LF)             AGBK - BANCO AGIBANK S.A.                                   
LF002400DFP 17052027 LF002400DFP 17052027 I790947             276.303,15       0,00 10435 - Titulos Privados-Letras Financeiras (LF)             AGBK - BANCO AGIBANK S.A.                                   
LF002400DFQ 17052027 LF002400DFQ 17052027 I790946             663.127,57       0,01 10435 - Titulos Privados-Letras Financeiras (LF)             AGBK - BANCO AGIBANK S.A.                                   
LF002400DFR 17052027 LF002400DFR 17052027 I790940             221.042,52       0,00 10435 - Titulos Privados-Letras Financeiras (LF)             AGBK - BANCO AGIBANK S.A.                                   
LF002400DFS 17052027 LF002400DFS 17052027 I790943             276.303,15       0,00 10435 - Titulos Privados-Letras Financeiras (LF)             AGBK - BANCO AGIBANK S.A.                                   
LF002400DFT 17052027 LF002400DFT 17052027 I790945             994.691,36       0,02 10435 - Titulos Privados-Letras Financeiras (LF)             AGBK - BANCO AGIBANK S.A.                                   
LF002400DFU 17052027 LF002400DFU 17052027 I790944           9.062.743,48       0,16 10435 - Titulos Privados-Letras Financeiras (LF)             AGBK - BANCO AGIBANK S.A.                                   
LF002400DFV 17052027 LF002400DFV 17052027 I790941           2.984.074,07       0,05 10435 - Titulos Privados-Letras Financeiras (LF)             AGBK - BANCO AGIBANK S.A.                                   
LF002400DFW 17052027 LF002400DFW 17052027 I790950             110.521,26       0,00 10435 - Titulos Privados-Letras Financeiras (LF)             AGBK - BANCO AGIBANK S.A.                                   
LF002400DFX 17052027 LF002400DFX 17052027 I790952              55.260,63       0,00 10435 - Titulos Privados-Letras Financeiras (LF)             AGBK - BANCO AGIBANK S.A.                                   
DEBN AEGPA0_052029   DEBN AEGPA0 H750651                       10.335,16       0,00 10440 - Títulos Privados-Debêntures Incent. (Lei 12.431)     AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN CAMLA1_102028   DEBN CAMLA1 I601775                        1.029,97       0,00 10403 - Títulos Privados-Debêntures simples                  CAML - CAMIL ALIMENTOS SA                                   
LF002400DFY 17052027 LF002400DFY 17052027 I790942              55.260,63       0,00 10435 - Titulos Privados-Letras Financeiras (LF)             AGBK - BANCO AGIBANK S.A.                                   
LF002400DFZ 17052027 LF002400DFZ 17052027 I790951             165.781,89       0,00 10435 - Titulos Privados-Letras Financeiras (LF)             AGBK - BANCO AGIBANK S.A.                                   
LF002400DFZ 17052027 LF002400DFZ 17052027 I790951           1.602.558,30       0,03 10435 - Titulos Privados-Letras Financeiras (LF)             AGBK - BANCO AGIBANK S.A.                                   
LFSN21001YT 16062031 LFSN21001YT 16062031 H655901           1.984.616,90       0,04 10437 - Letras Financeiras Subordinadas (LFS)                BBDC - BCO BRADESCO SA                                      
LFSN21001YT 16062031 LFSN21001YT 16062031 H655901             496.154,22       0,01 10437 - Letras Financeiras Subordinadas (LFS)                BBDC - BCO BRADESCO SA                                      
LFSN21001YT 16062031 LFSN21001YT 16062031 H655901           1.488.462,67       0,03 10437 - Letras Financeiras Subordinadas (LFS)                BBDC - BCO BRADESCO SA                                      
LFSN21001YT 16062031 LFSN21001YT 16062031 H655901             496.154,22       0,01 10437 - Letras Financeiras Subordinadas (LFS)                BBDC - BCO BRADESCO SA                                      
LFSN21001YT 16062031 LFSN21001YT 16062031 H655901             496.154,22       0,01 10437 - Letras Financeiras Subordinadas (LFS)                BBDC - BCO BRADESCO SA                                      
LFSN21001YT 16062031 LFSN21001YT 16062031 H655901           1.488.462,67       0,03 10437 - Letras Financeiras Subordinadas (LFS)                BBDC - BCO BRADESCO SA                                      
LFSN21001YT 16062031 LFSN21001YT 16062031 H655901             496.154,22       0,01 10437 - Letras Financeiras Subordinadas (LFS)                BBDC - BCO BRADESCO SA                                      
DEBN CAMLA1_102028   DEBN CAMLA1 I601775                        1.029,97       0,00 10403 - Títulos Privados-Debêntures simples                  CAML - CAMIL ALIMENTOS SA                                   
LFSN210028Q 08072031 LFSN210028Q 08072031 I153073             494.509,95       0,01 10437 - Letras Financeiras Subordinadas (LFS)                BBDC - BCO BRADESCO SA                                      
LFSN210028Q 08072031 LFSN210028Q 08072031 I153073             494.509,95       0,01 10437 - Letras Financeiras Subordinadas (LFS)                BBDC - BCO BRADESCO SA                                      
LFSN210028Q 08072031 LFSN210028Q 08072031 I153073             494.509,95       0,01 10437 - Letras Financeiras Subordinadas (LFS)                BBDC - BCO BRADESCO SA                                      
LFSN210028Q 08072031 LFSN210028Q 08072031 I153073             494.509,95       0,01 10437 - Letras Financeiras Subordinadas (LFS)                BBDC - BCO BRADESCO SA                                      
LFSN210028Q 08072031 LFSN210028Q 08072031 I153073             494.509,95       0,01 10437 - Letras Financeiras Subordinadas (LFS)                BBDC - BCO BRADESCO SA                                      
LFSN21006SX 04112031 LFSN21006SX 04112031 I528889             959.280,98       0,02 10437 - Letras Financeiras Subordinadas (LFS)                BBDC - BCO BRADESCO SA                                      
LFSN21006SX 04112031 LFSN21006SX 04112031 I528889             479.640,49       0,01 10437 - Letras Financeiras Subordinadas (LFS)                BBDC - BCO BRADESCO SA                                      
LFSN21006SX 04112031 LFSN21006SX 04112031 I528889           1.438.921,47       0,03 10437 - Letras Financeiras Subordinadas (LFS)                BBDC - BCO BRADESCO SA                                      
LFSN21006SX 04112031 LFSN21006SX 04112031 I528889             959.280,98       0,02 10437 - Letras Financeiras Subordinadas (LFS)                BBDC - BCO BRADESCO SA                                      
LFSN2100742 10112031 LFSN2100742 10112031                     479.373,73       0,01 10437 - Letras Financeiras Subordinadas (LFS)                BBDC - BCO BRADESCO SA                                      
DEBN CAMLA1_102028   DEBN CAMLA1 I601775                       36.048,87       0,00 10403 - Títulos Privados-Debêntures simples                  CAML - CAMIL ALIMENTOS SA                                   
LFSN2100742 10112031 LFSN2100742 10112031                     479.373,73       0,01 10437 - Letras Financeiras Subordinadas (LFS)                BBDC - BCO BRADESCO SA                                      
LFSN2100742 10112031 LFSN2100742 10112031                     479.373,73       0,01 10437 - Letras Financeiras Subordinadas (LFS)                BBDC - BCO BRADESCO SA                                      
LFSN2100742 10112031 LFSN2100742 10112031                     479.373,73       0,01 10437 - Letras Financeiras Subordinadas (LFS)                BBDC - BCO BRADESCO SA                                      
LFSN2100742 10112031 LFSN2100742 10112031                     479.373,73       0,01 10437 - Letras Financeiras Subordinadas (LFS)                BBDC - BCO BRADESCO SA                                      
LFSN2100742 10112031 LFSN2100742 10112031                     479.373,73       0,01 10437 - Letras Financeiras Subordinadas (LFS)                BBDC - BCO BRADESCO SA                                      
LFSN2100742 10112031 LFSN2100742 10112031                     479.373,73       0,01 10437 - Letras Financeiras Subordinadas (LFS)                BBDC - BCO BRADESCO SA                                      
LFSN2100742 10112031 LFSN2100742 10112031                     479.373,73       0,01 10437 - Letras Financeiras Subordinadas (LFS)                BBDC - BCO BRADESCO SA                                      
LFSN2100742 10112031 LFSN2100742 10112031                     479.373,73       0,01 10437 - Letras Financeiras Subordinadas (LFS)                BBDC - BCO BRADESCO SA                                      
LFSN2100742 10112031 LFSN2100742 10112031                     479.373,73       0,01 10437 - Letras Financeiras Subordinadas (LFS)                BBDC - BCO BRADESCO SA                                      
LFSN2100742 10112031 LFSN2100742 10112031                   1.438.121,20       0,03 10437 - Letras Financeiras Subordinadas (LFS)                BBDC - BCO BRADESCO SA                                      
DEBN CAMLA1_102028   DEBN CAMLA1 I601775                        7.209,77       0,00 10403 - Títulos Privados-Debêntures simples                  CAML - CAMIL ALIMENTOS SA                                   
LFSN22002S3 16032032 LFSN22002S3 16032032 H692228           1.387.250,78       0,02 10437 - Letras Financeiras Subordinadas (LFS)                BBDC - BCO BRADESCO SA                                      
LFSN22002S3 16032032 LFSN22002S3 16032032 H692228             924.833,86       0,02 10437 - Letras Financeiras Subordinadas (LFS)                BBDC - BCO BRADESCO SA                                      
LFSN22002S3 16032032 LFSN22002S3 16032032 H692228             462.416,93       0,01 10437 - Letras Financeiras Subordinadas (LFS)                BBDC - BCO BRADESCO SA                                      
LFSN22002S3 16032032 LFSN22002S3 16032032 H692228             462.416,93       0,01 10437 - Letras Financeiras Subordinadas (LFS)                BBDC - BCO BRADESCO SA                                      
LFSN22002S3 16032032 LFSN22002S3 16032032 H692228             462.416,93       0,01 10437 - Letras Financeiras Subordinadas (LFS)                BBDC - BCO BRADESCO SA                                      
LFSN22002S3 16032032 LFSN22002S3 16032032 H692228             462.416,93       0,01 10437 - Letras Financeiras Subordinadas (LFS)                BBDC - BCO BRADESCO SA                                      
LFSN22002S3 16032032 LFSN22002S3 16032032 H692228             462.416,93       0,01 10437 - Letras Financeiras Subordinadas (LFS)                BBDC - BCO BRADESCO SA                                      
LFSN22002S3 16032032 LFSN22002S3 16032032 H692228             462.416,93       0,01 10437 - Letras Financeiras Subordinadas (LFS)                BBDC - BCO BRADESCO SA                                      
LFSN22002S3 16032032 LFSN22002S3 16032032 H692228             462.416,93       0,01 10437 - Letras Financeiras Subordinadas (LFS)                BBDC - BCO BRADESCO SA                                      
LFSN22002S3 16032032 LFSN22002S3 16032032 H692228             462.416,93       0,01 10437 - Letras Financeiras Subordinadas (LFS)                BBDC - BCO BRADESCO SA                                      
DEBN CAMLA1_102028   DEBN CAMLA1 I601775                        1.029,97       0,00 10403 - Títulos Privados-Debêntures simples                  CAML - CAMIL ALIMENTOS SA                                   
LFSN22002S3 16032032 LFSN22002S3 16032032 H692228             462.416,93       0,01 10437 - Letras Financeiras Subordinadas (LFS)                BBDC - BCO BRADESCO SA                                      
LFSN22002S3 16032032 LFSN22002S3 16032032 H692228             462.416,93       0,01 10437 - Letras Financeiras Subordinadas (LFS)                BBDC - BCO BRADESCO SA                                      
LFSN22002S3 16032032 LFSN22002S3 16032032 H692228           1.387.250,78       0,02 10437 - Letras Financeiras Subordinadas (LFS)                BBDC - BCO BRADESCO SA                                      
LFSN22002S3 16032032 LFSN22002S3 16032032 H692228             462.416,93       0,01 10437 - Letras Financeiras Subordinadas (LFS)                BBDC - BCO BRADESCO SA                                      
LFSN22002S3 16032032 LFSN22002S3 16032032 H692228           1.387.250,78       0,02 10437 - Letras Financeiras Subordinadas (LFS)                BBDC - BCO BRADESCO SA                                      
LFSN22002S3 16032032 LFSN22002S3 16032032 H692228             924.833,86       0,02 10437 - Letras Financeiras Subordinadas (LFS)                BBDC - BCO BRADESCO SA                                      
LFSN22002S3 16032032 LFSN22002S3 16032032 H692228             924.833,86       0,02 10437 - Letras Financeiras Subordinadas (LFS)                BBDC - BCO BRADESCO SA                                      
LFSN22002S4 16032032 LFSN22002S4 16032032 H692229             462.416,93       0,01 10437 - Letras Financeiras Subordinadas (LFS)                BBDC - BCO BRADESCO SA                                      
LFSN22002S4 16032032 LFSN22002S4 16032032 H692229             462.416,93       0,01 10437 - Letras Financeiras Subordinadas (LFS)                BBDC - BCO BRADESCO SA                                      
LFSN22002S4 16032032 LFSN22002S4 16032032 H692229             462.416,93       0,01 10437 - Letras Financeiras Subordinadas (LFS)                BBDC - BCO BRADESCO SA                                      
DEBN CAMLA1_102028   DEBN CAMLA1 I601775                        1.029,97       0,00 10403 - Títulos Privados-Debêntures simples                  CAML - CAMIL ALIMENTOS SA                                   
LFSN22002S5 16032032 LFSN22002S5 16032032 H692227             462.416,93       0,01 10437 - Letras Financeiras Subordinadas (LFS)                BBDC - BCO BRADESCO SA                                      
LFSN22002S5 16032032 LFSN22002S5 16032032 H692227             462.416,93       0,01 10437 - Letras Financeiras Subordinadas (LFS)                BBDC - BCO BRADESCO SA                                      
LFSN22002S9 16032032 LFSN22002S9 16032032 H692234             462.416,93       0,01 10437 - Letras Financeiras Subordinadas (LFS)                BBDC - BCO BRADESCO SA                                      
LFSN2200FN1 15122032 LFSN2200FN1 15122032 I1941               316.748,27       0,01 10437 - Letras Financeiras Subordinadas (LFS)                BCXP - BANCO XP S.A                                         
LFSN2200FN1 15122032 LFSN2200FN1 15122032 I1941               316.748,27       0,01 10437 - Letras Financeiras Subordinadas (LFS)                BCXP - BANCO XP S.A                                         
LFSN2200FN7 15122032 LFSN2200FN7 15122032 I1940               316.748,27       0,01 10437 - Letras Financeiras Subordinadas (LFS)                BCXP - BANCO XP S.A                                         
LFSN2200FN7 15122032 LFSN2200FN7 15122032 I1940               316.748,27       0,01 10437 - Letras Financeiras Subordinadas (LFS)                BCXP - BANCO XP S.A                                         
LFSN2200FNK 15122032 LFSN2200FNK 15122032 I2131               316.748,27       0,01 10437 - Letras Financeiras Subordinadas (LFS)                BCXP - BANCO XP S.A                                         
LFSN2200FNK 15122032 LFSN2200FNK 15122032 I2131               316.748,27       0,01 10437 - Letras Financeiras Subordinadas (LFS)                BCXP - BANCO XP S.A                                         
LFSN2200FNK 15122032 LFSN2200FNK 15122032 I2131               316.748,27       0,01 10437 - Letras Financeiras Subordinadas (LFS)                BCXP - BANCO XP S.A                                         
DEBN CAMLA1_102028   DEBN CAMLA1 I601775                       61.798,07       0,00 10403 - Títulos Privados-Debêntures simples                  CAML - CAMIL ALIMENTOS SA                                   
LFSN2200FNK 15122032 LFSN2200FNK 15122032 I2131               316.748,27       0,01 10437 - Letras Financeiras Subordinadas (LFS)                BCXP - BANCO XP S.A                                         
LFSN2200FNM 15122032 LFSN2200FNM 15122032 I2001               633.496,53       0,01 10437 - Letras Financeiras Subordinadas (LFS)                BCXP - BANCO XP S.A                                         
LFSN2200FNM 15122032 LFSN2200FNM 15122032 I2001               316.748,27       0,01 10437 - Letras Financeiras Subordinadas (LFS)                BCXP - BANCO XP S.A                                         
LFSN2200FNM 15122032 LFSN2200FNM 15122032 I2001               316.748,27       0,01 10437 - Letras Financeiras Subordinadas (LFS)                BCXP - BANCO XP S.A                                         
LFSN2200FNM 15122032 LFSN2200FNM 15122032 I2001               316.748,27       0,01 10437 - Letras Financeiras Subordinadas (LFS)                BCXP - BANCO XP S.A                                         
LFSN2200FNM 15122032 LFSN2200FNM 15122032 I2001               316.748,27       0,01 10437 - Letras Financeiras Subordinadas (LFS)                BCXP - BANCO XP S.A                                         
LFSN2200FNO 15122032 LFSN2200FNO 15122032 I2005               316.748,27       0,01 10437 - Letras Financeiras Subordinadas (LFS)                BCXP - BANCO XP S.A                                         
LFSN2200FNO 15122032 LFSN2200FNO 15122032 I2005               316.748,27       0,01 10437 - Letras Financeiras Subordinadas (LFS)                BCXP - BANCO XP S.A                                         
LFSN2200FNO 15122032 LFSN2200FNO 15122032 I2005               316.748,27       0,01 10437 - Letras Financeiras Subordinadas (LFS)                BCXP - BANCO XP S.A                                         
LFSN2200FNO 15122032 LFSN2200FNO 15122032 I2005               316.748,27       0,01 10437 - Letras Financeiras Subordinadas (LFS)                BCXP - BANCO XP S.A                                         
DEBN CAMLA1_102028   DEBN CAMLA1 I601775                        1.029,97       0,00 10403 - Títulos Privados-Debêntures simples                  CAML - CAMIL ALIMENTOS SA                                   
LFSN2200FNR 15122032 LFSN2200FNR 15122032 I1946               316.748,27       0,01 10437 - Letras Financeiras Subordinadas (LFS)                BCXP - BANCO XP S.A                                         
LFSN2200FNR 15122032 LFSN2200FNR 15122032 I1946               633.496,53       0,01 10437 - Letras Financeiras Subordinadas (LFS)                BCXP - BANCO XP S.A                                         
LFSN2200FNS 15122032 LFSN2200FNS 15122032 I1955               316.748,27       0,01 10437 - Letras Financeiras Subordinadas (LFS)                BCXP - BANCO XP S.A                                         
LFSN2200FNS 15122032 LFSN2200FNS 15122032 I1955               633.496,53       0,01 10437 - Letras Financeiras Subordinadas (LFS)                BCXP - BANCO XP S.A                                         
LFSN2200FNS 15122032 LFSN2200FNS 15122032 I1955             1.583.741,33       0,03 10437 - Letras Financeiras Subordinadas (LFS)                BCXP - BANCO XP S.A                                         
LFSN2200FNS 15122032 LFSN2200FNS 15122032 I1955               316.748,27       0,01 10437 - Letras Financeiras Subordinadas (LFS)                BCXP - BANCO XP S.A                                         
LFSN2200FNY 15122032 LFSN2200FNY 15122032 I1949               316.748,27       0,01 10437 - Letras Financeiras Subordinadas (LFS)                BCXP - BANCO XP S.A                                         
LFSN2200FNY 15122032 LFSN2200FNY 15122032 I1949               316.748,27       0,01 10437 - Letras Financeiras Subordinadas (LFS)                BCXP - BANCO XP S.A                                         
LFSN2200FNY 15122032 LFSN2200FNY 15122032 I1949               316.748,27       0,01 10437 - Letras Financeiras Subordinadas (LFS)                BCXP - BANCO XP S.A                                         
LFSN2200FNY 15122032 LFSN2200FNY 15122032 I1949               633.496,54       0,01 10437 - Letras Financeiras Subordinadas (LFS)                BCXP - BANCO XP S.A                                         
DEBN CAMLA1_102028   DEBN CAMLA1 I601775                        1.029,97       0,00 10403 - Títulos Privados-Debêntures simples                  CAML - CAMIL ALIMENTOS SA                                   
LFSN2200FNY 15122032 LFSN2200FNY 15122032 I1949               316.748,27       0,01 10437 - Letras Financeiras Subordinadas (LFS)                BCXP - BANCO XP S.A                                         
LFSN2200FOD 15122032 LFSN2200FOD 15122032 I3976               316.748,27       0,01 10437 - Letras Financeiras Subordinadas (LFS)                BCXP - BANCO XP S.A                                         
LFSN2200FOD 15122032 LFSN2200FOD 15122032 I3976               316.748,27       0,01 10437 - Letras Financeiras Subordinadas (LFS)                BCXP - BANCO XP S.A                                         
LFSN2200FOM 15122032 LFSN2200FOM 15122032 I1956            24.389.616,55       0,44 10437 - Letras Financeiras Subordinadas (LFS)                BCXP - BANCO XP S.A                                         
LFSN2200FOM 15122032 LFSN2200FOM 15122032 I1956               316.748,27       0,01 10437 - Letras Financeiras Subordinadas (LFS)                BCXP - BANCO XP S.A                                         
LFSN2200FOM 15122032 LFSN2200FOM 15122032 I1956               316.748,27       0,01 10437 - Letras Financeiras Subordinadas (LFS)                BCXP - BANCO XP S.A                                         
LFSN2200FSK 16122032 LFSN2200FSK 16122032 I3972               633.521,94       0,01 10437 - Letras Financeiras Subordinadas (LFS)                BCXP - BANCO XP S.A                                         
LFSN2200FSK 16122032 LFSN2200FSK 16122032 I3972               633.521,94       0,01 10437 - Letras Financeiras Subordinadas (LFS)                BCXP - BANCO XP S.A                                         
LFSN2200FSK 16122032 LFSN2200FSK 16122032 I3972             1.583.804,84       0,03 10437 - Letras Financeiras Subordinadas (LFS)                BCXP - BANCO XP S.A                                         
LFSN2200FSK 16122032 LFSN2200FSK 16122032 I3972               633.521,94       0,01 10437 - Letras Financeiras Subordinadas (LFS)                BCXP - BANCO XP S.A                                         
DEBN CAMLA1_102028   DEBN CAMLA1 I601775                        2.059,94       0,00 10403 - Títulos Privados-Debêntures simples                  CAML - CAMIL ALIMENTOS SA                                   
LFSN2200FSK 16122032 LFSN2200FSK 16122032 I3972             1.267.043,88       0,02 10437 - Letras Financeiras Subordinadas (LFS)                BCXP - BANCO XP S.A                                         
LFSN2200FSK 16122032 LFSN2200FSK 16122032 I3972               316.760,97       0,01 10437 - Letras Financeiras Subordinadas (LFS)                BCXP - BANCO XP S.A                                         
LFSN2200FSK 16122032 LFSN2200FSK 16122032 I3972               316.760,97       0,01 10437 - Letras Financeiras Subordinadas (LFS)                BCXP - BANCO XP S.A                                         
LFSN2200FSK 16122032 LFSN2200FSK 16122032 I3972               633.521,94       0,01 10437 - Letras Financeiras Subordinadas (LFS)                BCXP - BANCO XP S.A                                         
LFSN2200FSK 16122032 LFSN2200FSK 16122032 I3972               633.521,94       0,01 10437 - Letras Financeiras Subordinadas (LFS)                BCXP - BANCO XP S.A                                         
LFSN2200FSK 16122032 LFSN2200FSK 16122032 I3972             2.534.087,75       0,05 10437 - Letras Financeiras Subordinadas (LFS)                BCXP - BANCO XP S.A                                         
LFSN2200FSK 16122032 LFSN2200FSK 16122032 I3972               316.760,97       0,01 10437 - Letras Financeiras Subordinadas (LFS)                BCXP - BANCO XP S.A                                         
LFSN2200FSK 16122032 LFSN2200FSK 16122032 I3972               633.521,94       0,01 10437 - Letras Financeiras Subordinadas (LFS)                BCXP - BANCO XP S.A                                         
LFT 01032027         LFT 01032027                          84.229.138,30       1,51 10106 - Títulos Púb Federais-LFTs-Definitivo                 STNC - SECRETARIA TESOURO NACIONAL                          
LFT 01032027         LFT 01032027                             239.969,05       0,00 10106 - Títulos Púb Federais-LFTs-Definitivo                 STNC - SECRETARIA TESOURO NACIONAL                          
DEBN AEGPA0_052029   DEBN AEGPA0 H750651                        4.134,06       0,00 10440 - Títulos Privados-Debêntures Incent. (Lei 12.431)     AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN CAMLA1_102028   DEBN CAMLA1 I601775                        2.059,94       0,00 10403 - Títulos Privados-Debêntures simples                  CAML - CAMIL ALIMENTOS SA                                   
LFT 01032027         LFT 01032027                             239.969,05       0,00 10106 - Títulos Púb Federais-LFTs-Definitivo                 STNC - SECRETARIA TESOURO NACIONAL                          
LFT 01032027         LFT 01032027                         112.241.525,98       2,01 10106 - Títulos Púb Federais-LFTs-Definitivo                 STNC - SECRETARIA TESOURO NACIONAL                          
LFT 01032028         LFT 01032028 H629313A                 82.713.302,92       1,48 10106 - Títulos Púb Federais-LFTs-Definitivo                 STNC - SECRETARIA TESOURO NACIONAL                          
LFT 01032028         LFT 01032028 H629313A                     79.900,79       0,00 10106 - Títulos Púb Federais-LFTs-Definitivo                 STNC - SECRETARIA TESOURO NACIONAL                          
LFT 01032029         LFT 01032029 K676785A                318.808.564,51       5,70 10106 - Títulos Púb Federais-LFTs-Definitivo                 STNC - SECRETARIA TESOURO NACIONAL                          
LFT 01032029         LFT 01032029 K676785A                 59.856.307,99       1,07 10106 - Títulos Púb Federais-LFTs-Definitivo                 STNC - SECRETARIA TESOURO NACIONAL                          
COTA:BR0CGZCTF021    FIDC BULLLA CARTOES (3A SERIE         25.301.655,47       0,45 30000 - Cotas de Fundos                                       -                                                          
COTA:BR0ENECTF036    FIDC ALION III CONSIGNADOS (CO        30.458.886,47       0,54 30000 - Cotas de Fundos                                       -                                                          
COTA:BR0FWRCTF044    GREEN SOLFACIL III FIDC                6.279.211,20       0,11 30000 - Cotas de Fundos                                       -                                                          
COTA:BR0G3RCTF001    INDIGO FIAGRO (COTA SENIOR)            9.947.585,62       0,18 30000 - Cotas de Fundos                                       -                                                          
DEBN CAMLA1_102028   DEBN CAMLA1 I601775                        3.089,90       0,00 10403 - Títulos Privados-Debêntures simples                  CAML - CAMIL ALIMENTOS SA                                   
COTA:BR0GLSCTF019    SOMACRED CONSIGNADO PÚBLICO II        26.087.082,48       0,47 30000 - Cotas de Fundos                                       -                                                          
COTA:BR0HXQCTF024    FIDC CREDITAS AUTO X – RESP LM        27.157.994,73       0,49 30000 - Cotas de Fundos                                       -                                                          
COTA:BR0IRQCTF008    CLOUDWALK BIG PICTURE IV FIDC         52.883.247,73       0,95 30000 - Cotas de Fundos                                       -                                                          
DEBN CAMLA1_102028   DEBN CAMLA1 I601775                      105.056,73       0,00 10403 - Títulos Privados-Debêntures simples                  CAML - CAMIL ALIMENTOS SA                                   
DEBN CAMLA1_102028   DEBN CAMLA1 I601775                        9.269,71       0,00 10403 - Títulos Privados-Debêntures simples                  CAML - CAMIL ALIMENTOS SA                                   
DEBN CAMLA1_102028   DEBN CAMLA1 I601775                        1.029,97       0,00 10403 - Títulos Privados-Debêntures simples                  CAML - CAMIL ALIMENTOS SA                                   
DEBN CAMLA1_102028   DEBN CAMLA1 I601775                        1.029,97       0,00 10403 - Títulos Privados-Debêntures simples                  CAML - CAMIL ALIMENTOS SA                                   
DEBN CEAB11_052025   DEBN CEAB11 I156897                       65.589,56       0,00 10403 - Títulos Privados-Debêntures simples                  CEAB - C&A MODAS S.A.                                       
DEBN CEAB11_052025   DEBN CEAB11 I156897                       69.204,73       0,00 10403 - Títulos Privados-Debêntures simples                  CEAB - C&A MODAS S.A.                                       
DEBN CEAB11_052025   DEBN CEAB11 I156897                      130.662,66       0,00 10403 - Títulos Privados-Debêntures simples                  CEAB - C&A MODAS S.A.                                       
DEBN CEAB11_052025   DEBN CEAB11 I156897                        3.098,72       0,00 10403 - Títulos Privados-Debêntures simples                  CEAB - C&A MODAS S.A.                                       
DEBN AEGPA0_052029   DEBN AEGPA0 H750651                       91.982,90       0,00 10440 - Títulos Privados-Debêntures Incent. (Lei 12.431)     AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN CEAB11_052025   DEBN CEAB11 I156897                       50.612,41       0,00 10403 - Títulos Privados-Debêntures simples                  CEAB - C&A MODAS S.A.                                       
DEBN CEAB11_052025   DEBN CEAB11 I156897                       38.217,54       0,00 10403 - Títulos Privados-Debêntures simples                  CEAB - C&A MODAS S.A.                                       
DEBN CEAB11_052025   DEBN CEAB11 I156897                       99.675,47       0,00 10403 - Títulos Privados-Debêntures simples                  CEAB - C&A MODAS S.A.                                       
DEBN CEAB11_052025   DEBN CEAB11 I156897                       51.645,32       0,00 10403 - Títulos Privados-Debêntures simples                  CEAB - C&A MODAS S.A.                                       
DEBN CEAB11_052025   DEBN CEAB11 I156897                       49.579,51       0,00 10403 - Títulos Privados-Debêntures simples                  CEAB - C&A MODAS S.A.                                       
DEBN CEAB11_052025   DEBN CEAB11 I156897                       33.569,46       0,00 10403 - Títulos Privados-Debêntures simples                  CEAB - C&A MODAS S.A.                                       
DEBN CEAB11_052025   DEBN CEAB11 I156897                       73.852,81       0,00 10403 - Títulos Privados-Debêntures simples                  CEAB - C&A MODAS S.A.                                       
DEBN CEAB11_052025   DEBN CEAB11 I156897                       71.786,99       0,00 10403 - Títulos Privados-Debêntures simples                  CEAB - C&A MODAS S.A.                                       
DEBN CEAB11_052025   DEBN CEAB11 I156897                    1.849.418,90       0,03 10403 - Títulos Privados-Debêntures simples                  CEAB - C&A MODAS S.A.                                       
DEBN CEAB11_052025   DEBN CEAB11 I156897                       52.678,23       0,00 10403 - Títulos Privados-Debêntures simples                  CEAB - C&A MODAS S.A.                                       
DEBN AEGPA3_032026   DEBN AEGPA3 I109165                       72.285,28       0,00 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN CEAB11_052025   DEBN CEAB11 I156897                      317.618,72       0,01 10403 - Títulos Privados-Debêntures simples                  CEAB - C&A MODAS S.A.                                       
DEBN CEAB11_052025   DEBN CEAB11 I156897                       69.204,73       0,00 10403 - Títulos Privados-Debêntures simples                  CEAB - C&A MODAS S.A.                                       
DEBN CEAB11_052025   DEBN CEAB11 I156897                    1.448.651,22       0,03 10403 - Títulos Privados-Debêntures simples                  CEAB - C&A MODAS S.A.                                       
DEBN CEAB11_052025   DEBN CEAB11 I156897                          516,45       0,00 10403 - Títulos Privados-Debêntures simples                  CEAB - C&A MODAS S.A.                                       
DEBN CEAB11_052025   DEBN CEAB11 I156897                       98.126,11       0,00 10403 - Títulos Privados-Debêntures simples                  CEAB - C&A MODAS S.A.                                       
DEBN CEAB11_052025   DEBN CEAB11 I156897                       56.809,85       0,00 10403 - Títulos Privados-Debêntures simples                  CEAB - C&A MODAS S.A.                                       
DEBN CEAB11_052025   DEBN CEAB11 I156897                       58.359,21       0,00 10403 - Títulos Privados-Debêntures simples                  CEAB - C&A MODAS S.A.                                       
DEBN CEAB11_052025   DEBN CEAB11 I156897                    5.036.968,04       0,09 10403 - Títulos Privados-Debêntures simples                  CEAB - C&A MODAS S.A.                                       
DEBN CEAB11_052025   DEBN CEAB11 I156897                      472.038,22       0,01 10403 - Títulos Privados-Debêntures simples                  CEAB - C&A MODAS S.A.                                       
DEBN CEAB11_052025   DEBN CEAB11 I156897                      866.608,47       0,02 10403 - Títulos Privados-Debêntures simples                  CEAB - C&A MODAS S.A.                                       
CRI_CRA024002GX      CRI_CRA024002GX CRA  I666020              20.536,61       0,00 10444 - Títulos Privados-Certif.Receb. Agronegócio (CRA)     CASC - CANAL COMPANHIA DE SECURITIZACAO                     
DEBN AEGPA3_032026   DEBN AEGPA3 I109165                      133.940,38       0,00 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN CEAB11_052025   DEBN CEAB11 I156897                       13.427,78       0,00 10403 - Títulos Privados-Debêntures simples                  CEAB - C&A MODAS S.A.                                       
DEBN CEAB11_052025   DEBN CEAB11 I156897                       49.063,05       0,00 10403 - Títulos Privados-Debêntures simples                  CEAB - C&A MODAS S.A.                                       
DEBN CEAB11_052025   DEBN CEAB11 I156897                    1.874.208,66       0,03 10403 - Títulos Privados-Debêntures simples                  CEAB - C&A MODAS S.A.                                       
DEBN CEAB11_052025   DEBN CEAB11 I156897                       51.645,32       0,00 10403 - Títulos Privados-Debêntures simples                  CEAB - C&A MODAS S.A.                                       
DEBN CEAB11_052025   DEBN CEAB11 I156897                        8.779,70       0,00 10403 - Títulos Privados-Debêntures simples                  CEAB - C&A MODAS S.A.                                       
DEBN CEAB12_112025   DEBN CEAB12 I590347                       16.549,05       0,00 10403 - Títulos Privados-Debêntures simples                  CEAB - C&A MODAS S.A.                                       
DEBN CEAB12_112025   DEBN CEAB12 I590347                       23.789,26       0,00 10403 - Títulos Privados-Debêntures simples                  CEAB - C&A MODAS S.A.                                       
DEBN CEAB12_112025   DEBN CEAB12 I590347                       15.514,73       0,00 10403 - Títulos Privados-Debêntures simples                  CEAB - C&A MODAS S.A.                                       
DEBN CEAB12_112025   DEBN CEAB12 I590347                        1.034,32       0,00 10403 - Títulos Privados-Debêntures simples                  CEAB - C&A MODAS S.A.                                       
DEBN CEAB12_112025   DEBN CEAB12 I590347                       12.411,79       0,00 10403 - Títulos Privados-Debêntures simples                  CEAB - C&A MODAS S.A.                                       
DEBN AEGPA3_032026   DEBN AEGPA3 I109165                       92.482,64       0,00 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN CEAB12_112025   DEBN CEAB12 I590347                        3.102,95       0,00 10403 - Títulos Privados-Debêntures simples                  CEAB - C&A MODAS S.A.                                       
DEBN CEAB12_112025   DEBN CEAB12 I590347                       16.549,05       0,00 10403 - Títulos Privados-Debêntures simples                  CEAB - C&A MODAS S.A.                                       
DEBN CEAB12_112025   DEBN CEAB12 I590347                       15.514,73       0,00 10403 - Títulos Privados-Debêntures simples                  CEAB - C&A MODAS S.A.                                       
DEBN CEAB12_112025   DEBN CEAB12 I590347                       16.549,05       0,00 10403 - Títulos Privados-Debêntures simples                  CEAB - C&A MODAS S.A.                                       
DEBN CEAB12_112025   DEBN CEAB12 I590347                    1.786.262,93       0,03 10403 - Títulos Privados-Debêntures simples                  CEAB - C&A MODAS S.A.                                       
DEBN CEAB12_112025   DEBN CEAB12 I590347                        8.274,52       0,00 10403 - Títulos Privados-Debêntures simples                  CEAB - C&A MODAS S.A.                                       
DEBN CEAB12_112025   DEBN CEAB12 I590347                      525.432,29       0,01 10403 - Títulos Privados-Debêntures simples                  CEAB - C&A MODAS S.A.                                       
DEBN CEAB12_112025   DEBN CEAB12 I590347                        9.308,84       0,00 10403 - Títulos Privados-Debêntures simples                  CEAB - C&A MODAS S.A.                                       
DEBN CEAB12_112025   DEBN CEAB12 I590347                       40.338,31       0,00 10403 - Títulos Privados-Debêntures simples                  CEAB - C&A MODAS S.A.                                       
DEBN CEAB12_112025   DEBN CEAB12 I590347                      336.152,55       0,01 10403 - Títulos Privados-Debêntures simples                  CEAB - C&A MODAS S.A.                                       
DEBN AEGPA3_032026   DEBN AEGPA3 I109165                        4.252,08       0,00 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN CEAB12_112025   DEBN CEAB12 I590347                      137.563,97       0,00 10403 - Títulos Privados-Debêntures simples                  CEAB - C&A MODAS S.A.                                       
DEBN CEAB12_112025   DEBN CEAB12 I590347                    1.493.551,64       0,03 10403 - Títulos Privados-Debêntures simples                  CEAB - C&A MODAS S.A.                                       
DEBN CEAB12_112025   DEBN CEAB12 I590347                      112.740,39       0,00 10403 - Títulos Privados-Debêntures simples                  CEAB - C&A MODAS S.A.                                       
DEBN CEAB12_112025   DEBN CEAB12 I590347                       20.686,31       0,00 10403 - Títulos Privados-Debêntures simples                  CEAB - C&A MODAS S.A.                                       
DEBN CEAB12_112025   DEBN CEAB12 I590347                       20.686,31       0,00 10403 - Títulos Privados-Debêntures simples                  CEAB - C&A MODAS S.A.                                       
DEBN CEAB12_112025   DEBN CEAB12 I590347                      620.589,33       0,01 10403 - Títulos Privados-Debêntures simples                  CEAB - C&A MODAS S.A.                                       
DEBN CEAB12_112025   DEBN CEAB12 I590347                       18.617,68       0,00 10403 - Títulos Privados-Debêntures simples                  CEAB - C&A MODAS S.A.                                       
DEBN CEAB12_112025   DEBN CEAB12 I590347                       32.063,78       0,00 10403 - Títulos Privados-Debêntures simples                  CEAB - C&A MODAS S.A.                                       
DEBN CEAB12_112025   DEBN CEAB12 I590347                       16.549,05       0,00 10403 - Títulos Privados-Debêntures simples                  CEAB - C&A MODAS S.A.                                       
DEBN CEAB12_112025   DEBN CEAB12 I590347                       20.686,31       0,00 10403 - Títulos Privados-Debêntures simples                  CEAB - C&A MODAS S.A.                                       
DEBN AEGPA3_032026   DEBN AEGPA3 I109165                       68.033,21       0,00 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN CEAB12_112025   DEBN CEAB12 I590347                       11.377,47       0,00 10403 - Títulos Privados-Debêntures simples                  CEAB - C&A MODAS S.A.                                       
DEBN CEAB12_112025   DEBN CEAB12 I590347                       11.377,47       0,00 10403 - Títulos Privados-Debêntures simples                  CEAB - C&A MODAS S.A.                                       
DEBN CEAB12_112025   DEBN CEAB12 I590347                       29.995,15       0,00 10403 - Títulos Privados-Debêntures simples                  CEAB - C&A MODAS S.A.                                       
DEBN CEAB12_112025   DEBN CEAB12 I590347                       22.754,94       0,00 10403 - Títulos Privados-Debêntures simples                  CEAB - C&A MODAS S.A.                                       
DEBN CEAB12_112025   DEBN CEAB12 I590347                       12.411,79       0,00 10403 - Títulos Privados-Debêntures simples                  CEAB - C&A MODAS S.A.                                       
DEBN CEAB12_112025   DEBN CEAB12 I590347                      248.235,73       0,00 10403 - Títulos Privados-Debêntures simples                  CEAB - C&A MODAS S.A.                                       
DEBN CEAB22_052028   DEBN CEAB22 I514841                       14.570,90       0,00 10403 - Títulos Privados-Debêntures simples                  CEAB - C&A MODAS S.A.                                       
DEBN CEAB22_052028   DEBN CEAB22 I514841                        8.326,23       0,00 10403 - Títulos Privados-Debêntures simples                  CEAB - C&A MODAS S.A.                                       
DEBN CEAB22_052028   DEBN CEAB22 I514841                       11.448,57       0,00 10403 - Títulos Privados-Debêntures simples                  CEAB - C&A MODAS S.A.                                       
DEBN CEAB22_052028   DEBN CEAB22 I514841                        2.081,56       0,00 10403 - Títulos Privados-Debêntures simples                  CEAB - C&A MODAS S.A.                                       
DEBN AEGPA3_032026   DEBN AEGPA3 I109165                     -265.754,72       0,00 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN CEAB22_052028   DEBN CEAB22 I514841                       15.611,68       0,00 10403 - Títulos Privados-Debêntures simples                  CEAB - C&A MODAS S.A.                                       
DEBN CEAB22_052028   DEBN CEAB22 I514841                        9.367,01       0,00 10403 - Títulos Privados-Debêntures simples                  CEAB - C&A MODAS S.A.                                       
DEBN CEAB22_052028   DEBN CEAB22 I514841                       16.652,46       0,00 10403 - Títulos Privados-Debêntures simples                  CEAB - C&A MODAS S.A.                                       
DEBN CEAB22_052028   DEBN CEAB22 I514841                       11.448,57       0,00 10403 - Títulos Privados-Debêntures simples                  CEAB - C&A MODAS S.A.                                       
DEBN CEAB22_052028   DEBN CEAB22 I514841                      389.251,27       0,01 10403 - Títulos Privados-Debêntures simples                  CEAB - C&A MODAS S.A.                                       
DEBN CEAB22_052028   DEBN CEAB22 I514841                       11.448,57       0,00 10403 - Títulos Privados-Debêntures simples                  CEAB - C&A MODAS S.A.                                       
DEBN CEAB22_052028   DEBN CEAB22 I514841                        8.326,23       0,00 10403 - Títulos Privados-Debêntures simples                  CEAB - C&A MODAS S.A.                                       
DEBN CEAB22_052028   DEBN CEAB22 I514841                      241.460,68       0,00 10403 - Títulos Privados-Debêntures simples                  CEAB - C&A MODAS S.A.                                       
DEBN CEAB22_052028   DEBN CEAB22 I514841                       22.897,13       0,00 10403 - Títulos Privados-Debêntures simples                  CEAB - C&A MODAS S.A.                                       
DEBN CEAB22_052028   DEBN CEAB22 I514841                       17.693,24       0,00 10403 - Títulos Privados-Debêntures simples                  CEAB - C&A MODAS S.A.                                       
DEBN AEGPA3_032026   DEBN AEGPA3 I109165                      198.784,53       0,00 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN CEAB22_052028   DEBN CEAB22 I514841                       13.530,12       0,00 10403 - Títulos Privados-Debêntures simples                  CEAB - C&A MODAS S.A.                                       
DEBN CEAB22_052028   DEBN CEAB22 I514841                        1.040,78       0,00 10403 - Títulos Privados-Debêntures simples                  CEAB - C&A MODAS S.A.                                       
DEBN CEAB22_052028   DEBN CEAB22 I514841                       14.570,90       0,00 10403 - Títulos Privados-Debêntures simples                  CEAB - C&A MODAS S.A.                                       
DEBN CEAB22_052028   DEBN CEAB22 I514841                       11.448,57       0,00 10403 - Títulos Privados-Debêntures simples                  CEAB - C&A MODAS S.A.                                       
DEBN CEAB22_052028   DEBN CEAB22 I514841                       14.570,90       0,00 10403 - Títulos Privados-Debêntures simples                  CEAB - C&A MODAS S.A.                                       
DEBN CEDO13_072029   DEBN CEDO13 I894317                      117.095,66       0,00 10403 - Títulos Privados-Debêntures simples                  CEDO - CIA FIACAO TECIDOS CEDRO CACHOEIRA                   
DEBN CEDO13_072029   DEBN CEDO13 I894317                    1.211.990,08       0,02 10403 - Títulos Privados-Debêntures simples                  CEDO - CIA FIACAO TECIDOS CEDRO CACHOEIRA                   
DEBN CEDO13_072029   DEBN CEDO13 I894317                    1.257.026,87       0,02 10403 - Títulos Privados-Debêntures simples                  CEDO - CIA FIACAO TECIDOS CEDRO CACHOEIRA                   
DEBN CEDO13_072029   DEBN CEDO13 I894317                       29.023,71       0,00 10403 - Títulos Privados-Debêntures simples                  CEDO - CIA FIACAO TECIDOS CEDRO CACHOEIRA                   
DEBN CEDO13_072029   DEBN CEDO13 I894317                       37.030,25       0,00 10403 - Títulos Privados-Debêntures simples                  CEDO - CIA FIACAO TECIDOS CEDRO CACHOEIRA                   
DEBN AEGPA3_032026   DEBN AEGPA3 I109165                       83.978,49       0,00 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN CEDO13_072029   DEBN CEDO13 I894317                       60.049,05       0,00 10403 - Títulos Privados-Debêntures simples                  CEDO - CIA FIACAO TECIDOS CEDRO CACHOEIRA                   
DEBN CEDO13_072029   DEBN CEDO13 I894317                      139.113,64       0,00 10403 - Títulos Privados-Debêntures simples                  CEDO - CIA FIACAO TECIDOS CEDRO CACHOEIRA                   
DEBN CEDO13_072029   DEBN CEDO13 I894317                      157.128,36       0,00 10403 - Títulos Privados-Debêntures simples                  CEDO - CIA FIACAO TECIDOS CEDRO CACHOEIRA                   
DEBN CEDO13_072029   DEBN CEDO13 I894317                       52.042,51       0,00 10403 - Títulos Privados-Debêntures simples                  CEDO - CIA FIACAO TECIDOS CEDRO CACHOEIRA                   
DEBN CEDO13_072029   DEBN CEDO13 I894317                       78.063,77       0,00 10403 - Títulos Privados-Debêntures simples                  CEDO - CIA FIACAO TECIDOS CEDRO CACHOEIRA                   
DEBN CEDO13_072029   DEBN CEDO13 I894317                       79.064,59       0,00 10403 - Títulos Privados-Debêntures simples                  CEDO - CIA FIACAO TECIDOS CEDRO CACHOEIRA                   
DEBN CEDO13_072029   DEBN CEDO13 I894317                       78.063,77       0,00 10403 - Títulos Privados-Debêntures simples                  CEDO - CIA FIACAO TECIDOS CEDRO CACHOEIRA                   
DEBN CEDO13_072029   DEBN CEDO13 I894317                   18.132.812,74       0,32 10403 - Títulos Privados-Debêntures simples                  CEDO - CIA FIACAO TECIDOS CEDRO CACHOEIRA                   
DEBN CEDO13_072029   DEBN CEDO13 I894317                       54.044,15       0,00 10403 - Títulos Privados-Debêntures simples                  CEDO - CIA FIACAO TECIDOS CEDRO CACHOEIRA                   
DEBN CEDO13_072029   DEBN CEDO13 I894317                       41.033,52       0,00 10403 - Títulos Privados-Debêntures simples                  CEDO - CIA FIACAO TECIDOS CEDRO CACHOEIRA                   
DEBN AEGPA3_032026   DEBN AEGPA3 I109165                       78.663,40       0,00 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN CEDO13_072029   DEBN CEDO13 I894317                       70.057,23       0,00 10403 - Títulos Privados-Debêntures simples                  CEDO - CIA FIACAO TECIDOS CEDRO CACHOEIRA                   
DEBN CEDO13_072029   DEBN CEDO13 I894317                       55.044,97       0,00 10403 - Títulos Privados-Debêntures simples                  CEDO - CIA FIACAO TECIDOS CEDRO CACHOEIRA                   
DEBN CEDO13_072029   DEBN CEDO13 I894317                       60.049,05       0,00 10403 - Títulos Privados-Debêntures simples                  CEDO - CIA FIACAO TECIDOS CEDRO CACHOEIRA                   
DEBN CEDO13_072029   DEBN CEDO13 I894317                       55.044,97       0,00 10403 - Títulos Privados-Debêntures simples                  CEDO - CIA FIACAO TECIDOS CEDRO CACHOEIRA                   
DEBN CEDO13_072029   DEBN CEDO13 I894317                       55.044,97       0,00 10403 - Títulos Privados-Debêntures simples                  CEDO - CIA FIACAO TECIDOS CEDRO CACHOEIRA                   
DEBN CEDO13_072029   DEBN CEDO13 I894317                      103.084,21       0,00 10403 - Títulos Privados-Debêntures simples                  CEDO - CIA FIACAO TECIDOS CEDRO CACHOEIRA                   
DEBN CEDO13_072029   DEBN CEDO13 I894317                      729.596,01       0,01 10403 - Títulos Privados-Debêntures simples                  CEDO - CIA FIACAO TECIDOS CEDRO CACHOEIRA                   
DEBN CEPEA4_032029   DEBN CEPEA4 I707511                      158.666,89       0,00 10403 - Títulos Privados-Debêntures simples                  CEPE - CIA ENERGETICA PERNAMBUCO CELPE                      
DEBN CEPEA4_032029   DEBN CEPEA4 I707511                    2.620.119,19       0,05 10403 - Títulos Privados-Debêntures simples                  CEPE - CIA ENERGETICA PERNAMBUCO CELPE                      
DEBN CEPEA4_032029   DEBN CEPEA4 I707511                      892.765,68       0,02 10403 - Títulos Privados-Debêntures simples                  CEPE - CIA ENERGETICA PERNAMBUCO CELPE                      
DEBN AEGPA3_032026   DEBN AEGPA3 I109165                       71.222,26       0,00 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN CEPEA4_032029   DEBN CEPEA4 I707511                      138.569,08       0,00 10403 - Títulos Privados-Debêntures simples                  CEPE - CIA ENERGETICA PERNAMBUCO CELPE                      
DEBN CEPEA4_032029   DEBN CEPEA4 I707511                      110.009,04       0,00 10403 - Títulos Privados-Debêntures simples                  CEPE - CIA ENERGETICA PERNAMBUCO CELPE                      
DEBN CEPEA4_032029   DEBN CEPEA4 I707511                   28.111.541,24       0,50 10403 - Títulos Privados-Debêntures simples                  CEPE - CIA ENERGETICA PERNAMBUCO CELPE                      
DEBN CEPEA4_032029   DEBN CEPEA4 I707511                      108.951,26       0,00 10403 - Títulos Privados-Debêntures simples                  CEPE - CIA ENERGETICA PERNAMBUCO CELPE                      
DEBN CEPEA4_032029   DEBN CEPEA4 I707511                       37.022,27       0,00 10403 - Títulos Privados-Debêntures simples                  CEPE - CIA ENERGETICA PERNAMBUCO CELPE                      
DEBN CEPEA4_032029   DEBN CEPEA4 I707511                       64.524,53       0,00 10403 - Títulos Privados-Debêntures simples                  CEPE - CIA ENERGETICA PERNAMBUCO CELPE                      
DEBN CEPEA4_032029   DEBN CEPEA4 I707511                    3.623.951,70       0,06 10403 - Títulos Privados-Debêntures simples                  CEPE - CIA ENERGETICA PERNAMBUCO CELPE                      
DEBN CEPEA4_032029   DEBN CEPEA4 I707511                       66.640,09       0,00 10403 - Títulos Privados-Debêntures simples                  CEPE - CIA ENERGETICA PERNAMBUCO CELPE                      
DEBN CEPEA4_032029   DEBN CEPEA4 I707511                      137.511,30       0,00 10403 - Títulos Privados-Debêntures simples                  CEPE - CIA ENERGETICA PERNAMBUCO CELPE                      
DEBN CEPEA4_032029   DEBN CEPEA4 I707511                       40.195,61       0,00 10403 - Títulos Privados-Debêntures simples                  CEPE - CIA ENERGETICA PERNAMBUCO CELPE                      
DEBN AEGPA3_032026   DEBN AEGPA3 I109165                       90.356,60       0,00 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN CEPEA4_032029   DEBN CEPEA4 I707511                      120.586,83       0,00 10403 - Títulos Privados-Debêntures simples                  CEPE - CIA ENERGETICA PERNAMBUCO CELPE                      
DEBN CEPEA4_032029   DEBN CEPEA4 I707511                      107.893,48       0,00 10403 - Títulos Privados-Debêntures simples                  CEPE - CIA ENERGETICA PERNAMBUCO CELPE                      
DEBN CEPEA4_032029   DEBN CEPEA4 I707511                      106.835,70       0,00 10403 - Títulos Privados-Debêntures simples                  CEPE - CIA ENERGETICA PERNAMBUCO CELPE                      
DEBN CEPEA4_032029   DEBN CEPEA4 I707511                      207.324,73       0,00 10403 - Títulos Privados-Debêntures simples                  CEPE - CIA ENERGETICA PERNAMBUCO CELPE                      
DEBN CEPEA4_032029   DEBN CEPEA4 I707511                       21.155,58       0,00 10403 - Títulos Privados-Debêntures simples                  CEPE - CIA ENERGETICA PERNAMBUCO CELPE                      
DEBN CEPEA4_032029   DEBN CEPEA4 I707511                       80.391,22       0,00 10403 - Títulos Privados-Debêntures simples                  CEPE - CIA ENERGETICA PERNAMBUCO CELPE                      
DEBN CEPEA4_032029   DEBN CEPEA4 I707511                      121.644,61       0,00 10403 - Títulos Privados-Debêntures simples                  CEPE - CIA ENERGETICA PERNAMBUCO CELPE                      
DEBN CEPEA4_032029   DEBN CEPEA4 I707511                      151.262,43       0,00 10403 - Títulos Privados-Debêntures simples                  CEPE - CIA ENERGETICA PERNAMBUCO CELPE                      
DEBN CEPEA4_032029   DEBN CEPEA4 I707511                      396.667,22       0,01 10403 - Títulos Privados-Debêntures simples                  CEPE - CIA ENERGETICA PERNAMBUCO CELPE                      
DEBN CEPEA4_032029   DEBN CEPEA4 I707511                      107.893,48       0,00 10403 - Títulos Privados-Debêntures simples                  CEPE - CIA ENERGETICA PERNAMBUCO CELPE                      
CRI_CRA024002GY      CRI_CRA024002GY CRA  I666012               3.571,58       0,00 10444 - Títulos Privados-Certif.Receb. Agronegócio (CRA)     CASC - CANAL COMPANHIA DE SECURITIZACAO                     
DEBN AEGPA3_032026   DEBN AEGPA3 I109165                       53.150,94       0,00 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN CEPEA4_032029   DEBN CEPEA4 I707511                    1.443.868,67       0,03 10403 - Títulos Privados-Debêntures simples                  CEPE - CIA ENERGETICA PERNAMBUCO CELPE                      
DEBN CEPEA4_032029   DEBN CEPEA4 I707511                      529.947,40       0,01 10403 - Títulos Privados-Debêntures simples                  CEPE - CIA ENERGETICA PERNAMBUCO CELPE                      
DEBN CEPEA4_032029   DEBN CEPEA4 I707511                      173.475,80       0,00 10403 - Títulos Privados-Debêntures simples                  CEPE - CIA ENERGETICA PERNAMBUCO CELPE                      
DEBN CEPEA4_032029   DEBN CEPEA4 I707511                       83.564,56       0,00 10403 - Títulos Privados-Debêntures simples                  CEPE - CIA ENERGETICA PERNAMBUCO CELPE                      
DEBN CEPEA4_032029   DEBN CEPEA4 I707511                       38.080,05       0,00 10403 - Títulos Privados-Debêntures simples                  CEPE - CIA ENERGETICA PERNAMBUCO CELPE                      
DEBN CEPEA4_032029   DEBN CEPEA4 I707511                      242.231,45       0,00 10403 - Títulos Privados-Debêntures simples                  CEPE - CIA ENERGETICA PERNAMBUCO CELPE                      
DEBN CEPEA4_032029   DEBN CEPEA4 I707511                      263.387,03       0,00 10403 - Títulos Privados-Debêntures simples                  CEPE - CIA ENERGETICA PERNAMBUCO CELPE                      
DEBN CEPEA4_032029   DEBN CEPEA4 I707511                        7.404,45       0,00 10403 - Títulos Privados-Debêntures simples                  CEPE - CIA ENERGETICA PERNAMBUCO CELPE                      
DEBN CEPEA4_032029   DEBN CEPEA4 I707511                       49.715,62       0,00 10403 - Títulos Privados-Debêntures simples                  CEPE - CIA ENERGETICA PERNAMBUCO CELPE                      
DEBN CGOS14_102029   DEBN CGOS14 I504673                      206.357,57       0,00 10403 - Títulos Privados-Debêntures simples                  CGOS - EQUATORIAL GOIAS DISTRIBUIDORA DE ENERGIA S.A.       
DEBN AEGPA3_032026   DEBN AEGPA3 I109165                      731.356,98       0,01 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN CGOS14_102029   DEBN CGOS14 I504673                      394.555,71       0,01 10403 - Títulos Privados-Debêntures simples                  CGOS - EQUATORIAL GOIAS DISTRIBUIDORA DE ENERGIA S.A.       
DEBN CGOS14_102029   DEBN CGOS14 I504673                       71.119,57       0,00 10403 - Títulos Privados-Debêntures simples                  CGOS - EQUATORIAL GOIAS DISTRIBUIDORA DE ENERGIA S.A.       
DEBN CGOS14_102029   DEBN CGOS14 I504673                      211.452,79       0,00 10403 - Títulos Privados-Debêntures simples                  CGOS - EQUATORIAL GOIAS DISTRIBUIDORA DE ENERGIA S.A.       
DEBN CGOS14_102029   DEBN CGOS14 I504673                   -2.074.251,67      -0,04 10403 - Títulos Privados-Debêntures simples                  CGOS - EQUATORIAL GOIAS DISTRIBUIDORA DE ENERGIA S.A.       
DEBN CGOS14_102029   DEBN CGOS14 I504673                   40.273.886,48       0,72 10403 - Títulos Privados-Debêntures simples                  CGOS - EQUATORIAL GOIAS DISTRIBUIDORA DE ENERGIA S.A.       
DEBN CGOS14_102029   DEBN CGOS14 I504673                     -150.763,76       0,00 10403 - Títulos Privados-Debêntures simples                  CGOS - EQUATORIAL GOIAS DISTRIBUIDORA DE ENERGIA S.A.       
DEBN CGOS14_102029   DEBN CGOS14 I504673                     -353.987,29      -0,01 10403 - Títulos Privados-Debêntures simples                  CGOS - EQUATORIAL GOIAS DISTRIBUIDORA DE ENERGIA S.A.       
DEBN CGOS14_102029   DEBN CGOS14 I504673                     -675.385,76      -0,01 10403 - Títulos Privados-Debêntures simples                  CGOS - EQUATORIAL GOIAS DISTRIBUIDORA DE ENERGIA S.A.       
DEBN CGOS14_102029   DEBN CGOS14 I504673                      127.415,62       0,00 10403 - Títulos Privados-Debêntures simples                  CGOS - EQUATORIAL GOIAS DISTRIBUIDORA DE ENERGIA S.A.       
DEBN CGOS14_102029   DEBN CGOS14 I504673                      462.516,79       0,01 10403 - Títulos Privados-Debêntures simples                  CGOS - EQUATORIAL GOIAS DISTRIBUIDORA DE ENERGIA S.A.       
DEBN AEGPA3_032026   DEBN AEGPA3 I109165                      109.490,94       0,00 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN CGOS14_102029   DEBN CGOS14 I504673                      204.400,65       0,00 10403 - Títulos Privados-Debêntures simples                  CGOS - EQUATORIAL GOIAS DISTRIBUIDORA DE ENERGIA S.A.       
DEBN CGOS14_102029   DEBN CGOS14 I504673                      260.720,07       0,00 10403 - Títulos Privados-Debêntures simples                  CGOS - EQUATORIAL GOIAS DISTRIBUIDORA DE ENERGIA S.A.       
DEBN CGOS14_102029   DEBN CGOS14 I504673                       73.292,16       0,00 10403 - Títulos Privados-Debêntures simples                  CGOS - EQUATORIAL GOIAS DISTRIBUIDORA DE ENERGIA S.A.       
DEBN CGOS14_102029   DEBN CGOS14 I504673                       39.744,01       0,00 10403 - Títulos Privados-Debêntures simples                  CGOS - EQUATORIAL GOIAS DISTRIBUIDORA DE ENERGIA S.A.       
DEBN CGOS14_102029   DEBN CGOS14 I504673                       14.578,12       0,00 10403 - Títulos Privados-Debêntures simples                  CGOS - EQUATORIAL GOIAS DISTRIBUIDORA DE ENERGIA S.A.       
DEBN CGOS14_102029   DEBN CGOS14 I504673                      332.119,05       0,01 10403 - Títulos Privados-Debêntures simples                  CGOS - EQUATORIAL GOIAS DISTRIBUIDORA DE ENERGIA S.A.       
DEBN CGOS14_102029   DEBN CGOS14 I504673                      159.112,03       0,00 10403 - Títulos Privados-Debêntures simples                  CGOS - EQUATORIAL GOIAS DISTRIBUIDORA DE ENERGIA S.A.       
DEBN CGOS14_102029   DEBN CGOS14 I504673                      205.186,82       0,00 10403 - Títulos Privados-Debêntures simples                  CGOS - EQUATORIAL GOIAS DISTRIBUIDORA DE ENERGIA S.A.       
DEBN CGOS14_102029   DEBN CGOS14 I504673                       77.008,40       0,00 10403 - Títulos Privados-Debêntures simples                  CGOS - EQUATORIAL GOIAS DISTRIBUIDORA DE ENERGIA S.A.       
DEBN CGOS14_102029   DEBN CGOS14 I504673                      501.347,16       0,01 10403 - Títulos Privados-Debêntures simples                  CGOS - EQUATORIAL GOIAS DISTRIBUIDORA DE ENERGIA S.A.       
DEBN AEGPA3_032026   DEBN AEGPA3 I109165                       86.104,53       0,00 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN CGOS14_102029   DEBN CGOS14 I504673                      264.083,59       0,00 10403 - Títulos Privados-Debêntures simples                  CGOS - EQUATORIAL GOIAS DISTRIBUIDORA DE ENERGIA S.A.       
DEBN CGOS14_102029   DEBN CGOS14 I504673                       93.922,71       0,00 10403 - Títulos Privados-Debêntures simples                  CGOS - EQUATORIAL GOIAS DISTRIBUIDORA DE ENERGIA S.A.       
DEBN CGOS14_102029   DEBN CGOS14 I504673                      287.170,39       0,01 10403 - Títulos Privados-Debêntures simples                  CGOS - EQUATORIAL GOIAS DISTRIBUIDORA DE ENERGIA S.A.       
DEBN CGOS14_102029   DEBN CGOS14 I504673                      229.516,61       0,00 10403 - Títulos Privados-Debêntures simples                  CGOS - EQUATORIAL GOIAS DISTRIBUIDORA DE ENERGIA S.A.       
DEBN CGOS14_102029   DEBN CGOS14 I504673                      154.322,77       0,00 10403 - Títulos Privados-Debêntures simples                  CGOS - EQUATORIAL GOIAS DISTRIBUIDORA DE ENERGIA S.A.       
DEBN CGOS14_102029   DEBN CGOS14 I504673                      232.340,45       0,00 10403 - Títulos Privados-Debêntures simples                  CGOS - EQUATORIAL GOIAS DISTRIBUIDORA DE ENERGIA S.A.       
DEBN CGOS14_102029   DEBN CGOS14 I504673                      206.112,16       0,00 10403 - Títulos Privados-Debêntures simples                  CGOS - EQUATORIAL GOIAS DISTRIBUIDORA DE ENERGIA S.A.       
DEBN CGOS17_082030   DEBN CGOS17 I923489                      117.283,78       0,00 10403 - Títulos Privados-Debêntures simples                  CGOS - EQUATORIAL GOIAS DISTRIBUIDORA DE ENERGIA S.A.       
DEBN CGOS17_082030   DEBN CGOS17 I923489                      149.361,40       0,00 10403 - Títulos Privados-Debêntures simples                  CGOS - EQUATORIAL GOIAS DISTRIBUIDORA DE ENERGIA S.A.       
DEBN CGOS17_082030   DEBN CGOS17 I923489                       42.101,87       0,00 10403 - Títulos Privados-Debêntures simples                  CGOS - EQUATORIAL GOIAS DISTRIBUIDORA DE ENERGIA S.A.       
DEBN AEGPA3_032026   DEBN AEGPA3 I109165                      107.364,90       0,00 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN CGOS17_082030   DEBN CGOS17 I923489                       73.177,06       0,00 10403 - Títulos Privados-Debêntures simples                  CGOS - EQUATORIAL GOIAS DISTRIBUIDORA DE ENERGIA S.A.       
DEBN CGOS17_082030   DEBN CGOS17 I923489                       11.026,68       0,00 10403 - Títulos Privados-Debêntures simples                  CGOS - EQUATORIAL GOIAS DISTRIBUIDORA DE ENERGIA S.A.       
DEBN CGOS17_082030   DEBN CGOS17 I923489                      287.696,11       0,01 10403 - Títulos Privados-Debêntures simples                  CGOS - EQUATORIAL GOIAS DISTRIBUIDORA DE ENERGIA S.A.       
DEBN CGOS17_082030   DEBN CGOS17 I923489                      263.637,90       0,00 10403 - Títulos Privados-Debêntures simples                  CGOS - EQUATORIAL GOIAS DISTRIBUIDORA DE ENERGIA S.A.       
DEBN CGOS17_082030   DEBN CGOS17 I923489                      117.283,78       0,00 10403 - Títulos Privados-Debêntures simples                  CGOS - EQUATORIAL GOIAS DISTRIBUIDORA DE ENERGIA S.A.       
DEBN CGOS17_082030   DEBN CGOS17 I923489                       91.220,72       0,00 10403 - Títulos Privados-Debêntures simples                  CGOS - EQUATORIAL GOIAS DISTRIBUIDORA DE ENERGIA S.A.       
DEBN CGOS17_082030   DEBN CGOS17 I923489                   83.441.897,45       1,49 10403 - Títulos Privados-Debêntures simples                  CGOS - EQUATORIAL GOIAS DISTRIBUIDORA DE ENERGIA S.A.       
DEBN CGOS17_082030   DEBN CGOS17 I923489                       23.055,79       0,00 10403 - Títulos Privados-Debêntures simples                  CGOS - EQUATORIAL GOIAS DISTRIBUIDORA DE ENERGIA S.A.       
DEBN CGOS17_082030   DEBN CGOS17 I923489                      165.400,21       0,00 10403 - Títulos Privados-Debêntures simples                  CGOS - EQUATORIAL GOIAS DISTRIBUIDORA DE ENERGIA S.A.       
DEBN CGOS17_082030   DEBN CGOS17 I923489                      225.545,73       0,00 10403 - Títulos Privados-Debêntures simples                  CGOS - EQUATORIAL GOIAS DISTRIBUIDORA DE ENERGIA S.A.       
DEBN AEGPA3_032026   DEBN AEGPA3 I109165                       11.693,21       0,00 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN CGOS17_082030   DEBN CGOS17 I923489                      118.286,21       0,00 10403 - Títulos Privados-Debêntures simples                  CGOS - EQUATORIAL GOIAS DISTRIBUIDORA DE ENERGIA S.A.       
DEBN CGOS17_082030   DEBN CGOS17 I923489                      131.317,74       0,00 10403 - Títulos Privados-Debêntures simples                  CGOS - EQUATORIAL GOIAS DISTRIBUIDORA DE ENERGIA S.A.       
DEBN CGOS17_082030   DEBN CGOS17 I923489                       44.106,72       0,00 10403 - Títulos Privados-Debêntures simples                  CGOS - EQUATORIAL GOIAS DISTRIBUIDORA DE ENERGIA S.A.       
DEBN CGOS17_082030   DEBN CGOS17 I923489                       53.128,55       0,00 10403 - Títulos Privados-Debêntures simples                  CGOS - EQUATORIAL GOIAS DISTRIBUIDORA DE ENERGIA S.A.       
DEBN CGOS17_082030   DEBN CGOS17 I923489                      189.458,42       0,00 10403 - Títulos Privados-Debêntures simples                  CGOS - EQUATORIAL GOIAS DISTRIBUIDORA DE ENERGIA S.A.       
DEBN CGOS17_082030   DEBN CGOS17 I923489                       88.213,44       0,00 10403 - Títulos Privados-Debêntures simples                  CGOS - EQUATORIAL GOIAS DISTRIBUIDORA DE ENERGIA S.A.       
DEBN CGOS17_082030   DEBN CGOS17 I923489                       40.097,02       0,00 10403 - Títulos Privados-Debêntures simples                  CGOS - EQUATORIAL GOIAS DISTRIBUIDORA DE ENERGIA S.A.       
DEBN CGOS17_082030   DEBN CGOS17 I923489                      121.293,48       0,00 10403 - Títulos Privados-Debêntures simples                  CGOS - EQUATORIAL GOIAS DISTRIBUIDORA DE ENERGIA S.A.       
DEBN CGOS17_082030   DEBN CGOS17 I923489                      151.366,25       0,00 10403 - Títulos Privados-Debêntures simples                  CGOS - EQUATORIAL GOIAS DISTRIBUIDORA DE ENERGIA S.A.       
DEBN CGOS17_082030   DEBN CGOS17 I923489                      118.286,21       0,00 10403 - Títulos Privados-Debêntures simples                  CGOS - EQUATORIAL GOIAS DISTRIBUIDORA DE ENERGIA S.A.       
DEBN AEGPA3_032026   DEBN AEGPA3 I109165                       95.671,70       0,00 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN CGOS17_082030   DEBN CGOS17 I923489                      134.325,01       0,00 10403 - Títulos Privados-Debêntures simples                  CGOS - EQUATORIAL GOIAS DISTRIBUIDORA DE ENERGIA S.A.       
DEBN CGOS18_092030   DEBN CGOS18_092030 J22776                 23.965,37       0,00 10403 - Títulos Privados-Debêntures simples                  CGOS - EQUATORIAL GOIAS DISTRIBUIDORA DE ENERGIA S.A.       
DEBN CGOS18_092030   DEBN CGOS18_092030 J22776                 68.770,18       0,00 10403 - Títulos Privados-Debêntures simples                  CGOS - EQUATORIAL GOIAS DISTRIBUIDORA DE ENERGIA S.A.       
DEBN CGOS18_092030   DEBN CGOS18_092030 J22776                 39.594,95       0,00 10403 - Títulos Privados-Debêntures simples                  CGOS - EQUATORIAL GOIAS DISTRIBUIDORA DE ENERGIA S.A.       
DEBN CGOS18_092030   DEBN CGOS18_092030 J22776                 73.980,04       0,00 10403 - Títulos Privados-Debêntures simples                  CGOS - EQUATORIAL GOIAS DISTRIBUIDORA DE ENERGIA S.A.       
DEBN CGOS18_092030   DEBN CGOS18_092030 J22776                 59.392,43       0,00 10403 - Títulos Privados-Debêntures simples                  CGOS - EQUATORIAL GOIAS DISTRIBUIDORA DE ENERGIA S.A.       
DEBN CGOS18_092030   DEBN CGOS18_092030 J22776                 85.441,74       0,00 10403 - Títulos Privados-Debêntures simples                  CGOS - EQUATORIAL GOIAS DISTRIBUIDORA DE ENERGIA S.A.       
DEBN CGOS18_092030   DEBN CGOS18_092030 J22776                 85.441,74       0,00 10403 - Títulos Privados-Debêntures simples                  CGOS - EQUATORIAL GOIAS DISTRIBUIDORA DE ENERGIA S.A.       
DEBN CGOS18_092030   DEBN CGOS18_092030 J22776                 40.636,93       0,00 10403 - Títulos Privados-Debêntures simples                  CGOS - EQUATORIAL GOIAS DISTRIBUIDORA DE ENERGIA S.A.       
DEBN CGOS18_092030   DEBN CGOS18_092030 J22776                130.246,56       0,00 10403 - Títulos Privados-Debêntures simples                  CGOS - EQUATORIAL GOIAS DISTRIBUIDORA DE ENERGIA S.A.       
DEBN AEGPA3_032026   DEBN AEGPA3 I109165                     -367.804,53      -0,01 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN CGOS18_092030   DEBN CGOS18_092030 J22776                  3.125,92       0,00 10403 - Títulos Privados-Debêntures simples                  CGOS - EQUATORIAL GOIAS DISTRIBUIDORA DE ENERGIA S.A.       
DEBN CGOS18_092030   DEBN CGOS18_092030 J22776             19.014.955,84       0,34 10403 - Títulos Privados-Debêntures simples                  CGOS - EQUATORIAL GOIAS DISTRIBUIDORA DE ENERGIA S.A.       
DEBN CGOS18_092030   DEBN CGOS18_092030 J22776                 52.098,62       0,00 10403 - Títulos Privados-Debêntures simples                  CGOS - EQUATORIAL GOIAS DISTRIBUIDORA DE ENERGIA S.A.       
DEBN CGOS18_092030   DEBN CGOS18_092030 J22776                 20.839,45       0,00 10403 - Títulos Privados-Debêntures simples                  CGOS - EQUATORIAL GOIAS DISTRIBUIDORA DE ENERGIA S.A.       
DEBN CGOS18_092030   DEBN CGOS18_092030 J22776                119.826,83       0,00 10403 - Títulos Privados-Debêntures simples                  CGOS - EQUATORIAL GOIAS DISTRIBUIDORA DE ENERGIA S.A.       
DEBN CGOS18_092030   DEBN CGOS18_092030 J22776                 33.343,12       0,00 10403 - Títulos Privados-Debêntures simples                  CGOS - EQUATORIAL GOIAS DISTRIBUIDORA DE ENERGIA S.A.       
DEBN CGOS18_092030   DEBN CGOS18_092030 J22776                 53.140,60       0,00 10403 - Títulos Privados-Debêntures simples                  CGOS - EQUATORIAL GOIAS DISTRIBUIDORA DE ENERGIA S.A.       
DEBN CLII12_102031   DEBN CLII12 I364256                      158.251,85       0,00 10403 - Títulos Privados-Debêntures simples                  CLII - CORREDOR LOGISTICA E INFRAESTRUTURA S.A.             
DEBN CLII12_102031   DEBN CLII12 I364256                       96.888,89       0,00 10403 - Títulos Privados-Debêntures simples                  CLII - CORREDOR LOGISTICA E INFRAESTRUTURA S.A.             
DEBN CLII12_102031   DEBN CLII12 I364256                      596.404,92       0,01 10403 - Títulos Privados-Debêntures simples                  CLII - CORREDOR LOGISTICA E INFRAESTRUTURA S.A.             
DEBN AEGPA3_032026   DEBN AEGPA3 I109165                     -481.547,55      -0,01 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN CLII12_102031   DEBN CLII12 I364256                       97.965,43       0,00 10403 - Títulos Privados-Debêntures simples                  CLII - CORREDOR LOGISTICA E INFRAESTRUTURA S.A.             
DEBN CLII12_102031   DEBN CLII12 I364256                    3.186.567,82       0,06 10403 - Títulos Privados-Debêntures simples                  CLII - CORREDOR LOGISTICA E INFRAESTRUTURA S.A.             
DEBN CLII12_102031   DEBN CLII12 I364256                      460.760,48       0,01 10403 - Títulos Privados-Debêntures simples                  CLII - CORREDOR LOGISTICA E INFRAESTRUTURA S.A.             
DEBN CLII12_102031   DEBN CLII12 I364256                   10.916.147,88       0,20 10403 - Títulos Privados-Debêntures simples                  CLII - CORREDOR LOGISTICA E INFRAESTRUTURA S.A.             
DEBN CLII12_102031   DEBN CLII12 I364256                    1.963.614,77       0,04 10403 - Títulos Privados-Debêntures simples                  CLII - CORREDOR LOGISTICA E INFRAESTRUTURA S.A.             
DEBN CLII12_102031   DEBN CLII12 I364256                    6.748.849,21       0,12 10403 - Títulos Privados-Debêntures simples                  CLII - CORREDOR LOGISTICA E INFRAESTRUTURA S.A.             
DEBN CLII12_102031   DEBN CLII12 I364256                       65.669,13       0,00 10403 - Títulos Privados-Debêntures simples                  CLII - CORREDOR LOGISTICA E INFRAESTRUTURA S.A.             
DEBN CLII12_102031   DEBN CLII12 I364256                      191.624,69       0,00 10403 - Títulos Privados-Debêntures simples                  CLII - CORREDOR LOGISTICA E INFRAESTRUTURA S.A.             
DEBN CLII12_102031   DEBN CLII12 I364256                       38.755,55       0,00 10403 - Títulos Privados-Debêntures simples                  CLII - CORREDOR LOGISTICA E INFRAESTRUTURA S.A.             
DEBN CLII12_102031   DEBN CLII12 I364256                    4.027.348,05       0,07 10403 - Títulos Privados-Debêntures simples                  CLII - CORREDOR LOGISTICA E INFRAESTRUTURA S.A.             
DEBN AEGPA3_032026   DEBN AEGPA3 I109165                    2.726.643,39       0,05 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN CLII12_102031   DEBN CLII12 I364256                      147.486,42       0,00 10403 - Títulos Privados-Debêntures simples                  CLII - CORREDOR LOGISTICA E INFRAESTRUTURA S.A.             
DEBN CLII12_102031   DEBN CLII12 I364256                    6.051.249,23       0,11 10403 - Títulos Privados-Debêntures simples                  CLII - CORREDOR LOGISTICA E INFRAESTRUTURA S.A.             
DEBN CLII12_102031   DEBN CLII12 I364256                       76.434,57       0,00 10403 - Títulos Privados-Debêntures simples                  CLII - CORREDOR LOGISTICA E INFRAESTRUTURA S.A.             
DEBN CLII12_102031   DEBN CLII12 I364256                      510.281,47       0,01 10403 - Títulos Privados-Debêntures simples                  CLII - CORREDOR LOGISTICA E INFRAESTRUTURA S.A.             
DEBN CLII12_102031   DEBN CLII12 I364256                      863.387,63       0,02 10403 - Títulos Privados-Debêntures simples                  CLII - CORREDOR LOGISTICA E INFRAESTRUTURA S.A.             
DEBN CLII12_102031   DEBN CLII12 I364256                      636.237,02       0,01 10403 - Títulos Privados-Debêntures simples                  CLII - CORREDOR LOGISTICA E INFRAESTRUTURA S.A.             
DEBN CLII12_102031   DEBN CLII12 I364256                      433.846,90       0,01 10403 - Títulos Privados-Debêntures simples                  CLII - CORREDOR LOGISTICA E INFRAESTRUTURA S.A.             
DEBN CLII12_102031   DEBN CLII12 I364256                      118.419,75       0,00 10403 - Títulos Privados-Debêntures simples                  CLII - CORREDOR LOGISTICA E INFRAESTRUTURA S.A.             
DEBN CLII12_102031   DEBN CLII12 I364256                      896.760,48       0,02 10403 - Títulos Privados-Debêntures simples                  CLII - CORREDOR LOGISTICA E INFRAESTRUTURA S.A.             
DEBN CLII12_102031   DEBN CLII12 I364256                      440.306,16       0,01 10403 - Títulos Privados-Debêntures simples                  CLII - CORREDOR LOGISTICA E INFRAESTRUTURA S.A.             
DEBN AEGPA0_052029   DEBN AEGPA0 H750651                        4.134,06       0,00 10440 - Títulos Privados-Debêntures Incent. (Lei 12.431)     AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN AEGPA3_032026   DEBN AEGPA3 I109165                    2.368.406,04       0,04 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN CLII12_102031   DEBN CLII12 I364256                      220.691,35       0,00 10403 - Títulos Privados-Debêntures simples                  CLII - CORREDOR LOGISTICA E INFRAESTRUTURA S.A.             
DEBN CLIS11_102031   DEBN CLIS11 I361744                    2.167.684,16       0,04 10403 - Títulos Privados-Debêntures simples                  CLIS - CLI SUL S.A.                                         
DEBN CLIS11_102031   DEBN CLIS11 I361744                    1.212.808,24       0,02 10403 - Títulos Privados-Debêntures simples                  CLIS - CLI SUL S.A.                                         
DEBN CLIS11_102031   DEBN CLIS11 I361744                      132.650,90       0,00 10403 - Títulos Privados-Debêntures simples                  CLIS - CLI SUL S.A.                                         
DEBN CLIS11_102031   DEBN CLIS11 I361744                      761.163,50       0,01 10403 - Títulos Privados-Debêntures simples                  CLIS - CLI SUL S.A.                                         
DEBN CLIS11_102031   DEBN CLIS11 I361744                    7.843.247,70       0,14 10403 - Títulos Privados-Debêntures simples                  CLIS - CLI SUL S.A.                                         
DEBN CLIS11_102031   DEBN CLIS11 I361744                       88.433,93       0,00 10403 - Títulos Privados-Debêntures simples                  CLIS - CLI SUL S.A.                                         
DEBN CLIS11_102031   DEBN CLIS11 I361744                      200.029,14       0,00 10403 - Títulos Privados-Debêntures simples                  CLIS - CLI SUL S.A.                                         
DEBN CLIS11_102031   DEBN CLIS11 I361744                      263.196,23       0,00 10403 - Títulos Privados-Debêntures simples                  CLIS - CLI SUL S.A.                                         
DEBN CLIS11_102031   DEBN CLIS11 I361744                      200.029,14       0,00 10403 - Títulos Privados-Debêntures simples                  CLIS - CLI SUL S.A.                                         
DEBN AEGPA3_032026   DEBN AEGPA3 I109165                     -241.305,28       0,00 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN CLIS11_102031   DEBN CLIS11 I361744                      160.023,31       0,00 10403 - Títulos Privados-Debêntures simples                  CLIS - CLI SUL S.A.                                         
DEBN CLIS11_102031   DEBN CLIS11 I361744                      298.990,92       0,01 10403 - Títulos Privados-Debêntures simples                  CLIS - CLI SUL S.A.                                         
DEBN CLIS11_102031   DEBN CLIS11 I361744                      588.506,77       0,01 10403 - Títulos Privados-Debêntures simples                  CLIS - CLI SUL S.A.                                         
DEBN CLIS11_102031   DEBN CLIS11 I361744                    4.160.606,03       0,07 10403 - Títulos Privados-Debêntures simples                  CLIS - CLI SUL S.A.                                         
DEBN CLIS11_102031   DEBN CLIS11 I361744                      680.099,06       0,01 10403 - Títulos Privados-Debêntures simples                  CLIS - CLI SUL S.A.                                         
DEBN CLIS11_102031   DEBN CLIS11 I361744                      595.876,27       0,01 10403 - Títulos Privados-Debêntures simples                  CLIS - CLI SUL S.A.                                         
DEBN CLIS11_102031   DEBN CLIS11 I361744                      314.782,69       0,01 10403 - Títulos Privados-Debêntures simples                  CLIS - CLI SUL S.A.                                         
DEBN CLIS11_102031   DEBN CLIS11 I361744                    5.075.476,13       0,09 10403 - Títulos Privados-Debêntures simples                  CLIS - CLI SUL S.A.                                         
DEBN CLIS11_102031   DEBN CLIS11 I361744                       48.428,11       0,00 10403 - Títulos Privados-Debêntures simples                  CLIS - CLI SUL S.A.                                         
DEBN CLIS11_102031   DEBN CLIS11 I361744                      184.237,36       0,00 10403 - Títulos Privados-Debêntures simples                  CLIS - CLI SUL S.A.                                         
DEBN AEGPA3_032026   DEBN AEGPA3 I109165                       31.890,57       0,00 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN CLIS11_102031   DEBN CLIS11 I361744                      205.293,06       0,00 10403 - Títulos Privados-Debêntures simples                  CLIS - CLI SUL S.A.                                         
DEBN CLIS11_102031   DEBN CLIS11 I361744                    1.371.778,76       0,02 10403 - Títulos Privados-Debêntures simples                  CLIS - CLI SUL S.A.                                         
DEBN CLIS11_102031   DEBN CLIS11 I361744                      807.486,04       0,01 10403 - Títulos Privados-Debêntures simples                  CLIS - CLI SUL S.A.                                         
DEBN CLIS11_102031   DEBN CLIS11 I361744                      553.764,87       0,01 10403 - Títulos Privados-Debêntures simples                  CLIS - CLI SUL S.A.                                         
DEBN CLIS11_102031   DEBN CLIS11 I361744                    1.278.080,90       0,02 10403 - Títulos Privados-Debêntures simples                  CLIS - CLI SUL S.A.                                         
DEBN CLIS11_102031   DEBN CLIS11 I361744                   15.169.578,00       0,27 10403 - Títulos Privados-Debêntures simples                  CLIS - CLI SUL S.A.                                         
DEBN CLIS11_102031   DEBN CLIS11 I361744                    1.572.860,68       0,03 10403 - Títulos Privados-Debêntures simples                  CLIS - CLI SUL S.A.                                         
DEBN CMGD19_052026   DEBN CMGD19 I227528                       28.972,97       0,00 10403 - Títulos Privados-Debêntures simples                  CMGD - CEMIG DISTRIBUICAO SA                                
DEBN CMGD19_052026   DEBN CMGD19 I227528                    3.065.961,50       0,05 10403 - Títulos Privados-Debêntures simples                  CMGD - CEMIG DISTRIBUICAO SA                                
DEBN CMGD19_052026   DEBN CMGD19 I227528                      182.115,84       0,00 10403 - Títulos Privados-Debêntures simples                  CMGD - CEMIG DISTRIBUICAO SA                                
DEBN AEGPA3_032026   DEBN AEGPA3 I109165                     -782.381,89      -0,01 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN CMGD19_052026   DEBN CMGD19 I227528                      197.637,08       0,00 10403 - Títulos Privados-Debêntures simples                  CMGD - CEMIG DISTRIBUICAO SA                                
DEBN CMGD19_052026   DEBN CMGD19 I227528                       49.667,96       0,00 10403 - Títulos Privados-Debêntures simples                  CMGD - CEMIG DISTRIBUICAO SA                                
DEBN CMGD19_052026   DEBN CMGD19 I227528                       37.250,97       0,00 10403 - Títulos Privados-Debêntures simples                  CMGD - CEMIG DISTRIBUICAO SA                                
DEBN CMGD19_052026   DEBN CMGD19 I227528                   21.150.271,00       0,38 10403 - Títulos Privados-Debêntures simples                  CMGD - CEMIG DISTRIBUICAO SA                                
DEBN CMGD19_052026   DEBN CMGD19 I227528                      118.996,14       0,00 10403 - Títulos Privados-Debêntures simples                  CMGD - CEMIG DISTRIBUICAO SA                                
DEBN CMGD19_052026   DEBN CMGD19 I227528                       48.633,21       0,00 10403 - Títulos Privados-Debêntures simples                  CMGD - CEMIG DISTRIBUICAO SA                                
DEBN CMGD19_052026   DEBN CMGD19 I227528                       61.050,20       0,00 10403 - Títulos Privados-Debêntures simples                  CMGD - CEMIG DISTRIBUICAO SA                                
DEBN CMGD19_052026   DEBN CMGD19 I227528                      112.787,65       0,00 10403 - Títulos Privados-Debêntures simples                  CMGD - CEMIG DISTRIBUICAO SA                                
DEBN CMGD19_052026   DEBN CMGD19 I227528                       92.092,66       0,00 10403 - Títulos Privados-Debêntures simples                  CMGD - CEMIG DISTRIBUICAO SA                                
DEBN CMGD19_052026   DEBN CMGD19 I227528                      104.509,66       0,00 10403 - Títulos Privados-Debêntures simples                  CMGD - CEMIG DISTRIBUICAO SA                                
DEBN AEGPA3_032026   DEBN AEGPA3 I109165                      -43.583,77       0,00 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN CMGD19_052026   DEBN CMGD19 I227528                       91.057,92       0,00 10403 - Títulos Privados-Debêntures simples                  CMGD - CEMIG DISTRIBUICAO SA                                
DEBN CMGD19_052026   DEBN CMGD19 I227528                       80.710,43       0,00 10403 - Títulos Privados-Debêntures simples                  CMGD - CEMIG DISTRIBUICAO SA                                
DEBN CMGD19_052026   DEBN CMGD19 I227528                        6.208,49       0,00 10403 - Títulos Privados-Debêntures simples                  CMGD - CEMIG DISTRIBUICAO SA                                
DEBN CMGD19_052026   DEBN CMGD19 I227528                       51.737,45       0,00 10403 - Títulos Privados-Debêntures simples                  CMGD - CEMIG DISTRIBUICAO SA                                
DEBN CMGD19_052026   DEBN CMGD19 I227528                       30.007,72       0,00 10403 - Títulos Privados-Debêntures simples                  CMGD - CEMIG DISTRIBUICAO SA                                
DEBN CMGD19_052026   DEBN CMGD19 I227528                       15.521,24       0,00 10403 - Títulos Privados-Debêntures simples                  CMGD - CEMIG DISTRIBUICAO SA                                
DEBN CMGD19_052026   DEBN CMGD19 I227528                      156.247,11       0,00 10403 - Títulos Privados-Debêntures simples                  CMGD - CEMIG DISTRIBUICAO SA                                
DEBN CMGD19_052026   DEBN CMGD19 I227528                       27.938,22       0,00 10403 - Títulos Privados-Debêntures simples                  CMGD - CEMIG DISTRIBUICAO SA                                
DEBN CMGD19_052026   DEBN CMGD19 I227528                      102.440,16       0,00 10403 - Títulos Privados-Debêntures simples                  CMGD - CEMIG DISTRIBUICAO SA                                
DEBN CMGD19_052026   DEBN CMGD19 I227528                       63.119,69       0,00 10403 - Títulos Privados-Debêntures simples                  CMGD - CEMIG DISTRIBUICAO SA                                
DEBN AEGPA3_032026   DEBN AEGPA3 I109165                       38.268,68       0,00 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN CMGD19_052026   DEBN CMGD19 I227528                       80.710,43       0,00 10403 - Títulos Privados-Debêntures simples                  CMGD - CEMIG DISTRIBUICAO SA                                
DEBN CMGD19_052026   DEBN CMGD19 I227528                       82.779,93       0,00 10403 - Títulos Privados-Debêntures simples                  CMGD - CEMIG DISTRIBUICAO SA                                
DEBN CMGD19_052026   DEBN CMGD19 I227528                       31.042,47       0,00 10403 - Títulos Privados-Debêntures simples                  CMGD - CEMIG DISTRIBUICAO SA                                
DEBN CMGD19_052026   DEBN CMGD19 I227528                      132.447,88       0,00 10403 - Títulos Privados-Debêntures simples                  CMGD - CEMIG DISTRIBUICAO SA                                
DEBN CMGD19_052026   DEBN CMGD19 I227528                       34.146,72       0,00 10403 - Títulos Privados-Debêntures simples                  CMGD - CEMIG DISTRIBUICAO SA                                
DEBN CMGD19_052026   DEBN CMGD19 I227528                       77.606,18       0,00 10403 - Títulos Privados-Debêntures simples                  CMGD - CEMIG DISTRIBUICAO SA                                
DEBN CMGD19_052026   DEBN CMGD19 I227528                      852.633,23       0,02 10403 - Títulos Privados-Debêntures simples                  CMGD - CEMIG DISTRIBUICAO SA                                
DEBN CMGD19_052026   DEBN CMGD19 I227528                       81.745,18       0,00 10403 - Títulos Privados-Debêntures simples                  CMGD - CEMIG DISTRIBUICAO SA                                
DEBN CMGD19_052026   DEBN CMGD19 I227528                      671.552,15       0,01 10403 - Títulos Privados-Debêntures simples                  CMGD - CEMIG DISTRIBUICAO SA                                
DEBN CMGD19_052026   DEBN CMGD19 I227528                       80.710,43       0,00 10403 - Títulos Privados-Debêntures simples                  CMGD - CEMIG DISTRIBUICAO SA                                
DEBN AEGPA3_032026   DEBN AEGPA3 I109165                    1.694.452,07       0,03 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN CMGD19_052026   DEBN CMGD19 I227528                      296.972,98       0,01 10403 - Títulos Privados-Debêntures simples                  CMGD - CEMIG DISTRIBUICAO SA                                
DEBN CMGD19_052026   DEBN CMGD19 I227528                    1.984.648,72       0,04 10403 - Títulos Privados-Debêntures simples                  CMGD - CEMIG DISTRIBUICAO SA                                
DEBN CMPH14_112028   DEBN CMPH14 I559118                      103.378,26       0,00 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN CMPH14_112028   DEBN CMPH14 I559118                      126.585,62       0,00 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN CMPH14_112028   DEBN CMPH14 I559118                       15.823,20       0,00 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN CMPH14_112028   DEBN CMPH14 I559118                       23.207,36       0,00 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN CMPH14_112028   DEBN CMPH14 I559118                      447.269,20       0,01 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN CMPH14_112028   DEBN CMPH14 I559118                      912.471,36       0,02 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN CMPH14_112028   DEBN CMPH14 I559118                     -197.790,03       0,00 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN CMPH14_112028   DEBN CMPH14 I559118                      895.065,83       0,02 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN AEGPA3_032026   DEBN AEGPA3 I109165                       69.096,23       0,00 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN CMPH14_112028   DEBN CMPH14 I559118                       86.500,17       0,00 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN CMPH14_112028   DEBN CMPH14 I559118                       17.932,96       0,00 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN CMPH14_112028   DEBN CMPH14 I559118                        9.493,92       0,00 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN CMPH14_112028   DEBN CMPH14 I559118                       15.823,20       0,00 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN CMPH14_112028   DEBN CMPH14 I559118                       12.131,12       0,00 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN CMPH14_112028   DEBN CMPH14 I559118                       69.094,65       0,00 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN CMPH14_112028   DEBN CMPH14 I559118                       12.658,56       0,00 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN CMPH14_112028   DEBN CMPH14 I559118                        6.329,28       0,00 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN CMPH14_112028   DEBN CMPH14 I559118                        8.439,04       0,00 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN CMPH14_112028   DEBN CMPH14 I559118                       34.283,60       0,00 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN AEGPA3_032026   DEBN AEGPA3 I109165                      180.713,21       0,00 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN CMPH14_112028   DEBN CMPH14 I559118                       13.713,44       0,00 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN CMPH14_112028   DEBN CMPH14 I559118                       15.823,20       0,00 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN CMPH14_112028   DEBN CMPH14 I559118                       11.603,68       0,00 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN CMPH14_112028   DEBN CMPH14 I559118                        2.109,76       0,00 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN CMPH14_112028   DEBN CMPH14 I559118                        1.054,88       0,00 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN CMPH14_112028   DEBN CMPH14 I559118                       16.350,64       0,00 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN CMPH14_112028   DEBN CMPH14 I559118                      271.631,64       0,00 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN CMPH14_112028   DEBN CMPH14 I559118                      190.405,87       0,00 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN CMPH14_112028   DEBN CMPH14 I559118                        4.746,96       0,00 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN CMPH14_112028   DEBN CMPH14 I559118                       23.734,80       0,00 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN AEGPA3_032026   DEBN AEGPA3 I109165                      797.264,15       0,01 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN CMPH14_112028   DEBN CMPH14 I559118                       12.131,12       0,00 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN CMPH14_112028   DEBN CMPH14 I559118                       31.646,40       0,00 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN CMPH14_112028   DEBN CMPH14 I559118                       12.658,56       0,00 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN CMPH14_112028   DEBN CMPH14 I559118                       23.734,80       0,00 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN CMPH14_112028   DEBN CMPH14 I559118                       10.548,80       0,00 10403 - Títulos Privados-Debêntures simples                  VVEO - CM HOSPITALAR SA                                     
DEBN CPGT18_012030   DEBN CPGT18 I477458                       10.255,06       0,00 10403 - Títulos Privados-Debêntures simples                  CPGT - COPEL GERACAO TRANSMISSAO SA                         
DEBN CPGT18_012030   DEBN CPGT18 I477458                      709.650,47       0,01 10403 - Títulos Privados-Debêntures simples                  CPGT - COPEL GERACAO TRANSMISSAO SA                         
DEBN CPGT18_012030   DEBN CPGT18 I477458                      122.035,27       0,00 10403 - Títulos Privados-Debêntures simples                  CPGT - COPEL GERACAO TRANSMISSAO SA                         
DEBN CPGT18_012030   DEBN CPGT18 I477458                    1.336.234,91       0,02 10403 - Títulos Privados-Debêntures simples                  CPGT - COPEL GERACAO TRANSMISSAO SA                         
DEBN CPGT18_012030   DEBN CPGT18 I477458                       15.382,60       0,00 10403 - Títulos Privados-Debêntures simples                  CPGT - COPEL GERACAO TRANSMISSAO SA                         
DEBN AEGPA0_052029   DEBN AEGPA0 H750651                        6.201,09       0,00 10440 - Títulos Privados-Debêntures Incent. (Lei 12.431)     AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN AEGPA3_032026   DEBN AEGPA3 I109165                       66.970,19       0,00 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN CPGT18_012030   DEBN CPGT18 I477458                       11.280,57       0,00 10403 - Títulos Privados-Debêntures simples                  CPGT - COPEL GERACAO TRANSMISSAO SA                         
DEBN CPGT18_012030   DEBN CPGT18 I477458                       18.459,12       0,00 10403 - Títulos Privados-Debêntures simples                  CPGT - COPEL GERACAO TRANSMISSAO SA                         
DEBN CPGT18_012030   DEBN CPGT18 I477458                       44.096,78       0,00 10403 - Títulos Privados-Debêntures simples                  CPGT - COPEL GERACAO TRANSMISSAO SA                         
DEBN CPGT18_012030   DEBN CPGT18 I477458                       34.867,22       0,00 10403 - Títulos Privados-Debêntures simples                  CPGT - COPEL GERACAO TRANSMISSAO SA                         
DEBN CPGT18_012030   DEBN CPGT18 I477458                       35.892,72       0,00 10403 - Títulos Privados-Debêntures simples                  CPGT - COPEL GERACAO TRANSMISSAO SA                         
DEBN CPGT18_012030   DEBN CPGT18 I477458                       18.459,12       0,00 10403 - Títulos Privados-Debêntures simples                  CPGT - COPEL GERACAO TRANSMISSAO SA                         
DEBN CPGT18_012030   DEBN CPGT18 I477458                       31.790,70       0,00 10403 - Títulos Privados-Debêntures simples                  CPGT - COPEL GERACAO TRANSMISSAO SA                         
DEBN CPGT18_012030   DEBN CPGT18 I477458                      228.687,94       0,00 10403 - Títulos Privados-Debêntures simples                  CPGT - COPEL GERACAO TRANSMISSAO SA                         
DEBN CPGT18_012030   DEBN CPGT18 I477458                        3.076,52       0,00 10403 - Títulos Privados-Debêntures simples                  CPGT - COPEL GERACAO TRANSMISSAO SA                         
DEBN CPGT18_012030   DEBN CPGT18 I477458                       10.255,06       0,00 10403 - Títulos Privados-Debêntures simples                  CPGT - COPEL GERACAO TRANSMISSAO SA                         
DEBN AEGPA3_032026   DEBN AEGPA3 I109165                      141.381,51       0,00 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN CPGT18_012030   DEBN CPGT18 I477458                       48.198,80       0,00 10403 - Títulos Privados-Debêntures simples                  CPGT - COPEL GERACAO TRANSMISSAO SA                         
DEBN CPGT18_012030   DEBN CPGT18 I477458                        8.204,05       0,00 10403 - Títulos Privados-Debêntures simples                  CPGT - COPEL GERACAO TRANSMISSAO SA                         
DEBN CPGT18_012030   DEBN CPGT18 I477458                       25.637,66       0,00 10403 - Títulos Privados-Debêntures simples                  CPGT - COPEL GERACAO TRANSMISSAO SA                         
DEBN CPGT18_012030   DEBN CPGT18 I477458                       27.688,67       0,00 10403 - Títulos Privados-Debêntures simples                  CPGT - COPEL GERACAO TRANSMISSAO SA                         
DEBN CPGT18_012030   DEBN CPGT18 I477458                    6.879.097,30       0,12 10403 - Títulos Privados-Debêntures simples                  CPGT - COPEL GERACAO TRANSMISSAO SA                         
DEBN CPGT18_012030   DEBN CPGT18 I477458                        6.153,04       0,00 10403 - Títulos Privados-Debêntures simples                  CPGT - COPEL GERACAO TRANSMISSAO SA                         
DEBN CPGT18_012030   DEBN CPGT18 I477458                        1.025,51       0,00 10403 - Títulos Privados-Debêntures simples                  CPGT - COPEL GERACAO TRANSMISSAO SA                         
DEBN CPGT18_012030   DEBN CPGT18 I477458                       27.688,67       0,00 10403 - Títulos Privados-Debêntures simples                  CPGT - COPEL GERACAO TRANSMISSAO SA                         
DEBN CPGT18_012030   DEBN CPGT18 I477458                       24.612,15       0,00 10403 - Títulos Privados-Debêntures simples                  CPGT - COPEL GERACAO TRANSMISSAO SA                         
DEBN CPGT18_012030   DEBN CPGT18 I477458                       15.382,60       0,00 10403 - Títulos Privados-Debêntures simples                  CPGT - COPEL GERACAO TRANSMISSAO SA                         
DEBN AEGPA3_032026   DEBN AEGPA3 I109165                       47.835,85       0,00 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN CPGT18_012030   DEBN CPGT18 I477458                       60.504,88       0,00 10403 - Títulos Privados-Debêntures simples                  CPGT - COPEL GERACAO TRANSMISSAO SA                         
DEBN CPGT18_012030   DEBN CPGT18 I477458                       25.637,66       0,00 10403 - Títulos Privados-Debêntures simples                  CPGT - COPEL GERACAO TRANSMISSAO SA                         
DEBN CPGT18_012030   DEBN CPGT18 I477458                       31.790,70       0,00 10403 - Títulos Privados-Debêntures simples                  CPGT - COPEL GERACAO TRANSMISSAO SA                         
DEBN CPGT18_012030   DEBN CPGT18 I477458                       58.453,87       0,00 10403 - Títulos Privados-Debêntures simples                  CPGT - COPEL GERACAO TRANSMISSAO SA                         
DEBN CPGT18_012030   DEBN CPGT18 I477458                       25.637,66       0,00 10403 - Títulos Privados-Debêntures simples                  CPGT - COPEL GERACAO TRANSMISSAO SA                         
DEBN CPGT18_012030   DEBN CPGT18 I477458                        8.204,05       0,00 10403 - Títulos Privados-Debêntures simples                  CPGT - COPEL GERACAO TRANSMISSAO SA                         
DEBN CPLD16_062026   DEBN CPLD16                               46.965,14       0,00 10403 - Títulos Privados-Debêntures simples                  CPLD - COPEL DISTRIBUICAO SA                                
DEBN CPLD16_062026   DEBN CPLD16                               34.713,36       0,00 10403 - Títulos Privados-Debêntures simples                  CPLD - COPEL DISTRIBUICAO SA                                
DEBN CPLD16_062026   DEBN CPLD16                               17.356,68       0,00 10403 - Títulos Privados-Debêntures simples                  CPLD - COPEL DISTRIBUICAO SA                                
DEBN CPLD16_062026   DEBN CPLD16                              110.265,98       0,00 10403 - Títulos Privados-Debêntures simples                  CPLD - COPEL DISTRIBUICAO SA                                
DEBN AEGPA3_032026   DEBN AEGPA3 I109165                       64.844,15       0,00 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN CPLD16_062026   DEBN CPLD16                               46.965,14       0,00 10403 - Títulos Privados-Debêntures simples                  CPLD - COPEL DISTRIBUICAO SA                                
DEBN CPLD16_062026   DEBN CPLD16                               53.091,03       0,00 10403 - Títulos Privados-Debêntures simples                  CPLD - COPEL DISTRIBUICAO SA                                
DEBN CPLD16_062026   DEBN CPLD16                               65.342,81       0,00 10403 - Títulos Privados-Debêntures simples                  CPLD - COPEL DISTRIBUICAO SA                                
DEBN CPLD16_062026   DEBN CPLD16                               66.363,78       0,00 10403 - Títulos Privados-Debêntures simples                  CPLD - COPEL DISTRIBUICAO SA                                
DEBN CPLD16_062026   DEBN CPLD16                               60.237,90       0,00 10403 - Títulos Privados-Debêntures simples                  CPLD - COPEL DISTRIBUICAO SA                                
DEBN CPLD16_062026   DEBN CPLD16                               61.258,88       0,00 10403 - Títulos Privados-Debêntures simples                  CPLD - COPEL DISTRIBUICAO SA                                
DEBN CPLD16_062026   DEBN CPLD16                               21.440,61       0,00 10403 - Títulos Privados-Debêntures simples                  CPLD - COPEL DISTRIBUICAO SA                                
DEBN CPLD16_062026   DEBN CPLD16                               46.965,14       0,00 10403 - Títulos Privados-Debêntures simples                  CPLD - COPEL DISTRIBUICAO SA                                
DEBN CPLD16_062026   DEBN CPLD16                               16.335,70       0,00 10403 - Títulos Privados-Debêntures simples                  CPLD - COPEL DISTRIBUICAO SA                                
DEBN CPLD16_062026   DEBN CPLD16                               54.112,01       0,00 10403 - Títulos Privados-Debêntures simples                  CPLD - COPEL DISTRIBUICAO SA                                
DEBN AEGPA3_032026   DEBN AEGPA3 I109165                    1.199.085,28       0,02 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN CPLD16_062026   DEBN CPLD16                              158.252,10       0,00 10403 - Títulos Privados-Debêntures simples                  CPLD - COPEL DISTRIBUICAO SA                                
DEBN CPLD16_062026   DEBN CPLD16                              550.308,92       0,01 10403 - Títulos Privados-Debêntures simples                  CPLD - COPEL DISTRIBUICAO SA                                
DEBN CPLD16_062026   DEBN CPLD16                              113.328,93       0,00 10403 - Títulos Privados-Debêntures simples                  CPLD - COPEL DISTRIBUICAO SA                                
DEBN CPLD16_062026   DEBN CPLD16                              318.546,16       0,01 10403 - Títulos Privados-Debêntures simples                  CPLD - COPEL DISTRIBUICAO SA                                
DEBN CPLD16_062026   DEBN CPLD16                               30.629,44       0,00 10403 - Títulos Privados-Debêntures simples                  CPLD - COPEL DISTRIBUICAO SA                                
DEBN CPLD16_062026   DEBN CPLD16                               75.552,62       0,00 10403 - Títulos Privados-Debêntures simples                  CPLD - COPEL DISTRIBUICAO SA                                
DEBN CPLD16_062026   DEBN CPLD16                           12.582.573,48       0,22 10403 - Títulos Privados-Debêntures simples                  CPLD - COPEL DISTRIBUICAO SA                                
DEBN CPLD16_062026   DEBN CPLD16                            1.312.981,95       0,02 10403 - Títulos Privados-Debêntures simples                  CPLD - COPEL DISTRIBUICAO SA                                
DEBN CPLD16_062026   DEBN CPLD16                              485.987,10       0,01 10403 - Títulos Privados-Debêntures simples                  CPLD - COPEL DISTRIBUICAO SA                                
DEBN CPLD16_062026   DEBN CPLD16                               49.007,10       0,00 10403 - Títulos Privados-Debêntures simples                  CPLD - COPEL DISTRIBUICAO SA                                
DEBN AEGPA3_032026   DEBN AEGPA3 I109165                        1.063,02       0,00 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN CPLD16_062026   DEBN CPLD16                               90.867,34       0,00 10403 - Títulos Privados-Debêntures simples                  CPLD - COPEL DISTRIBUICAO SA                                
DEBN CPLD16_062026   DEBN CPLD16                               12.251,78       0,00 10403 - Títulos Privados-Debêntures simples                  CPLD - COPEL DISTRIBUICAO SA                                
DEBN CPLD16_062026   DEBN CPLD16                               82.699,49       0,00 10403 - Títulos Privados-Debêntures simples                  CPLD - COPEL DISTRIBUICAO SA                                
DEBN CPLD16_062026   DEBN CPLD16                               35.734,35       0,00 10403 - Títulos Privados-Debêntures simples                  CPLD - COPEL DISTRIBUICAO SA                                
DEBN CPLD16_062026   DEBN CPLD16                               17.356,68       0,00 10403 - Títulos Privados-Debêntures simples                  CPLD - COPEL DISTRIBUICAO SA                                
DEBN CPLD16_062026   DEBN CPLD16                               28.587,48       0,00 10403 - Títulos Privados-Debêntures simples                  CPLD - COPEL DISTRIBUICAO SA                                
DEBN CPLD16_062026   DEBN CPLD16                                7.146,87       0,00 10403 - Títulos Privados-Debêntures simples                  CPLD - COPEL DISTRIBUICAO SA                                
DEBN CPLD28_062027   DEBN CPLD28 I247951                    5.744.151,68       0,10 10403 - Títulos Privados-Debêntures simples                  CPLD - COPEL DISTRIBUICAO SA                                
DEBN CPLD28_062027   DEBN CPLD28 I247951                        9.289,73       0,00 10403 - Títulos Privados-Debêntures simples                  CPLD - COPEL DISTRIBUICAO SA                                
DEBN CPLD28_062027   DEBN CPLD28 I247951                       65.028,13       0,00 10403 - Títulos Privados-Debêntures simples                  CPLD - COPEL DISTRIBUICAO SA                                
DEBN AEGPA3_032026   DEBN AEGPA3 I109165                      544.265,66       0,01 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN CPLD28_062027   DEBN CPLD28 I247951                       30.965,78       0,00 10403 - Títulos Privados-Debêntures simples                  CPLD - COPEL DISTRIBUICAO SA                                
DEBN CPLD28_062027   DEBN CPLD28 I247951                       86.704,18       0,00 10403 - Títulos Privados-Debêntures simples                  CPLD - COPEL DISTRIBUICAO SA                                
DEBN CPLD28_062027   DEBN CPLD28 I247951                       95.993,91       0,00 10403 - Títulos Privados-Debêntures simples                  CPLD - COPEL DISTRIBUICAO SA                                
DEBN CPLD28_062027   DEBN CPLD28 I247951                       33.030,16       0,00 10403 - Títulos Privados-Debêntures simples                  CPLD - COPEL DISTRIBUICAO SA                                
DEBN CPLD28_062027   DEBN CPLD28 I247951                      110.444,61       0,00 10403 - Títulos Privados-Debêntures simples                  CPLD - COPEL DISTRIBUICAO SA                                
DEBN CPLD28_062027   DEBN CPLD28 I247951                       85.671,98       0,00 10403 - Títulos Privados-Debêntures simples                  CPLD - COPEL DISTRIBUICAO SA                                
DEBN CPLD28_062027   DEBN CPLD28 I247951                      120.766,54       0,00 10403 - Títulos Privados-Debêntures simples                  CPLD - COPEL DISTRIBUICAO SA                                
DEBN CPLD28_062027   DEBN CPLD28 I247951                      119.734,34       0,00 10403 - Títulos Privados-Debêntures simples                  CPLD - COPEL DISTRIBUICAO SA                                
DEBN CPLD28_062027   DEBN CPLD28 I247951                       39.223,32       0,00 10403 - Títulos Privados-Debêntures simples                  CPLD - COPEL DISTRIBUICAO SA                                
DEBN CPLD28_062027   DEBN CPLD28 I247951                       52.641,82       0,00 10403 - Títulos Privados-Debêntures simples                  CPLD - COPEL DISTRIBUICAO SA                                
DEBN AEGPA3_032026   DEBN AEGPA3 I109165                    5.653.134,33       0,10 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN CPLD28_062027   DEBN CPLD28 I247951                      203.341,94       0,00 10403 - Títulos Privados-Debêntures simples                  CPLD - COPEL DISTRIBUICAO SA                                
DEBN CPLD28_062027   DEBN CPLD28 I247951                      207.470,70       0,00 10403 - Títulos Privados-Debêntures simples                  CPLD - COPEL DISTRIBUICAO SA                                
DEBN CPLD28_062027   DEBN CPLD28 I247951                      111.476,80       0,00 10403 - Títulos Privados-Debêntures simples                  CPLD - COPEL DISTRIBUICAO SA                                
DEBN CPLD28_062027   DEBN CPLD28 I247951                       89.800,75       0,00 10403 - Títulos Privados-Debêntures simples                  CPLD - COPEL DISTRIBUICAO SA                                
DEBN CPLD28_062027   DEBN CPLD28 I247951                   23.517.475,60       0,42 10403 - Títulos Privados-Debêntures simples                  CPLD - COPEL DISTRIBUICAO SA                                
DEBN CPLD28_062027   DEBN CPLD28 I247951                       33.030,16       0,00 10403 - Títulos Privados-Debêntures simples                  CPLD - COPEL DISTRIBUICAO SA                                
DEBN CPLD28_062027   DEBN CPLD28 I247951                      813.367,75       0,01 10403 - Títulos Privados-Debêntures simples                  CPLD - COPEL DISTRIBUICAO SA                                
DEBN CPLD28_062027   DEBN CPLD28 I247951                    2.405.008,70       0,04 10403 - Títulos Privados-Debêntures simples                  CPLD - COPEL DISTRIBUICAO SA                                
DEBN CPLD28_062027   DEBN CPLD28 I247951                      339.591,36       0,01 10403 - Títulos Privados-Debêntures simples                  CPLD - COPEL DISTRIBUICAO SA                                
DEBN CPLD28_062027   DEBN CPLD28 I247951                       93.929,52       0,00 10403 - Títulos Privados-Debêntures simples                  CPLD - COPEL DISTRIBUICAO SA                                
DEBN AEGPA3_032026   DEBN AEGPA3 I109165                      651.630,57       0,01 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN CPLD28_062027   DEBN CPLD28 I247951                        7.225,35       0,00 10403 - Títulos Privados-Debêntures simples                  CPLD - COPEL DISTRIBUICAO SA                                
DEBN CPLD28_062027   DEBN CPLD28 I247951                       29.933,58       0,00 10403 - Títulos Privados-Debêntures simples                  CPLD - COPEL DISTRIBUICAO SA                                
DEBN CPLD28_062027   DEBN CPLD28 I247951                      167.215,20       0,00 10403 - Títulos Privados-Debêntures simples                  CPLD - COPEL DISTRIBUICAO SA                                
DEBN CPLD28_062027   DEBN CPLD28 I247951                       19.611,66       0,00 10403 - Títulos Privados-Debêntures simples                  CPLD - COPEL DISTRIBUICAO SA                                
DEBN CPLD28_062027   DEBN CPLD28 I247951                      151.732,31       0,00 10403 - Títulos Privados-Debêntures simples                  CPLD - COPEL DISTRIBUICAO SA                                
DEBN CPLD28_062027   DEBN CPLD28 I247951                       86.704,18       0,00 10403 - Títulos Privados-Debêntures simples                  CPLD - COPEL DISTRIBUICAO SA                                
DEBN CPLD28_062027   DEBN CPLD28 I247951                       65.028,13       0,00 10403 - Títulos Privados-Debêntures simples                  CPLD - COPEL DISTRIBUICAO SA                                
DEBN CPLD38_062028   DEBN CPLD38 I247862                       33.540,97       0,00 10403 - Títulos Privados-Debêntures simples                  CPLD - COPEL DISTRIBUICAO SA                                
DEBN CPLD38_062028   DEBN CPLD38 I247862                       58.696,69       0,00 10403 - Títulos Privados-Debêntures simples                  CPLD - COPEL DISTRIBUICAO SA                                
DEBN CPLD38_062028   DEBN CPLD38 I247862                       28.300,19       0,00 10403 - Títulos Privados-Debêntures simples                  CPLD - COPEL DISTRIBUICAO SA                                
DEBN AEGPA7_092026   DEBN AEGPA7 I445412                    1.068.702,40       0,02 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN CPLD38_062028   DEBN CPLD38 I247862                       63.937,47       0,00 10403 - Títulos Privados-Debêntures simples                  CPLD - COPEL DISTRIBUICAO SA                                
DEBN CPLD38_062028   DEBN CPLD38 I247862                       63.937,47       0,00 10403 - Títulos Privados-Debêntures simples                  CPLD - COPEL DISTRIBUICAO SA                                
DEBN CPLD38_062028   DEBN CPLD38 I247862                       45.070,67       0,00 10403 - Títulos Privados-Debêntures simples                  CPLD - COPEL DISTRIBUICAO SA                                
DEBN CPLD38_062028   DEBN CPLD38 I247862                       51.359,60       0,00 10403 - Títulos Privados-Debêntures simples                  CPLD - COPEL DISTRIBUICAO SA                                
DEBN CPLD38_062028   DEBN CPLD38 I247862                       16.770,48       0,00 10403 - Títulos Privados-Debêntures simples                  CPLD - COPEL DISTRIBUICAO SA                                
DEBN CPLD38_062028   DEBN CPLD38 I247862                       58.696,69       0,00 10403 - Títulos Privados-Debêntures simples                  CPLD - COPEL DISTRIBUICAO SA                                
DEBN CPLD38_062028   DEBN CPLD38 I247862                       46.118,83       0,00 10403 - Títulos Privados-Debêntures simples                  CPLD - COPEL DISTRIBUICAO SA                                
DEBN CPLD38_062028   DEBN CPLD38 I247862                       45.070,67       0,00 10403 - Títulos Privados-Debêntures simples                  CPLD - COPEL DISTRIBUICAO SA                                
DEBN CPLD38_062028   DEBN CPLD38 I247862                      109.008,14       0,00 10403 - Títulos Privados-Debêntures simples                  CPLD - COPEL DISTRIBUICAO SA                                
DEBN CPLD38_062028   DEBN CPLD38 I247862                       10.481,55       0,00 10403 - Títulos Privados-Debêntures simples                  CPLD - COPEL DISTRIBUICAO SA                                
DEBN AEGPA0_052029   DEBN AEGPA0 H750651                       16.536,25       0,00 10440 - Títulos Privados-Debêntures Incent. (Lei 12.431)     AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN AEGPA7_092026   DEBN AEGPA7 I445412                      122.411,13       0,00 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN CPLD38_062028   DEBN CPLD38 I247862                      428.695,47       0,01 10403 - Títulos Privados-Debêntures simples                  CPLD - COPEL DISTRIBUICAO SA                                
DEBN CPLD38_062028   DEBN CPLD38 I247862                    1.266.171,46       0,02 10403 - Títulos Privados-Debêntures simples                  CPLD - COPEL DISTRIBUICAO SA                                
DEBN CPLD38_062028   DEBN CPLD38 I247862                       88.045,04       0,00 10403 - Títulos Privados-Debêntures simples                  CPLD - COPEL DISTRIBUICAO SA                                
DEBN CPLD38_062028   DEBN CPLD38 I247862                      106.911,83       0,00 10403 - Títulos Privados-Debêntures simples                  CPLD - COPEL DISTRIBUICAO SA                                
DEBN CPLD38_062028   DEBN CPLD38 I247862                       45.070,67       0,00 10403 - Títulos Privados-Debêntures simples                  CPLD - COPEL DISTRIBUICAO SA                                
DEBN CPLD38_062028   DEBN CPLD38 I247862                       34.589,12       0,00 10403 - Títulos Privados-Debêntures simples                  CPLD - COPEL DISTRIBUICAO SA                                
DEBN CPLD38_062028   DEBN CPLD38 I247862                       79.659,79       0,00 10403 - Títulos Privados-Debêntures simples                  CPLD - COPEL DISTRIBUICAO SA                                
DEBN CPLD38_062028   DEBN CPLD38 I247862                       20.963,10       0,00 10403 - Títulos Privados-Debêntures simples                  CPLD - COPEL DISTRIBUICAO SA                                
DEBN CPLD38_062028   DEBN CPLD38 I247862                        3.144,47       0,00 10403 - Títulos Privados-Debêntures simples                  CPLD - COPEL DISTRIBUICAO SA                                
DEBN CPLD38_062028   DEBN CPLD38 I247862                       15.722,33       0,00 10403 - Títulos Privados-Debêntures simples                  CPLD - COPEL DISTRIBUICAO SA                                
DEBN AEGPA7_092026   DEBN AEGPA7 I445412                      100.057,79       0,00 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN CPLD38_062028   DEBN CPLD38 I247862                       47.166,98       0,00 10403 - Títulos Privados-Debêntures simples                  CPLD - COPEL DISTRIBUICAO SA                                
DEBN CPLD38_062028   DEBN CPLD38 I247862                       50.311,45       0,00 10403 - Títulos Privados-Debêntures simples                  CPLD - COPEL DISTRIBUICAO SA                                
DEBN CPLD38_062028   DEBN CPLD38 I247862                   12.378.712,75       0,22 10403 - Títulos Privados-Debêntures simples                  CPLD - COPEL DISTRIBUICAO SA                                
DEBN CPLD38_062028   DEBN CPLD38 I247862                        5.240,78       0,00 10403 - Títulos Privados-Debêntures simples                  CPLD - COPEL DISTRIBUICAO SA                                
DEBN CPLD38_062028   DEBN CPLD38 I247862                       17.818,64       0,00 10403 - Títulos Privados-Debêntures simples                  CPLD - COPEL DISTRIBUICAO SA                                
DEBN CPLD38_062028   DEBN CPLD38 I247862                       16.770,48       0,00 10403 - Títulos Privados-Debêntures simples                  CPLD - COPEL DISTRIBUICAO SA                                
DEBN CRNP11_092025   DEBN CRNP11 I351399                    2.387.192,92       0,04 10448 - Titulos Privados-Debêntures SPE                      CRNP - CONCESSIONARIA DE RODOVIAS NOROESTE PAULISTA S.A.    
DEBN CRNP11_092025   DEBN CRNP11 I351399                      869.784,95       0,02 10448 - Titulos Privados-Debêntures SPE                      CRNP - CONCESSIONARIA DE RODOVIAS NOROESTE PAULISTA S.A.    
DEBN CRNP11_092025   DEBN CRNP11 I351399                    5.178.888,22       0,09 10448 - Titulos Privados-Debêntures SPE                      CRNP - CONCESSIONARIA DE RODOVIAS NOROESTE PAULISTA S.A.    
DEBN CRNP11_092025   DEBN CRNP11 I351399                       48.204,95       0,00 10448 - Titulos Privados-Debêntures SPE                      CRNP - CONCESSIONARIA DE RODOVIAS NOROESTE PAULISTA S.A.    
DEBN AEGPA7_092026   DEBN AEGPA7 I445412                        2.128,89       0,00 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN CRNP11_092025   DEBN CRNP11 I351399                      588.938,73       0,01 10448 - Titulos Privados-Debêntures SPE                      CRNP - CONCESSIONARIA DE RODOVIAS NOROESTE PAULISTA S.A.    
DEBN CRNP11_092025   DEBN CRNP11 I351399                   11.332.354,79       0,20 10448 - Titulos Privados-Debêntures SPE                      CRNP - CONCESSIONARIA DE RODOVIAS NOROESTE PAULISTA S.A.    
DEBN CRNP11_092025   DEBN CRNP11 I351399                       36.677,68       0,00 10448 - Titulos Privados-Debêntures SPE                      CRNP - CONCESSIONARIA DE RODOVIAS NOROESTE PAULISTA S.A.    
DEBN CRNP11_092025   DEBN CRNP11 I351399                       55.540,48       0,00 10448 - Titulos Privados-Debêntures SPE                      CRNP - CONCESSIONARIA DE RODOVIAS NOROESTE PAULISTA S.A.    
DEBN CRNP11_092025   DEBN CRNP11 I351399                    2.972.987,84       0,05 10448 - Titulos Privados-Debêntures SPE                      CRNP - CONCESSIONARIA DE RODOVIAS NOROESTE PAULISTA S.A.    
DEBN CRNP11_092025   DEBN CRNP11 I351399                       37.725,61       0,00 10448 - Titulos Privados-Debêntures SPE                      CRNP - CONCESSIONARIA DE RODOVIAS NOROESTE PAULISTA S.A.    
DEBN CRNP11_092025   DEBN CRNP11 I351399                       26.198,34       0,00 10448 - Titulos Privados-Debêntures SPE                      CRNP - CONCESSIONARIA DE RODOVIAS NOROESTE PAULISTA S.A.    
DEBN CRNP11_092025   DEBN CRNP11 I351399                       39.821,48       0,00 10448 - Titulos Privados-Debêntures SPE                      CRNP - CONCESSIONARIA DE RODOVIAS NOROESTE PAULISTA S.A.    
DEBN CRNP11_092025   DEBN CRNP11 I351399                    3.248.594,40       0,06 10448 - Titulos Privados-Debêntures SPE                      CRNP - CONCESSIONARIA DE RODOVIAS NOROESTE PAULISTA S.A.    
DEBN CRNP11_092025   DEBN CRNP11 I351399                    1.326.684,04       0,02 10448 - Titulos Privados-Debêntures SPE                      CRNP - CONCESSIONARIA DE RODOVIAS NOROESTE PAULISTA S.A.    
DEBN AEGPA7_092026   DEBN AEGPA7 I445412                       14.902,22       0,00 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN CRNP11_092025   DEBN CRNP11 I351399                       58.684,29       0,00 10448 - Titulos Privados-Debêntures SPE                      CRNP - CONCESSIONARIA DE RODOVIAS NOROESTE PAULISTA S.A.    
DEBN CRNP11_092025   DEBN CRNP11 I351399                      251.504,08       0,00 10448 - Titulos Privados-Debêntures SPE                      CRNP - CONCESSIONARIA DE RODOVIAS NOROESTE PAULISTA S.A.    
DEBN CRNP11_092025   DEBN CRNP11 I351399                       17.814,87       0,00 10448 - Titulos Privados-Debêntures SPE                      CRNP - CONCESSIONARIA DE RODOVIAS NOROESTE PAULISTA S.A.    
DEBN CRNP11_092025   DEBN CRNP11 I351399                    3.975.860,39       0,07 10448 - Titulos Privados-Debêntures SPE                      CRNP - CONCESSIONARIA DE RODOVIAS NOROESTE PAULISTA S.A.    
DEBN CRNP11_092025   DEBN CRNP11 I351399                       38.773,55       0,00 10448 - Titulos Privados-Debêntures SPE                      CRNP - CONCESSIONARIA DE RODOVIAS NOROESTE PAULISTA S.A.    
DEBN CRNP11_092025   DEBN CRNP11 I351399                       80.690,89       0,00 10448 - Titulos Privados-Debêntures SPE                      CRNP - CONCESSIONARIA DE RODOVIAS NOROESTE PAULISTA S.A.    
DEBN CRNP11_092025   DEBN CRNP11 I351399                   41.699.376,88       0,75 10448 - Titulos Privados-Debêntures SPE                      CRNP - CONCESSIONARIA DE RODOVIAS NOROESTE PAULISTA S.A.    
DEBN CRNP11_092025   DEBN CRNP11 I351399                      470.522,22       0,01 10448 - Titulos Privados-Debêntures SPE                      CRNP - CONCESSIONARIA DE RODOVIAS NOROESTE PAULISTA S.A.    
DEBN CRNP11_092025   DEBN CRNP11 I351399                    4.396.081,80       0,08 10448 - Titulos Privados-Debêntures SPE                      CRNP - CONCESSIONARIA DE RODOVIAS NOROESTE PAULISTA S.A.    
DEBN CRNP11_092025   DEBN CRNP11 I351399                   16.667.385,13       0,30 10448 - Titulos Privados-Debêntures SPE                      CRNP - CONCESSIONARIA DE RODOVIAS NOROESTE PAULISTA S.A.    
DEBN AEGPA7_092026   DEBN AEGPA7 I445412                       17.031,11       0,00 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN CRNP11_092025   DEBN CRNP11 I351399                       46.109,08       0,00 10448 - Titulos Privados-Debêntures SPE                      CRNP - CONCESSIONARIA DE RODOVIAS NOROESTE PAULISTA S.A.    
DEBN CRNP11_092025   DEBN CRNP11 I351399                      307.044,57       0,01 10448 - Titulos Privados-Debêntures SPE                      CRNP - CONCESSIONARIA DE RODOVIAS NOROESTE PAULISTA S.A.    
DEBN CRNP11_092025   DEBN CRNP11 I351399                    7.162.626,68       0,13 10448 - Titulos Privados-Debêntures SPE                      CRNP - CONCESSIONARIA DE RODOVIAS NOROESTE PAULISTA S.A.    
DEBN CRNP11_092025   DEBN CRNP11 I351399                    3.470.756,34       0,06 10448 - Titulos Privados-Debêntures SPE                      CRNP - CONCESSIONARIA DE RODOVIAS NOROESTE PAULISTA S.A.    
DEBN CRNP11_092025   DEBN CRNP11 I351399                    2.021.464,07       0,04 10448 - Titulos Privados-Debêntures SPE                      CRNP - CONCESSIONARIA DE RODOVIAS NOROESTE PAULISTA S.A.    
DEBN CRNP11_092025   DEBN CRNP11 I351399                      645.527,15       0,01 10448 - Titulos Privados-Debêntures SPE                      CRNP - CONCESSIONARIA DE RODOVIAS NOROESTE PAULISTA S.A.    
DEBN CRNP11_092025   DEBN CRNP11 I351399                      107.937,17       0,00 10448 - Titulos Privados-Debêntures SPE                      CRNP - CONCESSIONARIA DE RODOVIAS NOROESTE PAULISTA S.A.    
DEBN CRNP11_092025   DEBN CRNP11 I351399                      313.332,17       0,01 10448 - Titulos Privados-Debêntures SPE                      CRNP - CONCESSIONARIA DE RODOVIAS NOROESTE PAULISTA S.A.    
DEBN CRNP11_092025   DEBN CRNP11 I351399                      535.494,11       0,01 10448 - Titulos Privados-Debêntures SPE                      CRNP - CONCESSIONARIA DE RODOVIAS NOROESTE PAULISTA S.A.    
DEBN CRNP11_092025   DEBN CRNP11 I351399                      166.621,45       0,00 10448 - Titulos Privados-Debêntures SPE                      CRNP - CONCESSIONARIA DE RODOVIAS NOROESTE PAULISTA S.A.    
DEBN AEGPA7_092026   DEBN AEGPA7 I445412                       20.224,45       0,00 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN CRNP11_092025   DEBN CRNP11 I351399                    2.133.592,97       0,04 10448 - Titulos Privados-Debêntures SPE                      CRNP - CONCESSIONARIA DE RODOVIAS NOROESTE PAULISTA S.A.    
DEBN CRNP11_092025   DEBN CRNP11 I351399                       18.862,81       0,00 10448 - Titulos Privados-Debêntures SPE                      CRNP - CONCESSIONARIA DE RODOVIAS NOROESTE PAULISTA S.A.    
DEBN CRNP11_092025   DEBN CRNP11 I351399                       36.677,68       0,00 10448 - Titulos Privados-Debêntures SPE                      CRNP - CONCESSIONARIA DE RODOVIAS NOROESTE PAULISTA S.A.    
DEBN CRNP11_092025   DEBN CRNP11 I351399                       40.869,41       0,00 10448 - Titulos Privados-Debêntures SPE                      CRNP - CONCESSIONARIA DE RODOVIAS NOROESTE PAULISTA S.A.    
DEBN CRNP11_092025   DEBN CRNP11 I351399                      495.672,63       0,01 10448 - Titulos Privados-Debêntures SPE                      CRNP - CONCESSIONARIA DE RODOVIAS NOROESTE PAULISTA S.A.    
DEBN CRNP11_092025   DEBN CRNP11 I351399                    1.637.920,34       0,03 10448 - Titulos Privados-Debêntures SPE                      CRNP - CONCESSIONARIA DE RODOVIAS NOROESTE PAULISTA S.A.    
DEBN CRNP11_092025   DEBN CRNP11 I351399                    2.690.045,76       0,05 10448 - Titulos Privados-Debêntures SPE                      CRNP - CONCESSIONARIA DE RODOVIAS NOROESTE PAULISTA S.A.    
DEBN CRNP11_092025   DEBN CRNP11 I351399                       19.910,74       0,00 10448 - Titulos Privados-Debêntures SPE                      CRNP - CONCESSIONARIA DE RODOVIAS NOROESTE PAULISTA S.A.    
DEBN CRNP11_092025   DEBN CRNP11 I351399                       44.013,21       0,00 10448 - Titulos Privados-Debêntures SPE                      CRNP - CONCESSIONARIA DE RODOVIAS NOROESTE PAULISTA S.A.    
DEBN CRNP11_092025   DEBN CRNP11 I351399                      166.621,45       0,00 10448 - Titulos Privados-Debêntures SPE                      CRNP - CONCESSIONARIA DE RODOVIAS NOROESTE PAULISTA S.A.    
DEBN AEGPA7_092026   DEBN AEGPA7 I445412                       20.224,45       0,00 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN CSAN15_042028   DEBN CSAN15 I169186                       60.446,26       0,00 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN15_042028   DEBN CSAN15 I169186                       29.692,90       0,00 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN15_042028   DEBN CSAN15 I169186                    3.250.312,40       0,06 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN15_042028   DEBN CSAN15 I169186                      100.743,78       0,00 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN15_042028   DEBN CSAN15 I169186                      922.600,91       0,02 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN15_042028   DEBN CSAN15 I169186                      100.743,78       0,00 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN15_042028   DEBN CSAN15 I169186                      632.034,65       0,01 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN15_042028   DEBN CSAN15 I169186                      155.887,74       0,00 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN15_042028   DEBN CSAN15 I169186                      306.473,18       0,01 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN15_042028   DEBN CSAN15 I169186                      419.942,48       0,01 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN AEGPA7_092026   DEBN AEGPA7 I445412                       18.095,56       0,00 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN CSAN15_042028   DEBN CSAN15 I169186                      310.715,02       0,01 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN15_042028   DEBN CSAN15 I169186                      446.454,00       0,01 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN15_042028   DEBN CSAN15 I169186                    3.190.926,60       0,06 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN15_042028   DEBN CSAN15 I169186                    2.744.472,59       0,05 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN15_042028   DEBN CSAN15 I169186                       59.385,81       0,00 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN15_042028   DEBN CSAN15 I169186                      143.162,21       0,00 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN15_042028   DEBN CSAN15 I169186                    2.817.644,39       0,05 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN15_042028   DEBN CSAN15 I169186                      207.850,32       0,00 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN15_042028   DEBN CSAN15 I169186                      362.677,60       0,01 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN15_042028   DEBN CSAN15 I169186                      659.606,63       0,01 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN AEGPA7_092026   DEBN AEGPA7 I445412                       55.351,12       0,00 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN CSAN15_042028   DEBN CSAN15 I169186                      390.249,58       0,01 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN15_042028   DEBN CSAN15 I169186                    1.606.598,14       0,03 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN15_042028   DEBN CSAN15 I169186                      153.766,82       0,00 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN15_042028   DEBN CSAN15 I169186                       99.683,32       0,00 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN15_042028   DEBN CSAN15 I169186                      431.607,55       0,01 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN15_042028   DEBN CSAN15 I169186                      495.235,20       0,01 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN15_042028   DEBN CSAN15 I169186                      575.830,22       0,01 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN15_042028   DEBN CSAN15 I169186                       74.232,26       0,00 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN15_042028   DEBN CSAN15 I169186                      433.728,47       0,01 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN15_042028   DEBN CSAN15 I169186                      316.017,32       0,01 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN AEGPA7_092026   DEBN AEGPA7 I445412                        9.580,00       0,00 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN CSAN15_042028   DEBN CSAN15 I169186                      503.718,89       0,01 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN15_042028   DEBN CSAN15 I169186                      408.277,41       0,01 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN15_042028   DEBN CSAN15 I169186                      290.566,26       0,01 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN15_042028   DEBN CSAN15 I169186                      221.636,31       0,00 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN15_042028   DEBN CSAN15 I169186                    4.546.195,52       0,08 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN15_042028   DEBN CSAN15 I169186                      125.134,38       0,00 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN15_042028   DEBN CSAN15 I169186                    1.773.090,48       0,03 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN15_042028   DEBN CSAN15 I169186                      125.134,38       0,00 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN15_042028   DEBN CSAN15 I169186                       55.143,96       0,00 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN15_042028   DEBN CSAN15 I169186                       83.776,40       0,00 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN AEGPA0_052029   DEBN AEGPA0 H750651                        3.100,55       0,00 10440 - Títulos Privados-Debêntures Incent. (Lei 12.431)     AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN AEGPA7_092026   DEBN AEGPA7 I445412                       32.997,78       0,00 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN CSAN15_042028   DEBN CSAN15 I169186                      376.463,59       0,01 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN15_042028   DEBN CSAN15 I169186                      643.699,72       0,01 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN15_042028   DEBN CSAN15 I169186                      347.831,15       0,01 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN15_042028   DEBN CSAN15 I169186                      158.008,66       0,00 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN16_062028   DEBN CSAN16 I265153                      118.966,06       0,00 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN16_062028   DEBN CSAN16 I265153                      446.898,58       0,01 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN16_062028   DEBN CSAN16 I265153                      421.036,39       0,01 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN16_062028   DEBN CSAN16 I265153                    1.703.800,83       0,03 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN16_062028   DEBN CSAN16 I265153                      417.932,93       0,01 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN16_062028   DEBN CSAN16 I265153                    2.026.560,91       0,04 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN AEGPA7_092026   DEBN AEGPA7 I445412                       15.966,67       0,00 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN CSAN16_062028   DEBN CSAN16 I265153                       83.793,48       0,00 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN16_062028   DEBN CSAN16 I265153                      555.519,76       0,01 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN16_062028   DEBN CSAN16 I265153                      652.761,58       0,01 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN16_062028   DEBN CSAN16 I265153                      527.588,60       0,01 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN16_062028   DEBN CSAN16 I265153                      850.348,69       0,02 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN16_062028   DEBN CSAN16 I265153                      210.000,95       0,00 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN16_062028   DEBN CSAN16 I265153                      411.726,00       0,01 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN16_062028   DEBN CSAN16 I265153                      566.899,12       0,01 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN16_062028   DEBN CSAN16 I265153                      317.587,65       0,01 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN16_062028   DEBN CSAN16 I265153                      605.175,16       0,01 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN AEGPA7_092026   DEBN AEGPA7 I445412                       24.482,23       0,00 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN CSAN16_062028   DEBN CSAN16 I265153                      134.483,37       0,00 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN16_062028   DEBN CSAN16 I265153                    2.373.114,21       0,04 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN16_062028   DEBN CSAN16 I265153                       83.793,48       0,00 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN16_062028   DEBN CSAN16 I265153                    8.194.175,08       0,15 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN16_062028   DEBN CSAN16 I265153                      789.313,92       0,01 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN16_062028   DEBN CSAN16 I265153                    7.286.929,59       0,13 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN16_062028   DEBN CSAN16 I265153                       78.621,05       0,00 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN16_062028   DEBN CSAN16 I265153                       41.379,50       0,00 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN16_062028   DEBN CSAN16 I265153                    4.347.950,75       0,08 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN16_062028   DEBN CSAN16 I265153                      724.141,21       0,01 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN AEGPA7_092026   DEBN AEGPA7 I445412                      222.468,93       0,00 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN CSAN16_062028   DEBN CSAN16 I265153                    2.160.009,79       0,04 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN16_062028   DEBN CSAN16 I265153                       55.862,32       0,00 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN16_062028   DEBN CSAN16 I265153                      652.761,58       0,01 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN16_062028   DEBN CSAN16 I265153                    1.648.972,99       0,03 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN16_062028   DEBN CSAN16 I265153                       65.172,71       0,00 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN16_062028   DEBN CSAN16 I265153                       97.241,82       0,00 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN16_062028   DEBN CSAN16 I265153                      146.897,22       0,00 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN16_062028   DEBN CSAN16 I265153                    3.276.221,75       0,06 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN16_062028   DEBN CSAN16 I265153                    1.185.522,62       0,02 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN16_062028   DEBN CSAN16 I265153                       65.172,71       0,00 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN AEGPA7_092026   DEBN AEGPA7 I445412                        6.386,67       0,00 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN CSAN16_062028   DEBN CSAN16 I265153                      728.279,17       0,01 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN16_062028   DEBN CSAN16 I265153                      655.865,04       0,01 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN16_062028   DEBN CSAN16 I265153                       91.034,90       0,00 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN16_062028   DEBN CSAN16 I265153                      184.138,77       0,00 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN16_062028   DEBN CSAN16 I265153                      243.104,55       0,00 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN16_062028   DEBN CSAN16 I265153                      263.794,30       0,00 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN18_012031   DEBN CSAN18 I528962                      534.945,42       0,01 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN18_012031   DEBN CSAN18 I528962                       18.306,12       0,00 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN18_012031   DEBN CSAN18 I528962                       92.547,59       0,00 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN18_012031   DEBN CSAN18 I528962                       39.663,25       0,00 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN AEGPA7_092026   DEBN AEGPA7 I445412                        9.580,00       0,00 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN CSAN18_012031   DEBN CSAN18 I528962                       35.595,23       0,00 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN18_012031   DEBN CSAN18 I528962                    5.013.842,07       0,09 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN18_012031   DEBN CSAN18 I528962                    2.388.948,28       0,04 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN18_012031   DEBN CSAN18 I528962                    7.905.191,57       0,14 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN18_012031   DEBN CSAN18 I528962                    4.938.583,59       0,09 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN18_012031   DEBN CSAN18 I528962                    4.010.056,65       0,07 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN18_012031   DEBN CSAN18 I528962                    1.789.931,45       0,03 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN18_012031   DEBN CSAN18 I528962                       74.241,47       0,00 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN18_012031   DEBN CSAN18 I528962                    3.990.733,53       0,07 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN23_082031   DEBN CSAN23 I298100                        4.329,77       0,00 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN AEGPA7_092026   DEBN AEGPA7 I445412                       24.482,23       0,00 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN CSAN23_082031   DEBN CSAN23 I298100                      507.665,74       0,01 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN23_082031   DEBN CSAN23 I298100                       32.473,29       0,00 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN23_082031   DEBN CSAN23 I298100                       40.050,39       0,00 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN23_082031   DEBN CSAN23 I298100                       75.771,01       0,00 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN23_082031   DEBN CSAN23 I298100                      121.233,61       0,00 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN23_082031   DEBN CSAN23 I298100                      218.653,47       0,00 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN23_082031   DEBN CSAN23 I298100                       14.071,76       0,00 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN23_082031   DEBN CSAN23 I298100                       20.566,42       0,00 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN23_082031   DEBN CSAN23 I298100                        8.659,54       0,00 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN23_082031   DEBN CSAN23 I298100                       12.989,32       0,00 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN AEGPA7_092026   DEBN AEGPA7 I445412                       37.255,56       0,00 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN CSAN23_082031   DEBN CSAN23 I298100                       19.483,97       0,00 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN23_082031   DEBN CSAN23 I298100                       16.236,64       0,00 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN23_082031   DEBN CSAN23 I298100                       60.616,80       0,00 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN23_082031   DEBN CSAN23 I298100                       87.677,88       0,00 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN23_082031   DEBN CSAN23 I298100                       84.430,55       0,00 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN23_082031   DEBN CSAN23 I298100                      101.749,64       0,00 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN23_082031   DEBN CSAN23 I298100                       23.813,74       0,00 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN23_082031   DEBN CSAN23 I298100                       37.885,50       0,00 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN23_082031   DEBN CSAN23 I298100                       29.225,96       0,00 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN23_082031   DEBN CSAN23 I298100                       12.989,32       0,00 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN AEGPA7_092026   DEBN AEGPA7 I445412                       12.773,34       0,00 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN CSAN23_082031   DEBN CSAN23 I298100                      143.964,91       0,00 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN23_082031   DEBN CSAN23 I298100                      112.574,07       0,00 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN23_082031   DEBN CSAN23 I298100                       42.215,27       0,00 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN23_082031   DEBN CSAN23 I298100                       81.183,22       0,00 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN23_082031   DEBN CSAN23 I298100                       58.451,92       0,00 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN23_082031   DEBN CSAN23 I298100                       28.143,52       0,00 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN23_082031   DEBN CSAN23 I298100                    1.777.371,31       0,03 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN23_082031   DEBN CSAN23 I298100                      784.771,13       0,01 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN23_082031   DEBN CSAN23 I298100                        9.741,99       0,00 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN23_082031   DEBN CSAN23 I298100                        8.659,55       0,00 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN AEGPA7_092026   DEBN AEGPA7 I445412                        1.064,44       0,00 10403 - Títulos Privados-Debêntures simples                  AEGP - AEGEA SANEAMENTO PARTICIPACOES SA                    
DEBN CSAN24_052032   DEBN CSAN24 I373524                       20.931,61       0,00 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN24_052032   DEBN CSAN24 I373524                       11.512,39       0,00 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN24_052032   DEBN CSAN24 I373524                    1.937.221,29       0,03 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN24_052032   DEBN CSAN24 I373524                       63.841,44       0,00 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN24_052032   DEBN CSAN24 I373524                    1.177.403,54       0,02 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN24_052032   DEBN CSAN24 I373524                       62.794,86       0,00 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN24_052032   DEBN CSAN24 I373524                       52.329,05       0,00 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN24_052032   DEBN CSAN24 I373524                      188.384,57       0,00 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN24_052032   DEBN CSAN24 I373524                    1.331.250,94       0,02 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
DEBN CSAN24_052032   DEBN CSAN24 I373524                       24.071,36       0,00 10403 - Títulos Privados-Debêntures simples                  CSAN - COSAN SA                                             
"""
    #display(tabela_texto_memoria_para_df(txt))
    #print(agrupa_ativos(txt))
    df = tabela_texto_memoria_para_df(txt)
    print(df.display())

    

