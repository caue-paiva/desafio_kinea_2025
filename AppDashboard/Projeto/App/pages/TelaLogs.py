import streamlit as st
import csv, ast
import pandas as pd
from streamlit_autorefresh import st_autorefresh
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

@dataclass
class Log:
   data: datetime
   regra:str
   fundo:str
   memoria_calculo:str
   descricao_regra:str
   saldo_base_calculo:float
   valor_exposicao:float
   saldo_objeto:float
   ativos_desenquadrados: list[str] = field(default_factory=list)
   


import streamlit as st

def get_logs(depois_do_tempo:datetime | None = None)->list[Log]:
    """
    Função que retorna lista de logs. 
    Neste exemplo, estamos lendo do session_state para fins de demonstração.
    Se você quiser puxar do mesmo local que 'get_backend_status', basta replicar 
    a lógica ou importar a classe e gerar o dicionário lá.
    """
    # Caso queira logs "reais", poderia chamar:
    #   logs = st.session_state.tela.get_backend_status()["logs"]
    #   ou outra fonte de dados
    # Aqui, só para exemplo:
    logs = []
    print(Path().resolve())
    path = Path().resolve() / Path("pages") / Path("logs.csv")  

    with open(path, mode='r', encoding='utf-8', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert the date/time string
            row_datetime = datetime.strptime(row["data"], "%Y-%m-%d %H:%M:%S")
            
            # Filter by the 'after_dt'
            if depois_do_tempo is None or row_datetime > depois_do_tempo:
                # Safely convert the Python-like list string into a real list
                ativos_list = ast.literal_eval(row["ativos_desenquadrados"])
                
                # Build the Log object
                log_obj = Log(
                    data=row_datetime,
                    regra=row["regra"],
                    fundo=row["fundo"],
                    memoria_calculo=row["memoria_calculo"],
                    descricao_regra=row["descricao_regra"],
                    saldo_base_calculo=float(row["saldo_base_calculo"]),
                    valor_exposicao=float(row["valor_exposicao"]),
                    saldo_objeto=float(row["saldo_objeto"]),
                    ativos_desenquadrados=ativos_list
                )
                logs.append(log_obj)

    return logs

def main():
    st.set_page_config(layout="wide")
    st.title("Logs do Sistema")

    logs = get_logs()

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

    st.subheader("Tabela de Logs")

    # You can display as a static table:
    st.table(df)

    # Or an interactive table with sorting and filtering:
    # st.dataframe(df, use_container_width=True)

if __name__ == "__main__":
    main()
