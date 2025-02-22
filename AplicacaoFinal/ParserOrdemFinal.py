import pandas as pd
from datetime import datetime
from pathlib import Path


def get_ordem_original()->pd.DataFrame | None:
   path = Path("/Volumes/desafio_kinea/boletagem_cp/files/Ordem/")
   for file in path.glob("*.csv"):
      if "ordem_" in str(file): #arquivos de ordem são no formato: ordem_{data}
         return pd.read_csv(file)
   
   return None

def get_input_nexxus_final()->pd.DataFrame | None:
   path = Path("/Volumes/desafio_kinea/boletagem_cp/files/InputNexxus/")
   for file in path.glob("*.csv"):
      if "input_nexxus_2.csv" in str(file): #arquivos de ordem são no formato: ordem_{data}
         return pd.read_csv(file,sep=";")
   
   return None

def get_relacao_books()->pd.DataFrame:
   path = Path("/Volumes/desafio_kinea/boletagem_cp/files/DadosIniciais/verificacao_range_e_book.csv")
   df = pd.read_csv(path,usecols=["ativo","book_macro","book_micro"])
   return df



if __name__ == "__main__":
   ordem_df = get_ordem_original()
   enquadrado_nexxus_df = get_input_nexxus_final()
   relacao_books = get_relacao_books()

   display(relacao_books)

   enquadrado_nexxus_df = enquadrado_nexxus_df.merge( #Join pelo ativo e o preço ser igual
      ordem_df,left_on=["ATIVO","PU"],right_on=["Ticker","Price"], how="inner"
   )


   enquadrado_nexxus_df =  enquadrado_nexxus_df.drop(["ATIVO","QTDE","PU"],axis=1)


   data = datetime.today().date()

   enquadrado_nexxus_df["Data"] = data
   enquadrado_nexxus_df["Data Liq."] = data
   enquadrado_nexxus_df["Data Pay."] = data
   enquadrado_nexxus_df["Conta Mae Allocation"] = "Conta Mae Allocation"
   enquadrado_nexxus_df["TRADER"] = "Guilherme Ali Abdallah Bassani"
   enquadrado_nexxus_df["S. Broker"] = enquadrado_nexxus_df["Broker"]
   enquadrado_nexxus_df["Notes"] = ""


   enquadrado_nexxus_df = enquadrado_nexxus_df.rename(
      {
         "FUNDO": "Allocation",
      }, axis = 1)

   #display(enquadrado_nexxus_df)
