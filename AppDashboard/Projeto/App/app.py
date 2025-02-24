import streamlit as st
import pandas as pd
import io,time
from streamlit_autorefresh import st_autorefresh
from database_connection import connect_database
from pathlib import Path
import os
from datetime import datetime
import requests,os,io
import pandas as pd

HOST_NAME = os.getenv("HOST_NAME")
ACESS_TOKEN = os.getenv("ACESS_TOKEN")
BOOKS_JOB_ID = os.getenv("BOOKS_JOB_ID")
SQL_HTTP_PATH = os.getenv("SQL_HTTP_PATH")

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

def atualiza_tabela_books()->bool:
    url = f"https://{HOST_NAME}/api/2.2/jobs/run-now"
    
    headers = {
      "Authorization": f"Bearer {ACESS_TOKEN}",
      "Content-Type": "application/json"
    }

    params = {
        "job_id": BOOKS_JOB_ID 
    }

    response = requests.post(url=url,headers=headers,params=params)
    if response.status_code == 200:
       return True
    else:
       return False

def job_atualizacao_rodando()->bool | None:
    url = f"https://{HOST_NAME}/api/2.2/jobs/runs/list"
    
    headers = {
      "Authorization": f"Bearer {ACESS_TOKEN}",
      "Content-Type": "application/json"
    }

    params = {
        "job_id": BOOKS_JOB_ID,
        "active_only": "true" 
    }

    response = requests.get(url=url,headers=headers,params=params)
    if response.status_code == 200:
        response = response.json()

        if "runs" not in response: #não tem nenhuma run no momento
            return False
        else:
            return True
    else:
       return None

def popup_esperar_job(acabou_espera= False)->None:
    texto1 = "Tabelas AtualizadaS, prossiga para janela de EtapasBoletagem" if acabou_espera else "Esperando Atualização das tabelas com novo ativo"
    texto2 = "" if acabou_espera else "Antes de usar o resto da aplicação, por favor espere as tabelas atualizarem."

    st.markdown(
f"""
        <style>
        /* Fullscreen transparent overlay */
        .overlay {{
            position: fixed; 
            top: 0; 
            left: 0; 
            width: 100%; 
            height: 100%;
            background: rgba(0, 0, 0, 0.5);
            z-index: 9999;
            display: flex;
            justify-content: center;
            align-items: center;
        }}
        /* White box in the middle */
        .popup {{
            background: #fff;
            padding: 20px 30px;
            border-radius: 8px;
            text-align: center;
        }}
        </style>
        <div class="overlay">
          <div class="popup">
            <h3>{texto1}</h3>
            <p>{texto2}</p>
          </div>
        </div>
        """,
        unsafe_allow_html=True
    ) 

# Função para adicionar linha
def add_row():
    st.session_state.df = pd.concat([
        st.session_state.df, 
        pd.DataFrame([["", "", "", ""]], columns=st.session_state.df.columns)
    ], ignore_index=True)

# Função para remover linha
def remove_row():
    if not st.session_state.df.empty:
        st.session_state.df = st.session_state.df.iloc[:-1]

# Função para exportar CSV
def export_csv():
    df_filtered = st.session_state.df.replace("", pd.NA).dropna(how="all")

    if df_filtered.isna().any(axis=1).sum() > 0:
        st.warning("Existem linhas incompletas. Todas as colunas de uma linha devem estar preenchidas para exportação.")
        return None,False
    
    output = io.StringIO()
    df_filtered.to_csv(output, index=False)
    return df_filtered, output.getvalue()

# Função para verificar ativos
def verifica_ativos(df_app: pd.DataFrame):

    ativos_nao_encontrados = [
        ativo for ativo in df_app["Ticker"]
        if ativo.lower() not in st.session_state.df_verificacao["ativo"].str.lower().values
    ]

    if ativos_nao_encontrados:
        st.session_state.df_popup = pd.DataFrame([[ativos_nao_encontrados[0], "", ""]], 
                                                 columns=["Ativo", "Book", "Fundos Restritos"])
        st.session_state.show_popup = True
        st.rerun()

def cria_ativo_book(ativo:str, book:str, fundos_restritos:str):
    dir_atual = Path(os.getcwd())
    path_final = dir_atual.absolute().parent.parent.parent / Path("ScriptsSQL") / Path("TemplatesPython")
    with open(path_final / Path("inserir_book_ativos.sql"), "r") as file:
        sql_template = file.read()

    # Substitui os placeholders no template
    sql_query = sql_template.format(
        ativo=f"{ativo}",  # Aspas simples para strings no SQL
        book=f"{book}",
        fundos_restritos=f"{fundos_restritos}"
    )

    st.session_state.database.executa_query(sql_query)  

