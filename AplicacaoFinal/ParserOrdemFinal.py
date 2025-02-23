import pandas as pd
from datetime import datetime
from pathlib import Path


def __get_ordem_original()->pd.DataFrame | None:
   path = Path("/Volumes/desafio_kinea/boletagem_cp/files/Ordem/")
   for file in path.glob("*.csv"):
      if "ordem_" in str(file): #arquivos de ordem são no formato: ordem_{data}
         return pd.read_csv(file)
   
   return None

def __get_input_nexxus_final()->pd.DataFrame | None:
   path = Path("/Volumes/desafio_kinea/boletagem_cp/files/InputNexxus/")
   for file in path.glob("*.csv"):
      if "input_nexxus_2.csv" in str(file): #arquivos de ordem são no formato: ordem_{data}
         return pd.read_csv(file,sep=";")
   
   return None

def __get_relacao_books()->pd.DataFrame:
   path = Path("/Volumes/desafio_kinea/boletagem_cp/files/DadosIniciais/verificacao_range_e_book.csv")
   df = pd.read_csv(path,usecols=["ativo","book_micro"]) #remove duplicadas pq o CSV tem ativos repetidos (por que ele mapea um ativo em um fundo)
   df = df.drop_duplicates()

   return df

def __join_pelo_book(df_final:pd.DataFrame, relacao_books:pd.DataFrame)->pd.DataFrame:
   """
   Join do df final (só faltando a coluna de book) com o df de relação ativo -> book (micro e macro) para achar o book de cada ativo.
   """
   relacao_books["ativo"] = relacao_books["ativo"].apply(lambda x: x.replace(" ","").lower()) #tira o espaço e deixar lowercase para facilitar a comparação
   df_final["TickerParsed"] = df_final["Ticker"].apply(lambda x: x.replace(" ","").lower()) 

   #display(df_final)
   #print(relacao_books.head())

   df_join = df_final.merge(relacao_books,left_on="TickerParsed",right_on="ativo",how="left") #join pelas colunas de ativos parsed

   df_join  = df_join.drop( #drop nas colunas que não precisa
        ["ativo","TickerParsed"],axis=1
   )
   df_join = df_join.rename(columns={"book_micro": "Book"}) #renomeia a coluna para Book

   return df_join

def __adiciona_colunas(enquadrado_nexxus_df:pd.DataFrame)->pd.DataFrame:
      data = datetime.today().date()
      enquadrado_nexxus_df["Data"] = data
      enquadrado_nexxus_df["Data Liq."] = data
      enquadrado_nexxus_df["Data Pay."] = data
      enquadrado_nexxus_df["Conta Mae Allocation"] = "Conta Mae Allocation"
      enquadrado_nexxus_df["TRADER"] = "Guilherme Ali Abdallah Bassani"
      enquadrado_nexxus_df["S. Broker"] = enquadrado_nexxus_df["Broker"]
      enquadrado_nexxus_df["Notes"] = ""

      return enquadrado_nexxus_df

def ParseOrdemFinal()->None:
   ordem_df = __get_ordem_original()
   enquadrado_nexxus_df = __get_input_nexxus_final()
   relacao_books = __get_relacao_books()

   enquadrado_nexxus_df = enquadrado_nexxus_df.merge( #Join pelo ativo e o preço ser igual
      ordem_df,left_on=["ATIVO","PU"],right_on=["Ticker","Price"], how="inner"
   )

   enquadrado_nexxus_df =  enquadrado_nexxus_df.drop(["ATIVO","QTDE","PU"],axis=1)
   enquadrado_nexxus_df = __adiciona_colunas(enquadrado_nexxus_df)
   enquadrado_nexxus_df = enquadrado_nexxus_df.rename(
      {
         "FUNDO": "Allocation",
      }, axis = 1
   )
   
   enquadrado_nexxus_df = __join_pelo_book(enquadrado_nexxus_df,relacao_books)

   path_final = Path("/Volumes/desafio_kinea/boletagem_cp/files/ResultadoFinal/resultado_final.csv") #salva no diretório do resultado final
   enquadrado_nexxus_df.to_csv(path_final,index=False)

if __name__ == "__main__":
  ParseOrdemFinal()
