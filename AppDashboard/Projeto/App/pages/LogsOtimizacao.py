from dataclasses import dataclass, field
from datetime import datetime
import streamlit as st
import pandas as pd
import requests,os,io
import pandas as pd
import ast
from datetime import datetime

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
class LogOtimizacao:
   ativo:str
   data:datetime
   iteracao_otimizador:int
   passou_max_pl:bool #régua passou na verificação da tabelacar de MaxPL pelo rating do ativo
   passou_max_emissor:bool #régua passou na verificação da tabelacar de PL pelo rating do emissor
   passou_anos:bool #régua passou na verificação da tabelacar de PL pela duração do ativo
   fundos_alocados:list[str] = field(default_factory=list)

def get_logs_otimizacao() -> list[LogOtimizacao]:
    """
    Reads a CSV file ('logs_otimizacao.csv') and returns a list of LogOtimizacao objects.
    By default, we read it from the 'pages' folder (same place as the code).
    Adjust the CSV path as needed for your setup.
    """
    logs = []
   
    df_logs:pd.DataFrame | None = ler_arquivo_log("/Volumes/desafio_kinea/boletagem_cp/files/Logs/logs_otimizacao_teste.csv")
    if df_logs is None:
        return logs

    df_logs["data"] = df_logs["data"].astype("datetime64[ns]") #transforma em datetime

    # 4) fundos_alocados -> lista de strings (usando ast.literal_eval)
    def parse_fundos_alocados(value: str) -> list[str]:
        if not isinstance(value, str) or not value.strip():
            return []
        return ast.literal_eval(value)

    df_logs["fundos_alocados"] = df_logs["fundos_alocados"].apply(parse_fundos_alocados) #string  -> lista python
    
    # -- Monta a lista de objetos LogOtimizacao -- #
    for row in df_logs.itertuples(index=False):
        log_obj = LogOtimizacao(
            ativo=row.ativo,
            data=row.data,
            iteracao_otimizador=row.iteracao_otimizador,
            passou_max_pl=row.passou_max_pl,
            passou_max_emissor=row.passou_max_emissor,
            passou_anos=row.passou_anos,
            fundos_alocados=row.fundos_alocados
        )
        logs.append(log_obj)
    
    return logs

def main():
    st.set_page_config(layout="wide")
    st.title("Logs de Otimização")

    # 1) Read the logs from CSV
    logs = get_logs_otimizacao()

    # 2) Convert the list of dataclass objects into a DataFrame
    logs_dicts = []
    for log in logs:
        logs_dicts.append({
            "ativo": log.ativo,
            "data": log.data,  # Keep as datetime
            "iteracao_otimizador": log.iteracao_otimizador,
            "fundos_alocados": log.fundos_alocados,
            "passou_max_pl": log.passou_max_pl,
            "passou_max_emissor": log.passou_max_emissor,
            "passou_anos": log.passou_anos
        })

    df = pd.DataFrame(logs_dicts)

    # 3) Date Filter (Start / End)
    if not df.empty:
        min_date = df["data"].min().date()
        max_date = df["data"].max().date()
    else:
        # If CSV is empty, define a fallback date range
        min_date = datetime.now().date()
        max_date = datetime.now().date()

    st.sidebar.title("Filtro de Data (Otimização)")
    start_date = st.sidebar.date_input("Data inicial", value=min_date)
    end_date   = st.sidebar.date_input("Data final",   value=max_date)

    # If user picks the same date for both, treat it as "that single day."
    if start_date == end_date:
        st.write(f"Exibindo registros **somente** do dia: {start_date}")
        start_dt = datetime.combine(start_date, datetime.min.time())
        end_dt   = datetime.combine(end_date,   datetime.max.time())
    else:
        st.write(f"Exibindo registros de **{start_date}** até **{end_date}**")
        start_dt = datetime.combine(start_date, datetime.min.time())
        end_dt   = datetime.combine(end_date,   datetime.max.time())

    # 4) Filter the DataFrame by date
    mask = (df["data"] >= start_dt) & (df["data"] <= end_dt)
    df_filtered = df[mask].copy()

    # 5) Show the results
    st.subheader("Logs de Otimização Filtrados")
    st.dataframe(df_filtered, use_container_width=True, height=400)

if __name__ == "__main__":
    main()