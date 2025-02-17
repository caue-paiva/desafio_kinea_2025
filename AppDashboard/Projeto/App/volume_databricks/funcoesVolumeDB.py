import databricks,requests,os,io
import pandas as pd
from datetime import datetime

HOST_NAME = os.getenv("HOST_NAME")
#CLUSTER_ID = os.getenv("CLUSTER_ID")
ACESS_TOKEN = os.getenv("ACESS_TOKEN")


def ler_arquivo_log(path:str)-> pd.DataFrame | None:
   url = f"https://{HOST_NAME}/api/2.0/fs/files{path}"

   headers = {
      "Authorization": f"Bearer {ACESS_TOKEN}",
      "Content-Type": "application/octet-stream"
   }

   response = requests.get(url=url,headers=headers)

   if response.status_code == 200:
      df = pd.read_csv(io.BytesIO(response.content))
      return df
   else:
      print(f"Falha ao baixar arquivo do path {path}")
      return None

def update_log_file(novo_log:pd.DataFrame,path_log_antigo:str)->bool:
   log_existente:pd.DataFrame | None = ler_arquivo_log(path_log_antigo) #le CSV que ja esta no volume

   if log_existente is not None:
      log_final:pd.DataFrame = pd.concat([log_existente,novo_log],axis=0) #concat com novo
   else:
      log_final:pd.DataFrame = novo_log

   return upload_arquivo(log_final,path_log_antigo) #faz upload no lugar do antigo

def upload_arquivo(df:pd.DataFrame,path:str,overwrite:bool = True)->bool:

   csv_buffer = io.BytesIO()
   df.to_csv(csv_buffer, index=False)  # Save CSV as bytes
   csv_buffer.seek(0)  # Reset buffer position

   url = f"https://{HOST_NAME}/api/2.0/fs/files{path}"
   headers = {
      "Authorization": f"Bearer {ACESS_TOKEN}",
      "Content-Type": "application/octet-stream"
   }

   params = {
        "overwrite": str(overwrite).lower()  # Convert Boolean to lowercase string (true/false)
   }


   response = requests.put(url=url,headers=headers,params=params,data=csv_buffer)
   if response.status_code == 204:
      return True
   else:
      return False

def upload_ordem(ordem:pd.DataFrame)->bool:
   str_tempo = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
   path = f"/Volumes/desafio_kinea/boletagem_cp/files/Ordem/ordem_{str_tempo}.csv"
   return upload_arquivo(ordem,path,True)

