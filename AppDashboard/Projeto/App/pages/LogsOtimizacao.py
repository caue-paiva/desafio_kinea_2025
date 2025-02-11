from dataclasses import dataclass, field
from datetime import datetime
import streamlit as st
import csv, ast
import pandas as pd
from pathlib import Path

@dataclass
class LogOtimizacao:
   ativo:str
   data_ordem:datetime
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
    path = Path().resolve() / "pages" / "logs_otimizacao.csv"

    with open(path, mode="r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Parse the date/time
            row_datetime = datetime.strptime(row["data_ordem"], "%Y-%m-%d %H:%M:%S")

            # Convert the list of fundos to a real Python list
            # (Expecting something like "['Fundo ABC','Fundo XYZ']")
            fundos_list = ast.literal_eval(row["fundos_alocados"])

            # Convert the boolean fields from text to bool
            passou_max_pl = row["passou_max_pl"].strip().lower() == "true"
            passou_max_emissor = row["passou_max_emissor"].strip().lower() == "true"
            passou_anos = row["passou_anos"].strip().lower() == "true"

            log_obj = LogOtimizacao(
                ativo=row["ativo"],
                data_ordem=row_datetime,
                iteracao_otimizador=int(row["iteracao_otimizador"]),
                fundos_alocados=fundos_list,
                passou_max_pl=passou_max_pl,
                passou_max_emissor=passou_max_emissor,
                passou_anos=passou_anos
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
            "data_ordem": log.data_ordem,  # Keep as datetime
            "iteracao_otimizador": log.iteracao_otimizador,
            "fundos_alocados": log.fundos_alocados,
            "passou_max_pl": log.passou_max_pl,
            "passou_max_emissor": log.passou_max_emissor,
            "passou_anos": log.passou_anos
        })

    df = pd.DataFrame(logs_dicts)

    # 3) Date Filter (Start / End)
    if not df.empty:
        min_date = df["data_ordem"].min().date()
        max_date = df["data_ordem"].max().date()
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
    mask = (df["data_ordem"] >= start_dt) & (df["data_ordem"] <= end_dt)
    df_filtered = df[mask].copy()

    # 5) Show the results
    st.subheader("Logs de Otimização Filtrados")
    st.dataframe(df_filtered, use_container_width=True, height=400)


# If running this file directly (e.g., streamlit run pages/2_LogsOtimizacao.py)
if __name__ == "__main__":
    main()