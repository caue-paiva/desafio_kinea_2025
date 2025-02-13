import streamlit as st
import pandas as pd
import io
from streamlit_autorefresh import st_autorefresh

# Configurar a página
st.set_page_config(page_title="Input de ordem - Crédito Privado", layout="wide")

# Inicializar sessão
if "df" not in st.session_state:
    st.session_state.df = pd.DataFrame([["", "", ""]] * 100, columns=["Ticker", "Amount", "Price"])

#variáveis de seção
if "show_extra" not in st.session_state:
    st.session_state.show_extra = False #mostra tela das Etapas Boletagem
if "refresh_page" not in st.session_state:
    st.session_state.refresh_page = False #da um refresh único na tela

#dá refresh na tela se a flag tiver ativada
if st.session_state.refresh_page:
    # A minimal interval=100 (ms) or 1 (ms) works for a near-instant refresh
    st_autorefresh(interval=10, limit=1, key="page_refresh_trigger")
    # Reset refresh_page to False so it doesn't keep refreshing
    st.session_state.refresh_page = False

# TODO Remover, só para uso de testes para ainda sem integração com a base de dados com a query inserir_book_ativos.sql e 
if "df_verificacao" not in st.session_state:
    st.session_state.df_verificacao = pd.DataFrame({
        "Ativo": ["KNRI11", "ABCD11", "DEFG11", "HIJK11"],
        "fundo": ["ABC", "DEF", "GHI", "JKL"],
        "fundo_restrito": ["", "", "", ""],
        "blabla": ["", "", "", ""]
    })

if "show_popup" not in st.session_state:
    st.session_state.show_popup = False
if "df_popup" not in st.session_state:
    st.session_state.df_popup = pd.DataFrame(columns=["Ativo", "Book", "Fundos Restritos"])

# Função para adicionar linha
def add_row():
    st.session_state.df = pd.concat([
        st.session_state.df, 
        pd.DataFrame([["", "", ""]], columns=st.session_state.df.columns)
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

    ativos_nao_encontrados = [ativo for ativo in df_app["Ticker"] if ativo not in st.session_state.df_verificacao["Ativo"].values]

    if ativos_nao_encontrados:
        print("ativos não encontrados", ativos_nao_encontrados)
        st.session_state.df_popup = pd.DataFrame([[ativos_nao_encontrados[0], "", ""]], 
                                                 columns=["Ativo", "Book", "Fundos Restritos"])
        st.session_state.show_popup = True
        st.rerun()
    # TODO Trocar o download button para triggar o upload de um arquivo para o volume dentro do databricks
    else:
        st.write("Acabou, é tetra!") # TODO remover, apenas piada..

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
                st.session_state.show_extra = not st.session_state.show_extra #libera para ver tela do EtapasBoletagem
                st.session_state.refresh_page = True
                st.success("Ordem encaminhada, tela de Etapas Boletagem Disponível")

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
                st.session_state.df_popup = edited_popup_df
                
                #TODO trocar pela função de atualização da base de dados (chamar o script inserir_book_ativos.sql)

                st.session_state.df_verificacao = pd.concat([st.session_state.df_verificacao,pd.DataFrame({
                    "Ativo": [edited_popup_df.iloc[0]["Ativo"]],
                    "fundo": [edited_popup_df.iloc[0]["Book"]],
                    "fundo_restrito": [edited_popup_df.iloc[0]["Fundos Restritos"]],
                    "blabla": [""]})],
                ignore_index=True
                )
                
                st.rerun()
        with col_btn_popup[1]:
            if st.button("Cancelar"):
                st.session_state.show_popup = False
                st.rerun()
