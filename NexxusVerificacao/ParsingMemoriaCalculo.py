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
============================
== ATIVOS SEM PRAZO MEDIO ==
============================
 
DEBN FLCLA8_122029

MEMÓRIA DE CÁLCULO (PROCESSAMENTO)
----------------------------------

TÍTULO               NOME                           POSIÇÃO              %PL        GRUPO                                                        EMISSOR
-------------------- ------------------------------ -------------------- ---------- ------------------------------------------------------------ ------------------------------------------------------------
DEBN FLCLA8_122029   DEBN FLCLA8_122029                       126.035,60       0,01 10403 - Títulos Privados-Debêntures simples                  FLCL - ENERGISA MINAS RIO - DISTRIBUIDORA DE ENERGIA SA     
"""

    #display(tabela_texto_memoria_para_df(txt))
    print(agrupa_ativos(txt))
    #df = tabela_texto_memoria_para_df(txt)
     # display(df)

