import streamlit as st
import ast
import pandas as pd
from dataclasses import dataclass, field
from datetime import datetime
import requests,os,io

HOST_NAME = os.getenv("HOST_NAME")
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


@dataclass
class LogNexxus:
   data: datetime
   regra:str
   fundo:str
   memoria_calculo:str
   descricao_regra:str
   saldo_base_calculo:float
   valor_exposicao:float
   saldo_objeto:float
   ativos_desenquadrados: list[str] = field(default_factory=list)
   



def get_logs_nexxus(depois_do_tempo:datetime | None = None)->list[LogNexxus]:
    """
    Função que retorna lista de logs. 
    Neste exemplo, estamos lendo do session_state para fins de demonstração.
    Se você quiser puxar do mesmo local que 'get_backend_status', basta replicar 
    a lógica ou importar a classe e gerar o dicionário lá.
    """
    logs = []
    df_logs: pd.DataFrame | None = ler_arquivo_log("/Volumes/desafio_kinea/boletagem_cp/files/Logs/logs_nexxus_teste.csv")
    if df_logs is None:
        return []
    
    df_logs["data"] = df_logs["data"].astype("datetime64[ns]")
    if depois_do_tempo is not None:
        df_logs = df_logs[df_logs['data'] > depois_do_tempo].copy()
    
    for row in df_logs.itertuples():
        ativos = []
        if row.ativos_desenquadrados and row.ativos_desenquadrados.strip():
            ativos = ast.literal_eval(row.ativos_desenquadrados) #string para uma lista do python
        
        logs.append(
            LogNexxus(
                data=row.data,
                regra=row.regra,
                fundo=row.fundo,
                memoria_calculo=row.memoria_calculo,
                descricao_regra=row.descricao_regra,
                saldo_base_calculo=row.saldo_base_calculo,
                valor_exposicao=row.valor_exposicao,
                saldo_objeto=row.saldo_objeto,
                ativos_desenquadrados=ativos
            )
        )

    return logs

def main():
    st.set_page_config(layout="wide")
    st.title("Logs do Nexxus")

    logs = get_logs_nexxus()

    # Convert the list of dataclass objects into a list of dictionaries
    # We'll also format `data` as a string if you prefer readability.
    logs_dicts = []
    for log in logs:
        logs_dicts.append(
            {
                "data": log.data.strftime("%Y-%m-%d %H:%M:%S"),
                "regra": log.regra,
                "fundo": log.fundo,
                "memoria_calculo": log.memoria_calculo,
                "descricao_regra": log.descricao_regra,
                "saldo_base_calculo": log.saldo_base_calculo,
                "valor_exposicao": log.valor_exposicao,
                "saldo_objeto": log.saldo_objeto,
                "ativos_desenquadrados": log.ativos_desenquadrados,
            }
        )

    # Create a DataFrame from these dictionaries
    df = pd.DataFrame(logs_dicts)
    df["data"] = df["data"].astype('datetime64[ns]')

    min_date = df["data"].min().date()  # earliest date
    max_date = df["data"].max().date()  # latest date

    start_date = st.sidebar.date_input("Data inicial", value=min_date)
    end_date   = st.sidebar.date_input("Data final",   value=max_date)
    
    if start_date is None: #caso em que o user n escreve nenhuma data
        start_date = min_date
    if end_date is None:
        end_date = max_date

    # If user picks the same date for both, treat it as "that single day."
    if start_date == end_date:
        st.write(f"Exibindo registros **somente** do dia: {start_date}")
        start_dt = datetime.combine(start_date, datetime.min.time())
        end_dt   = datetime.combine(end_date,   datetime.max.time())
    else:
        # Normal range filter
        st.write(f"Exibindo registros de **{start_date}** até **{end_date}**")
        start_dt = datetime.combine(start_date, datetime.min.time())
        end_dt   = datetime.combine(end_date,   datetime.max.time())

    #filtra df pelas datas
    mask = (df["data"] >= start_dt) & (df["data"] <= end_dt)
    df_filtered = df[mask].copy()

    st.subheader("Logs Filtrados")
    st.dataframe(df_filtered, use_container_width=True, height=400)

if __name__ == "__main__":
    main()
