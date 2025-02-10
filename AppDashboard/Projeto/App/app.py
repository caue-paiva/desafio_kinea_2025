import streamlit as st
import time,os
from streamlit_autorefresh import st_autorefresh
from datetime import timedelta,datetime
from typing import Literal

# ------------------------------------------------------------------------------
# Simulação de “backend”:
# Aqui, estamos apenas simulando a resposta de um backend que retorna o status
# de cada fase, bem como outras informações úteis (por exemplo, se há CSV disponível).
# Você pode adaptar para buscar essas informações via API, banco de dados, etc.
# ------------------------------------------------------------------------------

class TelaFases:

   __TIMEOUT_NEXUS = timedelta(minutes=15) #limite máximo para esperar uma resposta do desenquadramento do nexxus
   __timer_nexus: datetime | None #timer a partir do momento que a régua fica pronta, se for none a régua n está pronta

   def __init__(self):
      pass

   def get_status_regua(self) -> bool:
        """
        Verifica no session_state se a régua está disponível (mock).
        Retorna True se 'régua pronta', False se 'processando'.
        """
        return st.session_state.mock_regua

   def get_status_nexxus(self) -> Literal['enquadrado', 'desenquadrado', 'esperando']:
        """
        Retorna o status do nexxus (mock), de dentro do session_state.
        """
        return st.session_state.mock_nexxus_status

   def get_backend_status(self):
        """
         Monta o dicionário de status de cada fase do processo, baseando-se
         nos retornos das funções internas (get_status_regua / get_status_nexxus)
         e em possíveis ações (ex: timeout).
        """
        status_data = {
            "regua_inicial": {
                "status": "",         
                "csv_disponivel": False
            },
            "nexxus": {
                "status": "esperando", #nexxus por padrão está  esperando (ou a régua ou o resultado do enquadramento)
                "csv_disponivel": False
            },
            "final": {
                "status": "aguardando",   # Exemplo: assumimos que só passa para 'concluido' depois.
                "csv_disponivel": False
            },
            "logs": [
                "Log 1: Processo iniciado às 10:00",
                "Log 2: Régua inicial concluída às 10:05",
                "Log 3: nexxus em processamento às 10:06",
            ]
        }

         #verifica status da régua otimizada
        status_regua = self.get_status_regua()
        if status_regua:
            # Régua otimizada está disponível
            status_data["regua_inicial"]["status"] = "pronta"
            status_data["regua_inicial"]["csv_disponivel"] = True
            self.__timer_nexus = datetime.now()
        else:
            # Ainda  Calculando régua 
            status_data["regua_inicial"]["status"] = "processando"
            status_data["regua_inicial"]["csv_disponivel"] = False
            self.__timer_nexus = None
            status_data["nexxus"]["status"] = "esperando" #nexxus está esperando a régua
         

        status_nexxus = self.get_status_nexxus() #status do nexxus
        if status_nexxus == "esperando"  and self.__timer_nexus is not None:
            tempo_decorrido = datetime.now() - self.__timer_nexus
            if tempo_decorrido >= self.__TIMEOUT_NEXUS:
                # Bateu no timeout
                status_data["nexxus"]["status"] = "timeout"
                # Aqui você pode implementar a lógica de erro, logs adicionais, etc.
                status_data["logs"].append("Timeout no nexxus após 15 minutos de espera.")
            else:
                status_data["nexxus"]["status"] = "esperando_resultado"
   
        elif status_nexxus == 'enquadrado':
            # Se o nexxus está enquadrado (ex.: “sucesso”)
            status_data["nexxus"]["status"] = "enquadrado"
            status_data["nexxus"]["csv_disponivel"] = True
            status_data["logs"].append("nexxus concluído com status 'enquadrado'.")

        elif status_nexxus == 'desenquadrado':
            # Se o nexxus está desenquadrado (ex.: “falha”)
            status_data["nexxus"]["status"] = "desenquadrado"
            status_data["nexxus"]["csv_disponivel"] = False
            status_data["logs"].append("nexxus concluído com status 'desenquadrado'.")


        
        return status_data

   # ------------------------------------------------------------------------------
   # Função principal do Streamlit
   # ------------------------------------------------------------------------------
   def run(self):
        st.set_page_config(page_title="Dashboard de Processo", layout="wide")
        st.title("Dashboard de Processo")

        # ----------------------------------------------------------------------
        # Criamos controles de estado no session_state.
        # Se não existirem, inicializamos com valores default.
        # ----------------------------------------------------------------------
        if "mock_regua" not in st.session_state:
            st.session_state.mock_regua = False  # False = ainda processando
        if "mock_nexxus_status" not in st.session_state:
            st.session_state.mock_nexxus_status = "esperando"

        # ----------------------------------------------------------------------
        # Barra lateral para manipular o estado simulado da régua e do nexxus
        # ----------------------------------------------------------------------
        st.sidebar.title("Testar Cenários de Back-end")

        st.sidebar.subheader("Régua")
        if st.sidebar.button("Régua -> PRONTA"):
            st.session_state.mock_regua = True
        if st.sidebar.button("Régua -> PROCESSANDO"):
            st.session_state.mock_regua = False

        st.sidebar.subheader("nexxus")
        if st.sidebar.button("nexxus -> ENQUADRADO"):
            st.session_state.mock_nexxus_status = "enquadrado"
        if st.sidebar.button("nexxus -> DESENQUADRADO"):
            st.session_state.mock_nexxus_status = "desenquadrado"
        if st.sidebar.button("nexxus -> ESPERANDO"):
            st.session_state.mock_nexxus_status = "esperando"

        # ----------------------------------------------------------------------
        # Refresh automático (a cada 5s)
        # ----------------------------------------------------------------------
        st_autorefresh(interval=5000, limit=None, key="autorefresh")

        # Carrega o status vindo do “back-end”
        status_data = self.get_backend_status()

        # Monta a interface com 3 colunas, cada uma representando uma fase
        col_regua_inicial, col_nexclus, col_final = st.columns(3)

        # ----------------------------------------------------------------------
        # Coluna da “Régua Inicial”
        # ----------------------------------------------------------------------
        with col_regua_inicial:
            st.header("Régua Inicial")
            
            regua_status = status_data["regua_inicial"]["status"]
            csv_regua_disponivel = status_data["regua_inicial"]["csv_disponivel"]
            
            if regua_status == "pronta":
                st.success("Status: Régua Pronta")
                if csv_regua_disponivel:
                    st.info("CSV disponível para download.")
                    if st.button("Baixar CSV - Régua Inicial"):
                        st.write("Lógica de download do CSV aqui...")
                else:
                    st.warning("CSV ainda não está disponível.")
            elif regua_status == "processando":
                st.warning("Status: Processando...")
            elif regua_status == "erro":
                st.error("Ocorreu um erro na fase ‘Régua Inicial’!")
            else:
                # Se for vazio ou algo que não mapeamos, mostramos cru
                st.write(f"Status: {regua_status}")

        # ----------------------------------------------------------------------
        # Coluna do “Nexclus” (nexxus)
        # ----------------------------------------------------------------------
        with col_nexclus:
            st.header("nexxus")
            
            nexclus_status = status_data["nexxus"]["status"]
            csv_nexclus_disponivel = status_data["nexxus"]["csv_disponivel"]
            
            if nexclus_status == "esperando_resultado":
                st.warning("Aguardando resultado do processamento...")
            elif nexclus_status == "sucesso":
                st.success("Processo concluído com sucesso!")
                if csv_nexclus_disponivel:
                    if st.button("Baixar CSV - nexxus"):
                        st.write("Lógica de download do CSV do nexxus aqui...")
                else:
                    st.info("CSV de nexxus não disponível no momento.")
            elif nexclus_status == "enquadrado":
                st.success("nexxus enquadrado!")
                if csv_nexclus_disponivel:
                    if st.button("Baixar CSV - nexxus"):
                        st.write("Lógica de download do CSV do nexxus aqui...")
                else:
                    st.info("CSV de nexxus não disponível no momento.")
            elif nexclus_status == "desenquadrado":
                st.error("nexxus desenquadrado!")
            elif nexclus_status == "timeout":
                st.error("nexxus em TIMEOUT! Processo demorou além do limite.")
            elif nexclus_status == "recalcula_regua":
                st.info("Necessário recalcular a Régua.")
                if st.button("Recalcular Régua"):
                    st.write("Lógica para solicitar recalcular a régua (chamada backend).")
            else:
                st.write(f"Status: {nexclus_status}")

        # ----------------------------------------------------------------------
        # Coluna Final
        # ----------------------------------------------------------------------
        with col_final:
            st.header("Final")
            
            final_status = status_data["final"]["status"]
            csv_final_disponivel = status_data["final"]["csv_disponivel"]
            
            if final_status == "concluido":
                st.success("Processo final concluído!")
                if csv_final_disponivel:
                    if st.button("Baixar CSV - Etapa Final"):
                        st.write("Lógica de download do CSV final aqui...")
                else:
                    st.warning("CSV final não disponível no momento.")
            elif final_status == "aguardando":
                st.warning("Aguardando conclusão das etapas anteriores...")
            else:
                st.write(f"Status: {final_status}")

        # ----------------------------------------------------------------------
        # Exibir logs recentes
        # ----------------------------------------------------------------------
        st.subheader("Ver últimos logs")
        if "logs" in status_data and status_data["logs"]:
            for log in status_data["logs"]:
                st.text(log)
        else:
            st.write("Nenhum log disponível.")


if __name__ == "__main__":
   if "tela" not in st.session_state:
        st.session_state.tela = TelaFases()

   tela = st.session_state.tela
   tela.run()
