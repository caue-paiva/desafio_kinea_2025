import pandas as pd
from datetime import datetime

def get_ordem_original()->pd.DataFrame:
   return pd.read_csv("ordem_2025-02-21 17_37_33.csv")

def get_input_nexxus_final()->pd.DataFrame:
   return pd.read_csv("input_nexxus_teste_joao (2).csv",sep=";")

def get_relacao_books()->pd.DataFrame:
   pass


ordem_df = get_ordem_original()
enquadrado_nexxus_df = get_input_nexxus_final()


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

print(enquadrado_nexxus_df.head())