def main()->None:
    # Configurar a página
    st.set_page_config(page_title="Input de ordem - Crédito Privado", layout="wide")

    # Inicializar sessão
    if "df" not in st.session_state:
        st.session_state.df = pd.DataFrame([["", "", "", ""]] * 100, columns=["Ticker", "Amount", "Price", "Broker"])

    #variáveis de seção
    if "show_extra" not in st.session_state:
        st.session_state.show_extra = False #mostra tela das Etapas Boletagem
    if "refresh_page" not in st.session_state:
        st.session_state.refresh_page = False #da um refresh único na tela
    if "cadastrou_ativo" not in st.session_state:
        st.session_state.cadastrou_ativo = False #diz se usuário cadastrou um novo ativo

    #dá refresh na tela se a flag tiver ativada
    if st.session_state.refresh_page:
        # A minimal interval=100 (ms) or 1 (ms) works for a near-instant refresh
        st_autorefresh(interval=10, limit=1, key="page_refresh_trigger")
        # Reset refresh_page to False so it doesn't keep refreshing
        st.session_state.refresh_page = False

    if "database" not in st.session_state:
        st.session_state.database = connect_database.Database()

    if "df_verificacao" not in st.session_state:
        st.session_state.df_verificacao = st.session_state.database.select_to_dataframe(
            """select * from desafio_kinea.boletagem_cp.book_ativos"""
        )
        
    if "show_popup" not in st.session_state:
        st.session_state.show_popup = False
    if "df_popup" not in st.session_state:
        st.session_state.df_popup = pd.DataFrame(columns=["Ativo", "Book", "Fundos Restritos"])

    # Layout da página
    st.title("Input da ordem para ser processada", anchor=False)

    # --- BLOQUEIA A INTERFACE PRINCIPAL SE O POPUP ESTIVER ABERTO ---
    if not st.session_state.show_popup:

        # Grid de edição principal
        col1, col2, col3 = st.columns([1, 3, 1])
        with col2:
            edited_df = st.data_editor(st.session_state.df, num_rows="fixed", use_container_width=True)
            if not edited_df.equals(st.session_state.df):
                st.session_state.df = edited_df.copy()
                st.rerun()

        # Botões de adicionar e remover linha
        col_btn = st.columns([5, 1, 1, 5])
        with col_btn[1]:
            st.button("➕", on_click=add_row)
        with col_btn[2]:
            st.button("➖", on_click=remove_row)

        # Botão de download CSV
        with col3:
            df_filtered, csv_data = export_csv()
            if csv_data:
                if st.button("Encaminhar Ordem"):
                    verifica_ativos(df_filtered)
                    resultado_upload:bool = upload_ordem(df_filtered) #faz upload do DF no volume
                    if resultado_upload: #upload teve sucesso
                        st.session_state.show_extra = not st.session_state.show_extra #libera para ver tela do EtapasBoletagem
                        st.session_state.refresh_page = True
                        st.success("Ordem encaminhada, tela de Etapas Boletagem Disponível")
                        
                        if st.session_state.cadastrou_ativo: #cadastrou novo ativo, precisamos atualizar tabela de books
                            resultado_atualizacao:bool = atualiza_tabela_books()

                            if resultado_atualizacao:
                                job_rodando = True

                                while job_rodando: #loop até o job de atualização acabar
                                    popup_esperar_job() #popup para o usuário saber que está esperando
                                    job_rodando = job_atualizacao_rodando()
                                    if job_rodando is None:
                                        print("Falha ao checar status do job de atualização de books")
                                        break
                                    time.sleep(3) #para não fazer muitas chamadas de API
                                time.sleep(1)
                                popup_esperar_job(acabou_espera=True) #popup para mostrar pro user que ele pode seguir para as etapas
                                time.sleep(4)
                                st.rerun()
                                time.sleep(1)

                                
                            else:
                                print("Falha ao iniciar Job do databricks para atualizar arquivos de books dos ativos")

                    else:
                        print("Falha ao dar upload do arquivo no volume do databricks")
    

    # --- POPUP ESTILO MODAL ---
    if st.session_state.show_popup:
        st.markdown(
            """
            <style>
            .popup {
                position: fixed;
                top: 20%;
                left: 50%;
                transform: translate(-50%, -20%);
                background: white;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0px 0px 10px rgba(0,0,0,0.3);
                z-index: 1000;
            }
            </style>
            """,
            unsafe_allow_html=True
        )

        with st.container():
            st.error("⚠️ O ativo abaixo não foi encontrado. Preencha as informações para continuar.")

            edited_popup_df = st.data_editor(st.session_state.df_popup, num_rows="fixed", use_container_width=True)

            st.info("Caso haja a intenção de adicionar mais de um fundo restrito, separe-os por `;`")

            col_btn_popup = st.columns([2, 1])
            with col_btn_popup[0]:
                if st.button("Confirmar"):
                    st.session_state.show_popup = False
                    st.session_state.cadastrou_ativo = True #usuário cadastrou um ativo
                    edited_popup_df = edited_popup_df.rename(columns={"Ativo": "ativo", "Book": "book", "Fundos Restritos": "fundo_restrito"})
                    st.session_state.df_popup = edited_popup_df

                    cria_ativo_book(edited_popup_df.iloc[0]["ativo"],
                                    edited_popup_df.iloc[0]["book"],
                                    edited_popup_df.iloc[0]["fundo_restrito"]
                    )

                    st.session_state.df_verificacao = pd.concat([st.session_state.df_verificacao,pd.DataFrame({
                        "ativo": [edited_popup_df.iloc[0]["ativo"]],
                        "book": [edited_popup_df.iloc[0]["book"]],
                        "fundo_restrito": [edited_popup_df.iloc[0]["fundo_restrito"]]})],
                    ignore_index=True
                    )
                    
                    st.rerun()
            with col_btn_popup[1]:
                if st.button("Cancelar"):
                    st.session_state.show_popup = False
                    st.rerun()

if __name__ == "__main__":
    if HOST_NAME is None:
        st.error("A variável de ambiente HOST_NAME não está definida.")
        st.stop()

    if ACESS_TOKEN is None:
        st.error("A variável de ambiente ACESS_TOKEN não está definida.")
        st.stop()

    if BOOKS_JOB_ID is None:
        st.error("A variável de ambiente BOOKS_JOB_ID não está definida.")
        st.stop()
    
    if SQL_HTTP_PATH is None:
        st.error("A variável de ambiente SQL_HTTP_PATH não está definida.")
        st.stop()
        
    main()