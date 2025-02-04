from io import StringIO
import pandas as pd


def __chega_final_texto(texto_memoria:str)->str:
    index1 = texto_memoria.find("MEMÓRIA DE CÁLCULO (PROCESSAMENTO)") #index do final da string, perto das colunas
    index_coluna = texto_memoria.find("TÍTULO",index1) #index da primeira coluna (TITULO)
    texto_final = texto_memoria[index_coluna:]

    linhas = texto_final.splitlines()
    apenas_linhas_dados = "\n".join(linhas[2:]) #pula linha de coluna e linhas tracejadas

    return apenas_linhas_dados


def texto_memoria_para_df(texto:str)->pd.DataFrame:
  
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


if __name__ == "__main__":
    df = texto_memoria_para_df(
        """
        
        
        TITULO: DEBN TJMM11 / EMISSOR: TJMM
ID AG: 2 LIM1: 6 LIM2: 22 RATING: -1 (EMISSOR)
ID AG: 3 LIM1: 6 LIM2: 20 RATING: 1 (TITULO)
ID AG: 1 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 9 LIM1: 6 LIM2: 20 RATING: -1 (EMISSOR)
ID AG: 11 LIM1: 4 LIM2: 10 RATING: -1 (EMISSOR)
ID AG: 13 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 14 LIM1: 2 LIM2: 5 RATING: -1 (EMISSOR)
ID AG: 15 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 16 LIM1: 6 LIM2: 22 RATING: -1 (EMISSOR)
[*ATIVO DESCONSIDERADO NA REGRA*] PIOR RATING PELA AGJNCIA ID: 3 RATING DE ORDEM: 1 / POSIGCO: 3.881.803,04
 
TITULO: DEBN VNYD12 / EMISSOR: VNYD
ID AG: 2 LIM1: 6 LIM2: 22 RATING: -1 (EMISSOR)
ID AG: 3 LIM1: 6 LIM2: 20 RATING: 1 (TITULO)
ID AG: 1 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 9 LIM1: 6 LIM2: 20 RATING: -1 (EMISSOR)
ID AG: 11 LIM1: 4 LIM2: 10 RATING: -1 (EMISSOR)
ID AG: 13 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 14 LIM1: 2 LIM2: 5 RATING: -1 (EMISSOR)
ID AG: 15 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 16 LIM1: 6 LIM2: 22 RATING: -1 (EMISSOR)
[*ATIVO DESCONSIDERADO NA REGRA*] PIOR RATING PELA AGJNCIA ID: 3 RATING DE ORDEM: 1 / POSIGCO: 906.748,58
 
TITULO: DEBN TRPI13 / EMISSOR: TRPI
ID AG: 2 LIM1: 6 LIM2: 22 RATING: -1 (EMISSOR)
ID AG: 3 LIM1: 6 LIM2: 20 RATING: -1 (EMISSOR)
ID AG: 1 LIM1: 6 LIM2: 21 RATING: 1 (TITULO)
ID AG: 9 LIM1: 6 LIM2: 20 RATING: -1 (EMISSOR)
ID AG: 11 LIM1: 4 LIM2: 10 RATING: -1 (EMISSOR)
ID AG: 13 LIM1: 6 LIM2: 21 RATING: 1 (TITULO)
ID AG: 14 LIM1: 2 LIM2: 5 RATING: -1 (EMISSOR)
ID AG: 15 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 16 LIM1: 6 LIM2: 22 RATING: -1 (EMISSOR)
[*ATIVO DESCONSIDERADO NA REGRA*] PIOR RATING PELA AGJNCIA ID: 1 RATING DE ORDEM: 1 / POSIGCO: 5.103.342,30
 
TITULO: DEBN TRPI13 / EMISSOR: TRPI
ID AG: 2 LIM1: 6 LIM2: 22 RATING: -1 (EMISSOR)
ID AG: 3 LIM1: 6 LIM2: 20 RATING: -1 (EMISSOR)
ID AG: 1 LIM1: 6 LIM2: 21 RATING: 1 (TITULO)
ID AG: 9 LIM1: 6 LIM2: 20 RATING: -1 (EMISSOR)
ID AG: 11 LIM1: 4 LIM2: 10 RATING: -1 (EMISSOR)
ID AG: 13 LIM1: 6 LIM2: 21 RATING: 1 (TITULO)
ID AG: 14 LIM1: 2 LIM2: 5 RATING: -1 (EMISSOR)
ID AG: 15 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 16 LIM1: 6 LIM2: 22 RATING: -1 (EMISSOR)
[*ATIVO DESCONSIDERADO NA REGRA*] PIOR RATING PELA AGJNCIA ID: 1 RATING DE ORDEM: 1 / POSIGCO: 815.334,28
 
TITULO: DEBN TRPI13 / EMISSOR: TRPI
ID AG: 2 LIM1: 6 LIM2: 22 RATING: -1 (EMISSOR)
ID AG: 3 LIM1: 6 LIM2: 20 RATING: -1 (EMISSOR)
ID AG: 1 LIM1: 6 LIM2: 21 RATING: 1 (TITULO)
ID AG: 9 LIM1: 6 LIM2: 20 RATING: -1 (EMISSOR)
ID AG: 11 LIM1: 4 LIM2: 10 RATING: -1 (EMISSOR)
ID AG: 13 LIM1: 6 LIM2: 21 RATING: 1 (TITULO)
ID AG: 14 LIM1: 2 LIM2: 5 RATING: -1 (EMISSOR)
ID AG: 15 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 16 LIM1: 6 LIM2: 22 RATING: -1 (EMISSOR)
[*ATIVO DESCONSIDERADO NA REGRA*] PIOR RATING PELA AGJNCIA ID: 1 RATING DE ORDEM: 1 / POSIGCO: 3.570.213,74
 
TITULO: DEBN TJMM11 / EMISSOR: TJMM
ID AG: 2 LIM1: 6 LIM2: 22 RATING: -1 (EMISSOR)
ID AG: 3 LIM1: 6 LIM2: 20 RATING: 1 (TITULO)
ID AG: 1 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 9 LIM1: 6 LIM2: 20 RATING: -1 (EMISSOR)
ID AG: 11 LIM1: 4 LIM2: 10 RATING: -1 (EMISSOR)
ID AG: 13 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 14 LIM1: 2 LIM2: 5 RATING: -1 (EMISSOR)
ID AG: 15 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 16 LIM1: 6 LIM2: 22 RATING: -1 (EMISSOR)
[*ATIVO DESCONSIDERADO NA REGRA*] PIOR RATING PELA AGJNCIA ID: 3 RATING DE ORDEM: 1 / POSIGCO: 1.743.647,22
 
TITULO: DEBN VNYD12 / EMISSOR: VNYD
ID AG: 2 LIM1: 6 LIM2: 22 RATING: -1 (EMISSOR)
ID AG: 3 LIM1: 6 LIM2: 20 RATING: 1 (TITULO)
ID AG: 1 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 9 LIM1: 6 LIM2: 20 RATING: -1 (EMISSOR)
ID AG: 11 LIM1: 4 LIM2: 10 RATING: -1 (EMISSOR)
ID AG: 13 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 14 LIM1: 2 LIM2: 5 RATING: -1 (EMISSOR)
ID AG: 15 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 16 LIM1: 6 LIM2: 22 RATING: -1 (EMISSOR)
[*ATIVO DESCONSIDERADO NA REGRA*] PIOR RATING PELA AGJNCIA ID: 3 RATING DE ORDEM: 1 / POSIGCO: 4.294.701,46
 
TITULO: DEBN TAEE18 / EMISSOR: TAEE
ID AG: 2 LIM1: 6 LIM2: 22 RATING: -1 (EMISSOR)
ID AG: 3 LIM1: 6 LIM2: 20 RATING: 1 (EMISSOR)
ID AG: 1 LIM1: 6 LIM2: 21 RATING: 1 (TITULO)
ID AG: 9 LIM1: 6 LIM2: 20 RATING: -1 (EMISSOR)
ID AG: 11 LIM1: 4 LIM2: 10 RATING: -1 (EMISSOR)
ID AG: 13 LIM1: 6 LIM2: 21 RATING: 1 (TITULO)
ID AG: 14 LIM1: 2 LIM2: 5 RATING: -1 (EMISSOR)
ID AG: 15 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 16 LIM1: 6 LIM2: 22 RATING: -1 (EMISSOR)
[*ATIVO DESCONSIDERADO NA REGRA*] PIOR RATING PELA AGJNCIA ID: 3 RATING DE ORDEM: 1 / POSIGCO: 7.786.941,49
 
TITULO: DEBN SOTE11 / EMISSOR: SOTE
ID AG: 2 LIM1: 6 LIM2: 22 RATING: -1 (EMISSOR)
ID AG: 3 LIM1: 6 LIM2: 20 RATING: 1 (TITULO)
ID AG: 1 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 9 LIM1: 6 LIM2: 20 RATING: -1 (EMISSOR)
ID AG: 11 LIM1: 4 LIM2: 10 RATING: -1 (EMISSOR)
ID AG: 13 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 14 LIM1: 2 LIM2: 5 RATING: -1 (EMISSOR)
ID AG: 15 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 16 LIM1: 6 LIM2: 22 RATING: -1 (EMISSOR)
[*ATIVO DESCONSIDERADO NA REGRA*] PIOR RATING PELA AGJNCIA ID: 3 RATING DE ORDEM: 1 / POSIGCO: 3.476.116,64
 
TITULO: DEBN SPLV11 / EMISSOR: SPLV
ID AG: 2 LIM1: 6 LIM2: 22 RATING: -1 (EMISSOR)
ID AG: 3 LIM1: 6 LIM2: 20 RATING: 2 (TITULO)
ID AG: 1 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 9 LIM1: 6 LIM2: 20 RATING: -1 (EMISSOR)
ID AG: 11 LIM1: 4 LIM2: 10 RATING: -1 (EMISSOR)
ID AG: 13 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 14 LIM1: 2 LIM2: 5 RATING: -1 (EMISSOR)
ID AG: 15 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 16 LIM1: 6 LIM2: 22 RATING: -1 (EMISSOR)
[*ATIVO DESCONSIDERADO NA REGRA*] PIOR RATING PELA AGJNCIA ID: 3 RATING DE ORDEM: 2 / POSIGCO: 5.172.047,56
 
TITULO: DEBN SPLV11 / EMISSOR: SPLV
ID AG: 2 LIM1: 6 LIM2: 22 RATING: -1 (EMISSOR)
ID AG: 3 LIM1: 6 LIM2: 20 RATING: 2 (TITULO)
ID AG: 1 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 9 LIM1: 6 LIM2: 20 RATING: -1 (EMISSOR)
ID AG: 11 LIM1: 4 LIM2: 10 RATING: -1 (EMISSOR)
ID AG: 13 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 14 LIM1: 2 LIM2: 5 RATING: -1 (EMISSOR)
ID AG: 15 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 16 LIM1: 6 LIM2: 22 RATING: -1 (EMISSOR)
[*ATIVO DESCONSIDERADO NA REGRA*] PIOR RATING PELA AGJNCIA ID: 3 RATING DE ORDEM: 2 / POSIGCO: 673.206,19
 
TITULO: DEBN TJMM11 / EMISSOR: TJMM
ID AG: 2 LIM1: 6 LIM2: 22 RATING: -1 (EMISSOR)
ID AG: 3 LIM1: 6 LIM2: 20 RATING: 1 (TITULO)
ID AG: 1 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 9 LIM1: 6 LIM2: 20 RATING: -1 (EMISSOR)
ID AG: 11 LIM1: 4 LIM2: 10 RATING: -1 (EMISSOR)
ID AG: 13 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 14 LIM1: 2 LIM2: 5 RATING: -1 (EMISSOR)
ID AG: 15 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 16 LIM1: 6 LIM2: 22 RATING: -1 (EMISSOR)
[*ATIVO DESCONSIDERADO NA REGRA*] PIOR RATING PELA AGJNCIA ID: 3 RATING DE ORDEM: 1 / POSIGCO: 1.782.694,15
 
TITULO: DEBN TAEE18 / EMISSOR: TAEE
ID AG: 2 LIM1: 6 LIM2: 22 RATING: -1 (EMISSOR)
ID AG: 3 LIM1: 6 LIM2: 20 RATING: 1 (EMISSOR)
ID AG: 1 LIM1: 6 LIM2: 21 RATING: 1 (TITULO)
ID AG: 9 LIM1: 6 LIM2: 20 RATING: -1 (EMISSOR)
ID AG: 11 LIM1: 4 LIM2: 10 RATING: -1 (EMISSOR)
ID AG: 13 LIM1: 6 LIM2: 21 RATING: 1 (TITULO)
ID AG: 14 LIM1: 2 LIM2: 5 RATING: -1 (EMISSOR)
ID AG: 15 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 16 LIM1: 6 LIM2: 22 RATING: -1 (EMISSOR)
[*ATIVO DESCONSIDERADO NA REGRA*] PIOR RATING PELA AGJNCIA ID: 3 RATING DE ORDEM: 1 / POSIGCO: 888.853,27
 
TITULO: DEBN ARCV12 / EMISSOR: ARCV
ID AG: 2 LIM1: 6 LIM2: 22 RATING: -1 (EMISSOR)
ID AG: 3 LIM1: 6 LIM2: 20 RATING: 1 (TITULO)
ID AG: 1 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 9 LIM1: 6 LIM2: 20 RATING: -1 (EMISSOR)
ID AG: 11 LIM1: 4 LIM2: 10 RATING: -1 (EMISSOR)
ID AG: 13 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 14 LIM1: 2 LIM2: 5 RATING: -1 (EMISSOR)
ID AG: 15 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 16 LIM1: 6 LIM2: 22 RATING: -1 (EMISSOR)
[*ATIVO DESCONSIDERADO NA REGRA*] PIOR RATING PELA AGJNCIA ID: 3 RATING DE ORDEM: 1 / POSIGCO: 1.478.583,98
 
TITULO: DEBN BRKPA0 / EMISSOR: BRKP
ID AG: 2 LIM1: 6 LIM2: 22 RATING: -1 (EMISSOR)
ID AG: 3 LIM1: 6 LIM2: 20 RATING: -1 (EMISSOR)
ID AG: 1 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 9 LIM1: 6 LIM2: 20 RATING: -1 (EMISSOR)
ID AG: 11 LIM1: 4 LIM2: 10 RATING: -1 (EMISSOR)
ID AG: 13 LIM1: 6 LIM2: 21 RATING: 5 (TITULO)
ID AG: 14 LIM1: 2 LIM2: 5 RATING: -1 (EMISSOR)
ID AG: 15 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 16 LIM1: 6 LIM2: 22 RATING: -1 (EMISSOR)
[*ATIVO DESCONSIDERADO NA REGRA*] PIOR RATING PELA AGJNCIA ID: 13 RATING DE ORDEM: 5 / POSIGCO: 1.530.859,06
 
TITULO: DEBN BRKPA0 / EMISSOR: BRKP
ID AG: 2 LIM1: 6 LIM2: 22 RATING: -1 (EMISSOR)
ID AG: 3 LIM1: 6 LIM2: 20 RATING: -1 (EMISSOR)
ID AG: 1 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 9 LIM1: 6 LIM2: 20 RATING: -1 (EMISSOR)
ID AG: 11 LIM1: 4 LIM2: 10 RATING: -1 (EMISSOR)
ID AG: 13 LIM1: 6 LIM2: 21 RATING: 5 (TITULO)
ID AG: 14 LIM1: 2 LIM2: 5 RATING: -1 (EMISSOR)
ID AG: 15 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 16 LIM1: 6 LIM2: 22 RATING: -1 (EMISSOR)
[*ATIVO DESCONSIDERADO NA REGRA*] PIOR RATING PELA AGJNCIA ID: 13 RATING DE ORDEM: 5 / POSIGCO: 3.717.089,13
 
TITULO: DEBN BBRM11 / EMISSOR: BBRM
ID AG: 2 LIM1: 6 LIM2: 22 RATING: -1 (EMISSOR)
ID AG: 3 LIM1: 6 LIM2: 20 RATING: 3 (TITULO)
ID AG: 1 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 9 LIM1: 6 LIM2: 20 RATING: -1 (EMISSOR)
ID AG: 11 LIM1: 4 LIM2: 10 RATING: -1 (EMISSOR)
ID AG: 13 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 14 LIM1: 2 LIM2: 5 RATING: -1 (EMISSOR)
ID AG: 15 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 16 LIM1: 6 LIM2: 22 RATING: -1 (EMISSOR)
[*ATIVO DESCONSIDERADO NA REGRA*] PIOR RATING PELA AGJNCIA ID: 3 RATING DE ORDEM: 3 / POSIGCO: 3.168.858,25
 
TITULO: DEBN ASCP23 / EMISSOR: ASCP
ID AG: 2 LIM1: 6 LIM2: 22 RATING: 1 (TITULO)
ID AG: 3 LIM1: 6 LIM2: 20 RATING: -1 (EMISSOR)
ID AG: 1 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 9 LIM1: 6 LIM2: 20 RATING: -1 (EMISSOR)
ID AG: 11 LIM1: 4 LIM2: 10 RATING: -1 (EMISSOR)
ID AG: 13 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 14 LIM1: 2 LIM2: 5 RATING: -1 (EMISSOR)
ID AG: 15 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 16 LIM1: 6 LIM2: 22 RATING: 1 (TITULO)
[*ATIVO DESCONSIDERADO NA REGRA*] PIOR RATING PELA AGJNCIA ID: 2 RATING DE ORDEM: 1 / POSIGCO: 725.406,77
 
TITULO: DEBN ARCV12 / EMISSOR: ARCV
ID AG: 2 LIM1: 6 LIM2: 22 RATING: -1 (EMISSOR)
ID AG: 3 LIM1: 6 LIM2: 20 RATING: 1 (TITULO)
ID AG: 1 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 9 LIM1: 6 LIM2: 20 RATING: -1 (EMISSOR)
ID AG: 11 LIM1: 4 LIM2: 10 RATING: -1 (EMISSOR)
ID AG: 13 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 14 LIM1: 2 LIM2: 5 RATING: -1 (EMISSOR)
ID AG: 15 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 16 LIM1: 6 LIM2: 22 RATING: -1 (EMISSOR)
[*ATIVO DESCONSIDERADO NA REGRA*] PIOR RATING PELA AGJNCIA ID: 3 RATING DE ORDEM: 1 / POSIGCO: 131.363,84
 
TITULO: DEBN VNYD12 / EMISSOR: VNYD
ID AG: 2 LIM1: 6 LIM2: 22 RATING: -1 (EMISSOR)
ID AG: 3 LIM1: 6 LIM2: 20 RATING: 1 (TITULO)
ID AG: 1 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 9 LIM1: 6 LIM2: 20 RATING: -1 (EMISSOR)
ID AG: 11 LIM1: 4 LIM2: 10 RATING: -1 (EMISSOR)
ID AG: 13 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 14 LIM1: 2 LIM2: 5 RATING: -1 (EMISSOR)
ID AG: 15 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 16 LIM1: 6 LIM2: 22 RATING: -1 (EMISSOR)
[*ATIVO DESCONSIDERADO NA REGRA*] PIOR RATING PELA AGJNCIA ID: 3 RATING DE ORDEM: 1 / POSIGCO: 1.145.790,03
 
TITULO: DEBN AEGPA3 / EMISSOR: AEGP
ID AG: 2 LIM1: 6 LIM2: 22 RATING: 2 (TITULO)
ID AG: 3 LIM1: 6 LIM2: 20 RATING: 3 (EMISSOR)
ID AG: 1 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 9 LIM1: 6 LIM2: 20 RATING: -1 (EMISSOR)
ID AG: 11 LIM1: 4 LIM2: 10 RATING: -1 (EMISSOR)
ID AG: 13 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 14 LIM1: 2 LIM2: 5 RATING: -1 (EMISSOR)
ID AG: 15 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 16 LIM1: 6 LIM2: 22 RATING: 2 (TITULO)
[*ATIVO DESCONSIDERADO NA REGRA*] PIOR RATING PELA AGJNCIA ID: 3 RATING DE ORDEM: 3 / POSIGCO: 1.111.518,08
 
TITULO: DEBN AEGPA3 / EMISSOR: AEGP
ID AG: 2 LIM1: 6 LIM2: 22 RATING: 2 (TITULO)
ID AG: 3 LIM1: 6 LIM2: 20 RATING: 3 (EMISSOR)
ID AG: 1 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 9 LIM1: 6 LIM2: 20 RATING: -1 (EMISSOR)
ID AG: 11 LIM1: 4 LIM2: 10 RATING: -1 (EMISSOR)
ID AG: 13 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 14 LIM1: 2 LIM2: 5 RATING: -1 (EMISSOR)
ID AG: 15 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 16 LIM1: 6 LIM2: 22 RATING: 2 (TITULO)
[*ATIVO DESCONSIDERADO NA REGRA*] PIOR RATING PELA AGJNCIA ID: 3 RATING DE ORDEM: 3 / POSIGCO: 8.095.486,25
 
TITULO: DEBN VSLE11 / EMISSOR: VSLE
ID AG: 2 LIM1: 6 LIM2: 22 RATING: -1 (EMISSOR)
ID AG: 3 LIM1: 6 LIM2: 20 RATING: 3 (TITULO)
ID AG: 1 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 9 LIM1: 6 LIM2: 20 RATING: -1 (EMISSOR)
ID AG: 11 LIM1: 4 LIM2: 10 RATING: -1 (EMISSOR)
ID AG: 13 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 14 LIM1: 2 LIM2: 5 RATING: -1 (EMISSOR)
ID AG: 15 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 16 LIM1: 6 LIM2: 22 RATING: -1 (EMISSOR)
[*ATIVO DESCONSIDERADO NA REGRA*] PIOR RATING PELA AGJNCIA ID: 3 RATING DE ORDEM: 3 / POSIGCO: 1.531.199,85
 
TITULO: DEBN VP1E11 / EMISSOR: VP1E
ID AG: 2 LIM1: 6 LIM2: 22 RATING: -1 (EMISSOR)
ID AG: 3 LIM1: 6 LIM2: 20 RATING: 1 (TITULO)
ID AG: 1 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 9 LIM1: 6 LIM2: 20 RATING: -1 (EMISSOR)
ID AG: 11 LIM1: 4 LIM2: 10 RATING: -1 (EMISSOR)
ID AG: 13 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 14 LIM1: 2 LIM2: 5 RATING: -1 (EMISSOR)
ID AG: 15 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 16 LIM1: 6 LIM2: 22 RATING: -1 (EMISSOR)
[*ATIVO DESCONSIDERADO NA REGRA*] PIOR RATING PELA AGJNCIA ID: 3 RATING DE ORDEM: 1 / POSIGCO: 109.700,21
 
TITULO: DEBN VP1E11 / EMISSOR: VP1E
ID AG: 2 LIM1: 6 LIM2: 22 RATING: -1 (EMISSOR)
ID AG: 3 LIM1: 6 LIM2: 20 RATING: 1 (TITULO)
ID AG: 1 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 9 LIM1: 6 LIM2: 20 RATING: -1 (EMISSOR)
ID AG: 11 LIM1: 4 LIM2: 10 RATING: -1 (EMISSOR)
ID AG: 13 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 14 LIM1: 2 LIM2: 5 RATING: -1 (EMISSOR)
ID AG: 15 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 16 LIM1: 6 LIM2: 22 RATING: -1 (EMISSOR)
[*ATIVO DESCONSIDERADO NA REGRA*] PIOR RATING PELA AGJNCIA ID: 3 RATING DE ORDEM: 1 / POSIGCO: 659.746,35
 
TITULO: DEBN SABP12 / EMISSOR: SABP
ID AG: 2 LIM1: 6 LIM2: 22 RATING: -1 (EMISSOR)
ID AG: 3 LIM1: 6 LIM2: 20 RATING: -1 (EMISSOR)
ID AG: 1 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 9 LIM1: 6 LIM2: 20 RATING: -1 (EMISSOR)
ID AG: 11 LIM1: 4 LIM2: 10 RATING: -1 (EMISSOR)
ID AG: 13 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 14 LIM1: 2 LIM2: 5 RATING: -1 (EMISSOR)
ID AG: 15 LIM1: 6 LIM2: 21 RATING: 1 (TITULO)
ID AG: 16 LIM1: 6 LIM2: 22 RATING: -1 (EMISSOR)
[*ATIVO DESCONSIDERADO NA REGRA*] PIOR RATING PELA AGJNCIA ID: 15 RATING DE ORDEM: 1 / POSIGCO: 4.164.070,26
 
TITULO: DEBN EREN13 / EMISSOR: EREN
ID AG: 2 LIM1: 6 LIM2: 22 RATING: -1 (EMISSOR)
ID AG: 3 LIM1: 6 LIM2: 20 RATING: 1 (TITULO)
ID AG: 1 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 9 LIM1: 6 LIM2: 20 RATING: -1 (EMISSOR)
ID AG: 11 LIM1: 4 LIM2: 10 RATING: -1 (EMISSOR)
ID AG: 13 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 14 LIM1: 2 LIM2: 5 RATING: -1 (EMISSOR)
ID AG: 15 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 16 LIM1: 6 LIM2: 22 RATING: -1 (EMISSOR)
[*ATIVO DESCONSIDERADO NA REGRA*] PIOR RATING PELA AGJNCIA ID: 3 RATING DE ORDEM: 1 / POSIGCO: 2.285.141,33
 
TITULO: DEBN OLIP11 / EMISSOR: OLIP
ID AG: 2 LIM1: 6 LIM2: 22 RATING: -1 (EMISSOR)
ID AG: 3 LIM1: 6 LIM2: 20 RATING: -1 (EMISSOR)
ID AG: 1 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 9 LIM1: 6 LIM2: 20 RATING: -1 (EMISSOR)
ID AG: 11 LIM1: 4 LIM2: 10 RATING: -1 (EMISSOR)
ID AG: 13 LIM1: 6 LIM2: 21 RATING: 1 (TITULO)
ID AG: 14 LIM1: 2 LIM2: 5 RATING: -1 (EMISSOR)
ID AG: 15 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 16 LIM1: 6 LIM2: 22 RATING: -1 (EMISSOR)
[*ATIVO DESCONSIDERADO NA REGRA*] PIOR RATING PELA AGJNCIA ID: 13 RATING DE ORDEM: 1 / POSIGCO: 2.337.117,09
 
TITULO: DEBN VSJX11 / EMISSOR: VSJX
ID AG: 2 LIM1: 6 LIM2: 22 RATING: -1 (EMISSOR)
ID AG: 3 LIM1: 6 LIM2: 20 RATING: 3 (TITULO)
ID AG: 1 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 9 LIM1: 6 LIM2: 20 RATING: -1 (EMISSOR)
ID AG: 11 LIM1: 4 LIM2: 10 RATING: -1 (EMISSOR)
ID AG: 13 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 14 LIM1: 2 LIM2: 5 RATING: -1 (EMISSOR)
ID AG: 15 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 16 LIM1: 6 LIM2: 22 RATING: -1 (EMISSOR)
[*ATIVO DESCONSIDERADO NA REGRA*] PIOR RATING PELA AGJNCIA ID: 3 RATING DE ORDEM: 3 / POSIGCO: 1.667.472,30
 
TITULO: DEBN HVSP11 / EMISSOR: HVSP
ID AG: 2 LIM1: 6 LIM2: 22 RATING: -1 (EMISSOR)
ID AG: 3 LIM1: 6 LIM2: 20 RATING: -1 (EMISSOR)
ID AG: 1 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 9 LIM1: 6 LIM2: 20 RATING: -1 (EMISSOR)
ID AG: 11 LIM1: 4 LIM2: 10 RATING: -1 (EMISSOR)
ID AG: 13 LIM1: 6 LIM2: 21 RATING: 4 (TITULO)
ID AG: 14 LIM1: 2 LIM2: 5 RATING: -1 (EMISSOR)
ID AG: 15 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 16 LIM1: 6 LIM2: 22 RATING: -1 (EMISSOR)
[*ATIVO DESCONSIDERADO NA REGRA*] PIOR RATING PELA AGJNCIA ID: 13 RATING DE ORDEM: 4 / POSIGCO: 3.641.440,94
 
TITULO: DEBN EREN23 / EMISSOR: EREN
ID AG: 2 LIM1: 6 LIM2: 22 RATING: -1 (EMISSOR)
ID AG: 3 LIM1: 6 LIM2: 20 RATING: 1 (TITULO)
ID AG: 1 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 9 LIM1: 6 LIM2: 20 RATING: -1 (EMISSOR)
ID AG: 11 LIM1: 4 LIM2: 10 RATING: -1 (EMISSOR)
ID AG: 13 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 14 LIM1: 2 LIM2: 5 RATING: -1 (EMISSOR)
ID AG: 15 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 16 LIM1: 6 LIM2: 22 RATING: -1 (EMISSOR)
[*ATIVO DESCONSIDERADO NA REGRA*] PIOR RATING PELA AGJNCIA ID: 3 RATING DE ORDEM: 1 / POSIGCO: 689.688,14
 
TITULO: DEBN EREN23 / EMISSOR: EREN
ID AG: 2 LIM1: 6 LIM2: 22 RATING: -1 (EMISSOR)
ID AG: 3 LIM1: 6 LIM2: 20 RATING: 1 (TITULO)
ID AG: 1 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 9 LIM1: 6 LIM2: 20 RATING: -1 (EMISSOR)
ID AG: 11 LIM1: 4 LIM2: 10 RATING: -1 (EMISSOR)
ID AG: 13 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 14 LIM1: 2 LIM2: 5 RATING: -1 (EMISSOR)
ID AG: 15 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 16 LIM1: 6 LIM2: 22 RATING: -1 (EMISSOR)
[*ATIVO DESCONSIDERADO NA REGRA*] PIOR RATING PELA AGJNCIA ID: 3 RATING DE ORDEM: 1 / POSIGCO: 148.189,75
 
TITULO: DEBN PAMP12 / EMISSOR: PAMP
ID AG: 2 LIM1: 6 LIM2: 22 RATING: -1 (EMISSOR)
ID AG: 3 LIM1: 6 LIM2: 20 RATING: -1 (EMISSOR)
ID AG: 1 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 9 LIM1: 6 LIM2: 20 RATING: -1 (EMISSOR)
ID AG: 11 LIM1: 4 LIM2: 10 RATING: -1 (EMISSOR)
ID AG: 13 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 14 LIM1: 2 LIM2: 5 RATING: -1 (EMISSOR)
ID AG: 15 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 16 LIM1: 6 LIM2: 22 RATING: 2 (TITULO)
[*ATIVO DESCONSIDERADO NA REGRA*] PIOR RATING PELA AGJNCIA ID: 16 RATING DE ORDEM: 2 / POSIGCO: 1.487.513,36
 
TITULO: DEBN EREN13 / EMISSOR: EREN
ID AG: 2 LIM1: 6 LIM2: 22 RATING: -1 (EMISSOR)
ID AG: 3 LIM1: 6 LIM2: 20 RATING: 1 (TITULO)
ID AG: 1 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 9 LIM1: 6 LIM2: 20 RATING: -1 (EMISSOR)
ID AG: 11 LIM1: 4 LIM2: 10 RATING: -1 (EMISSOR)
ID AG: 13 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 14 LIM1: 2 LIM2: 5 RATING: -1 (EMISSOR)
ID AG: 15 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 16 LIM1: 6 LIM2: 22 RATING: -1 (EMISSOR)
[*ATIVO DESCONSIDERADO NA REGRA*] PIOR RATING PELA AGJNCIA ID: 3 RATING DE ORDEM: 1 / POSIGCO: 486.890,91
 
TITULO: DEBN ECPN11 / EMISSOR: ECPN
ID AG: 2 LIM1: 6 LIM2: 22 RATING: -1 (EMISSOR)
ID AG: 3 LIM1: 6 LIM2: 20 RATING: 3 (TITULO)
ID AG: 1 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 9 LIM1: 6 LIM2: 20 RATING: -1 (EMISSOR)
ID AG: 11 LIM1: 4 LIM2: 10 RATING: -1 (EMISSOR)
ID AG: 13 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 14 LIM1: 2 LIM2: 5 RATING: -1 (EMISSOR)
ID AG: 15 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 16 LIM1: 6 LIM2: 22 RATING: -1 (EMISSOR)
[*ATIVO DESCONSIDERADO NA REGRA*] PIOR RATING PELA AGJNCIA ID: 3 RATING DE ORDEM: 3 / POSIGCO: 395.146,85
 
TITULO: DEBN CGEP12 / EMISSOR: CGEP
ID AG: 2 LIM1: 6 LIM2: 22 RATING: -1 (EMISSOR)
ID AG: 3 LIM1: 6 LIM2: 20 RATING: 1 (TITULO)
ID AG: 1 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 9 LIM1: 6 LIM2: 20 RATING: -1 (EMISSOR)
ID AG: 11 LIM1: 4 LIM2: 10 RATING: -1 (EMISSOR)
ID AG: 13 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 14 LIM1: 2 LIM2: 5 RATING: -1 (EMISSOR)
ID AG: 15 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 16 LIM1: 6 LIM2: 22 RATING: -1 (EMISSOR)
[*ATIVO DESCONSIDERADO NA REGRA*] PIOR RATING PELA AGJNCIA ID: 3 RATING DE ORDEM: 1 / POSIGCO: 964.047,15
 
TITULO: DEBN CGEP12 / EMISSOR: CGEP
ID AG: 2 LIM1: 6 LIM2: 22 RATING: -1 (EMISSOR)
ID AG: 3 LIM1: 6 LIM2: 20 RATING: 1 (TITULO)
ID AG: 1 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 9 LIM1: 6 LIM2: 20 RATING: -1 (EMISSOR)
ID AG: 11 LIM1: 4 LIM2: 10 RATING: -1 (EMISSOR)
ID AG: 13 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 14 LIM1: 2 LIM2: 5 RATING: -1 (EMISSOR)
ID AG: 15 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 16 LIM1: 6 LIM2: 22 RATING: -1 (EMISSOR)
[*ATIVO DESCONSIDERADO NA REGRA*] PIOR RATING PELA AGJNCIA ID: 3 RATING DE ORDEM: 1 / POSIGCO: 3.545.794,65
 
TITULO: DEBN BRKPA0 / EMISSOR: BRKP
ID AG: 2 LIM1: 6 LIM2: 22 RATING: -1 (EMISSOR)
ID AG: 3 LIM1: 6 LIM2: 20 RATING: -1 (EMISSOR)
ID AG: 1 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 9 LIM1: 6 LIM2: 20 RATING: -1 (EMISSOR)
ID AG: 11 LIM1: 4 LIM2: 10 RATING: -1 (EMISSOR)
ID AG: 13 LIM1: 6 LIM2: 21 RATING: 5 (TITULO)
ID AG: 14 LIM1: 2 LIM2: 5 RATING: -1 (EMISSOR)
ID AG: 15 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 16 LIM1: 6 LIM2: 22 RATING: -1 (EMISSOR)
[*ATIVO DESCONSIDERADO NA REGRA*] PIOR RATING PELA AGJNCIA ID: 13 RATING DE ORDEM: 5 / POSIGCO: 2.988.013,77
 
TITULO: DEBN TAEE18 / EMISSOR: TAEE
ID AG: 2 LIM1: 6 LIM2: 22 RATING: -1 (EMISSOR)
ID AG: 3 LIM1: 6 LIM2: 20 RATING: 1 (EMISSOR)
ID AG: 1 LIM1: 6 LIM2: 21 RATING: 1 (TITULO)
ID AG: 9 LIM1: 6 LIM2: 20 RATING: -1 (EMISSOR)
ID AG: 11 LIM1: 4 LIM2: 10 RATING: -1 (EMISSOR)
ID AG: 13 LIM1: 6 LIM2: 21 RATING: 1 (TITULO)
ID AG: 14 LIM1: 2 LIM2: 5 RATING: -1 (EMISSOR)
ID AG: 15 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 16 LIM1: 6 LIM2: 22 RATING: -1 (EMISSOR)
[*ATIVO DESCONSIDERADO NA REGRA*] PIOR RATING PELA AGJNCIA ID: 3 RATING DE ORDEM: 1 / POSIGCO: 4.649.668,47
 
TITULO: DEBN RTCQ12 / EMISSOR: RTCQ
ID AG: 2 LIM1: 6 LIM2: 22 RATING: -1 (EMISSOR)
ID AG: 3 LIM1: 6 LIM2: 20 RATING: 4 (TITULO)
ID AG: 1 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 9 LIM1: 6 LIM2: 20 RATING: -1 (EMISSOR)
ID AG: 11 LIM1: 4 LIM2: 10 RATING: -1 (EMISSOR)
ID AG: 13 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 14 LIM1: 2 LIM2: 5 RATING: -1 (EMISSOR)
ID AG: 15 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 16 LIM1: 6 LIM2: 22 RATING: -1 (EMISSOR)
[*ATIVO DESCONSIDERADO NA REGRA*] PIOR RATING PELA AGJNCIA ID: 3 RATING DE ORDEM: 4 / POSIGCO: 1.254.465,36
 
TITULO: DEBN TAEE18 / EMISSOR: TAEE
ID AG: 2 LIM1: 6 LIM2: 22 RATING: -1 (EMISSOR)
ID AG: 3 LIM1: 6 LIM2: 20 RATING: 1 (EMISSOR)
ID AG: 1 LIM1: 6 LIM2: 21 RATING: 1 (TITULO)
ID AG: 9 LIM1: 6 LIM2: 20 RATING: -1 (EMISSOR)
ID AG: 11 LIM1: 4 LIM2: 10 RATING: -1 (EMISSOR)
ID AG: 13 LIM1: 6 LIM2: 21 RATING: 1 (TITULO)
ID AG: 14 LIM1: 2 LIM2: 5 RATING: -1 (EMISSOR)
ID AG: 15 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 16 LIM1: 6 LIM2: 22 RATING: -1 (EMISSOR)
[*ATIVO DESCONSIDERADO NA REGRA*] PIOR RATING PELA AGJNCIA ID: 3 RATING DE ORDEM: 1 / POSIGCO: 934.090,64
 
TITULO: DEBN TAEE26 / EMISSOR: TAEE
ID AG: 2 LIM1: 6 LIM2: 22 RATING: -1 (EMISSOR)
ID AG: 3 LIM1: 6 LIM2: 20 RATING: 1 (EMISSOR)
ID AG: 1 LIM1: 6 LIM2: 21 RATING: 1 (TITULO)
ID AG: 9 LIM1: 6 LIM2: 20 RATING: -1 (EMISSOR)
ID AG: 11 LIM1: 4 LIM2: 10 RATING: -1 (EMISSOR)
ID AG: 13 LIM1: 6 LIM2: 21 RATING: 1 (TITULO)
ID AG: 14 LIM1: 2 LIM2: 5 RATING: -1 (EMISSOR)
ID AG: 15 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 16 LIM1: 6 LIM2: 22 RATING: -1 (EMISSOR)
[*ATIVO DESCONSIDERADO NA REGRA*] PIOR RATING PELA AGJNCIA ID: 3 RATING DE ORDEM: 1 / POSIGCO: 4.125.032,79
 
TITULO: DEBN SOTE11 / EMISSOR: SOTE
ID AG: 2 LIM1: 6 LIM2: 22 RATING: -1 (EMISSOR)
ID AG: 3 LIM1: 6 LIM2: 20 RATING: 1 (TITULO)
ID AG: 1 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 9 LIM1: 6 LIM2: 20 RATING: -1 (EMISSOR)
ID AG: 11 LIM1: 4 LIM2: 10 RATING: -1 (EMISSOR)
ID AG: 13 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 14 LIM1: 2 LIM2: 5 RATING: -1 (EMISSOR)
ID AG: 15 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 16 LIM1: 6 LIM2: 22 RATING: -1 (EMISSOR)
[*ATIVO DESCONSIDERADO NA REGRA*] PIOR RATING PELA AGJNCIA ID: 3 RATING DE ORDEM: 1 / POSIGCO: 1.336.785,29
 
TITULO: DEBN UNEG11 / EMISSOR: UNEG
ID AG: 2 LIM1: 6 LIM2: 22 RATING: 6 (TITULO)
ID AG: 3 LIM1: 6 LIM2: 20 RATING: -1 (EMISSOR)
ID AG: 1 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 9 LIM1: 6 LIM2: 20 RATING: -1 (EMISSOR)
ID AG: 11 LIM1: 4 LIM2: 10 RATING: -1 (EMISSOR)
ID AG: 13 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 14 LIM1: 2 LIM2: 5 RATING: -1 (EMISSOR)
ID AG: 15 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 16 LIM1: 6 LIM2: 22 RATING: -1 (EMISSOR)
[ATIVO CONSIDERADO NA REGRA] PIOR RATING PELA AGJNCIA ID: 2 RATING DE ORDEM: 6 / POSICAO: 1.187.874,75
 
TITULO: DEBN IRJS14 / EMISSOR: IRJS
ID AG: 2 LIM1: 6 LIM2: 22 RATING: 2 (TITULO)
ID AG: 3 LIM1: 6 LIM2: 20 RATING: -1 (EMISSOR)
ID AG: 1 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 9 LIM1: 6 LIM2: 20 RATING: -1 (EMISSOR)
ID AG: 11 LIM1: 4 LIM2: 10 RATING: -1 (EMISSOR)
ID AG: 13 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 14 LIM1: 2 LIM2: 5 RATING: -1 (EMISSOR)
ID AG: 15 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 16 LIM1: 6 LIM2: 22 RATING: 2 (TITULO)
[*ATIVO DESCONSIDERADO NA REGRA*] PIOR RATING PELA AGJNCIA ID: 2 RATING DE ORDEM: 2 / POSIGCO: 1.322.198,84
 
TITULO: DEBN RIS412 / EMISSOR: RISP
ID AG: 2 LIM1: 6 LIM2: 22 RATING: 2 (EMISSOR)
ID AG: 3 LIM1: 6 LIM2: 20 RATING: -1 (EMISSOR)
ID AG: 1 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 9 LIM1: 6 LIM2: 20 RATING: -1 (EMISSOR)
ID AG: 11 LIM1: 4 LIM2: 10 RATING: -1 (EMISSOR)
ID AG: 13 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 14 LIM1: 2 LIM2: 5 RATING: -1 (EMISSOR)
ID AG: 15 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 16 LIM1: 6 LIM2: 22 RATING: 2 (TITULO)
[*ATIVO DESCONSIDERADO NA REGRA*] PIOR RATING PELA AGJNCIA ID: 2 RATING DE ORDEM: 2 / POSIGCO: 315.330,81
 
TITULO: DEBN RMSA12 / EMISSOR: RMSA
ID AG: 2 LIM1: 6 LIM2: 22 RATING: -1 (EMISSOR)
ID AG: 3 LIM1: 6 LIM2: 20 RATING: -1 (EMISSOR)
ID AG: 1 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 9 LIM1: 6 LIM2: 20 RATING: -1 (EMISSOR)
ID AG: 11 LIM1: 4 LIM2: 10 RATING: -1 (EMISSOR)
ID AG: 13 LIM1: 6 LIM2: 21 RATING: 4 (TITULO)
ID AG: 14 LIM1: 2 LIM2: 5 RATING: -1 (EMISSOR)
ID AG: 15 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 16 LIM1: 6 LIM2: 22 RATING: -1 (EMISSOR)
[*ATIVO DESCONSIDERADO NA REGRA*] PIOR RATING PELA AGJNCIA ID: 13 RATING DE ORDEM: 4 / POSIGCO: 3.922.444,26
 
TITULO: DEBN RMSA12 / EMISSOR: RMSA
ID AG: 2 LIM1: 6 LIM2: 22 RATING: -1 (EMISSOR)
ID AG: 3 LIM1: 6 LIM2: 20 RATING: -1 (EMISSOR)
ID AG: 1 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 9 LIM1: 6 LIM2: 20 RATING: -1 (EMISSOR)
ID AG: 11 LIM1: 4 LIM2: 10 RATING: -1 (EMISSOR)
ID AG: 13 LIM1: 6 LIM2: 21 RATING: 4 (TITULO)
ID AG: 14 LIM1: 2 LIM2: 5 RATING: -1 (EMISSOR)
ID AG: 15 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 16 LIM1: 6 LIM2: 22 RATING: -1 (EMISSOR)
[*ATIVO DESCONSIDERADO NA REGRA*] PIOR RATING PELA AGJNCIA ID: 13 RATING DE ORDEM: 4 / POSIGCO: 2.427.563,70
 
TITULO: DEBN RISP22 / EMISSOR: RISP
ID AG: 2 LIM1: 6 LIM2: 22 RATING: 2 (EMISSOR)
ID AG: 3 LIM1: 6 LIM2: 20 RATING: -1 (EMISSOR)
ID AG: 1 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 9 LIM1: 6 LIM2: 20 RATING: -1 (EMISSOR)
ID AG: 11 LIM1: 4 LIM2: 10 RATING: -1 (EMISSOR)
ID AG: 13 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 14 LIM1: 2 LIM2: 5 RATING: -1 (EMISSOR)
ID AG: 15 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 16 LIM1: 6 LIM2: 22 RATING: 2 (TITULO)
[*ATIVO DESCONSIDERADO NA REGRA*] PIOR RATING PELA AGJNCIA ID: 2 RATING DE ORDEM: 2 / POSIGCO: 3.564.119,62
 
TITULO: DEBN RISP12 / EMISSOR: RISP
ID AG: 2 LIM1: 6 LIM2: 22 RATING: 2 (EMISSOR)
ID AG: 3 LIM1: 6 LIM2: 20 RATING: -1 (EMISSOR)
ID AG: 1 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 9 LIM1: 6 LIM2: 20 RATING: -1 (EMISSOR)
ID AG: 11 LIM1: 4 LIM2: 10 RATING: -1 (EMISSOR)
ID AG: 13 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 14 LIM1: 2 LIM2: 5 RATING: -1 (EMISSOR)
ID AG: 15 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 16 LIM1: 6 LIM2: 22 RATING: 2 (TITULO)
[*ATIVO DESCONSIDERADO NA REGRA*] PIOR RATING PELA AGJNCIA ID: 2 RATING DE ORDEM: 2 / POSIGCO: 537.901,72
 
TITULO: DEBN RIS422 / EMISSOR: RISP
ID AG: 2 LIM1: 6 LIM2: 22 RATING: 2 (EMISSOR)
ID AG: 3 LIM1: 6 LIM2: 20 RATING: -1 (EMISSOR)
ID AG: 1 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 9 LIM1: 6 LIM2: 20 RATING: -1 (EMISSOR)
ID AG: 11 LIM1: 4 LIM2: 10 RATING: -1 (EMISSOR)
ID AG: 13 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 14 LIM1: 2 LIM2: 5 RATING: -1 (EMISSOR)
ID AG: 15 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 16 LIM1: 6 LIM2: 22 RATING: 2 (TITULO)
[*ATIVO DESCONSIDERADO NA REGRA*] PIOR RATING PELA AGJNCIA ID: 2 RATING DE ORDEM: 2 / POSIGCO: 2.091.283,76
 
TITULO: DEBN UNEG11 / EMISSOR: UNEG
ID AG: 2 LIM1: 6 LIM2: 22 RATING: 6 (TITULO)
ID AG: 3 LIM1: 6 LIM2: 20 RATING: -1 (EMISSOR)
ID AG: 1 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 9 LIM1: 6 LIM2: 20 RATING: -1 (EMISSOR)
ID AG: 11 LIM1: 4 LIM2: 10 RATING: -1 (EMISSOR)
ID AG: 13 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 14 LIM1: 2 LIM2: 5 RATING: -1 (EMISSOR)
ID AG: 15 LIM1: 6 LIM2: 21 RATING: -1 (EMISSOR)
ID AG: 16 LIM1: 6 LIM2: 22 RATING: -1 (EMISSOR)
[ATIVO CONSIDERADO NA REGRA] PIOR RATING PELA AGJNCIA ID: 2 RATING DE ORDEM: 6 / POSICAO: 1.187.874,75

MEMÓRIA DE CÁLCULO (PROCESSAMENTO)
----------------------------------

TÍTULO               NOME                           POSIÇÃO              %PL        GRUPO                                                        EMISSOR
-------------------- ------------------------------ -------------------- ---------- ------------------------------------------------------------ ------------------------------------------------------------
DEBN UNEG11          DEBN UNEG11                            1.187.874,75       0,98 10440 - Títulos Privados-Debêntures Incent. (Lei 12.431)     UNEG - UTE GNA I GERACAO DE ENERGIA S.A.                    

        
        """
    )

    display(df)

