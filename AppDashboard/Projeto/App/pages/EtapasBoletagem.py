import streamlit as st
import time,requests,io,os
from streamlit_autorefresh import st_autorefresh
from datetime import timedelta,datetime
from typing import Literal
import pandas as pd
# ------------------------------------------------------------------------------
# Simulação de “backend”:
# Aqui, estamos apenas simulando a resposta de um backend que retorna o status
# de cada fase, bem como outras informações úteis (por exemplo, se há CSV disponível).
# Você pode adaptar para buscar essas informações via API, banco de dados, etc.
# ------------------------------------------------------------------------------

class TelaFases:

   __TIMEOUT_NEXUS = timedelta(minutes=15) #limite máximo para esperar uma resposta do desenquadramento do nexxus
   __timer_nexus: datetime | None #timer a partir do momento que a régua fica pronta, se for none a régua n está pronta

   HOST_NAME = os.getenv("HOST_NAME")
   ACESS_TOKEN = os.getenv("ACESS_TOKEN")

   def __init__(self):
      pass

   def __listdir_databricks(self,nome_dir:str)->list | None:
        """
        Lista os arquivos de uma diretório no Databricks ou retorna None se ele não existir
        """
        path_base = "/Volumes/desafio_kinea/boletagem_cp/files/"
        api_url = f"https://{self.HOST_NAME}/api/2.0/fs/directories{path_base}{nome_dir}"

        headers = {
            "Authorization": f"Bearer {self.ACESS_TOKEN}",
            "Content-Type": "application/octet-stream"
        }

        response = requests.get(url=api_url,headers=headers)
        if response.status_code == 200:
            data = response.json()
            contents = data.get('contents', [])
            
            entries = []
            for item in contents:
                entry = {
                    'path': item.get('path'),
                    'is_directory': item.get('is_directory', False),
                    'file_size': item.get('file_size'),  # may be None or omitted if it's a directory
                    'last_modified': item.get('last_modified'),
                    'name': item.get('name')
                }
                entries.append(entry)

            return entries
        else:
            print(f"Falha ao lista arquivos do diretório {nome_dir}")
            return None
   
   def __baixa_input_nexxus(self)->pd.DataFrame | None:
        """
        Baixa o arquivo de input para o nexxus que está no diretório InputNexxus/ do volume 
        """
        path_arquivo:str = "/Volumes/desafio_kinea/boletagem_cp/files/InputNexxus/input_nexxus_teste.csv"
        url = f"https://{self.HOST_NAME}/api/2.0/fs/files{path_arquivo}"

        headers = {
            "Authorization": f"Bearer {self.ACESS_TOKEN}",
            "Content-Type": "application/octet-stream"
        }

        response = requests.get(url=url,headers=headers)

        if response.status_code == 200:
            df = pd.read_csv(io.BytesIO(response.content))
            return df
        else:
            print(f"Falha ao baixar arquivo do path {path_arquivo}")
            return None

   def get_status_regua(self) -> bool:
        """
        verifica no volume InputNexxus se o arquivo CSV que combina todas as réguas no formato de input do databricks está pronta.
        Retorna true se o diretório não estiver vazio
        """
        conteudo_dir_reguas:list = self.__listdir_databricks("InputNexxus")  #arquivos nesse dir
        valor_debug:bool = st.session_state.mock_regua
        
        return valor_debug or len(conteudo_dir_reguas) != 0

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
            "regua_otimizada": {
                "status": "",         
                "csv_disponivel": False
            },
            "nexxus": {
                "status": "esperando", #nexxus por padrão está  esperando (ou a régua ou o resultado do enquadramento)
                "csv_disponivel": False
            },
            "logs": [
                "Log 1: Processo iniciado às 10:00",
                "Log 2: Régua Otimizada concluída às 10:05",
                "Log 3: nexxus em processamento às 10:06",
            ]
        }

         #verifica status da régua otimizada
        status_regua = self.get_status_regua()
        #print(status_regua)
        if status_regua:
            # Régua otimizada está disponível
            status_data["regua_otimizada"]["status"] = "pronta"
            status_data["regua_otimizada"]["csv_disponivel"] = True
            self.__timer_nexus = datetime.now()
        else:
            # Ainda  Calculando régua 
            status_data["regua_otimizada"]["status"] = "processando"
            status_data["regua_otimizada"]["csv_disponivel"] = False
            self.__timer_nexus = None
            status_data["nexxus"]["status"] = "esperando" #nexxus está esperando a régua
            if st.session_state.mock_nexxus_status  == 'desenquadrado':
                time.sleep(2)
                st.session_state.mock_nexxus_status = "esperando"
         

        status_nexxus = self.get_status_nexxus() #status do nexxus
        if status_nexxus == "esperando"  and self.__timer_nexus is not None:
            tempo_decorrido = datetime.now() - self.__timer_nexus
            if tempo_decorrido >= self.__TIMEOUT_NEXUS:
                # Bateu no timeout
                status_data["nexxus"]["status"] = "timeout"
                # Aqui você pode implementar a lógica de erro, logs adicionais, etc.
                status_data["logs"].append("Timeout no nexxus após 15 minutos de espera.")
   
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
        #st.set_page_config(page_title="Dashboard de Processo", layout="wide")
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
        col_regua_otimizada, col_nexxus, col_final = st.columns(3)

        # ----------------------------------------------------------------------
        # Coluna da “Régua Inicial”
        # ----------------------------------------------------------------------
        with col_regua_otimizada:
            st.header("Régua Otimizada")
            
            regua_status = status_data["regua_otimizada"]["status"]
            csv_regua_disponivel = status_data["regua_otimizada"]["csv_disponivel"]
            
            if regua_status == "pronta":
                st.success("Status: Régua Pronta")
                if csv_regua_disponivel:
                    st.info("CSV disponível para download.")
                    
                    df:pd.DataFrame | None  = self.__baixa_input_nexxus() #df da régua no formato do nexxus
                    if df is not None: #df valido
                        csv_data = df.to_csv(index=False).encode('utf-8')
                
                        # botão de baixar CSV
                        st.download_button(
                                label="Clique para baixar CSV",
                                data=csv_data,
                                file_name="regua_otimizada.csv",
                                mime="text/csv",
                        )
                    else: #df não valido por algum motivo
                        st.warning("Falha ao baixar CSV do input do Nexxus.")

            elif regua_status == "processando":
                st.warning("Status: Processando...")
            elif regua_status == "erro":
                st.error("Ocorreu um erro na fase ‘Régua Inicial’!")
            else:
                # Se for vazio ou algo que não mapeamos, mostramos cru
                st.write(f"Status: {regua_status}")

        # ----------------------------------------------------------------------
        # Coluna do “nexxus” (nexxus)
        # ----------------------------------------------------------------------
        with col_nexxus:
            st.header("nexxus")
            
            nexxus_status = status_data["nexxus"]["status"]
            #print("status nexxus: ", nexxus_status)
            csv_nexxus_disponivel = status_data["nexxus"]["csv_disponivel"]
            
            if nexxus_status == "esperando":
                st.warning("Aguardando input de régua ou calculo...")
            elif nexxus_status == "sucesso":
                st.success("Processo concluído com sucesso!")
                if csv_nexxus_disponivel:
                    if st.button("Baixar CSV - nexxus"):
                        st.write("Lógica de download do CSV do nexxus aqui...")
                else:
                    st.info("CSV de nexxus não disponível no momento.")
            elif nexxus_status == "enquadrado":
                st.success("nexxus enquadrado!")
            elif nexxus_status == "desenquadrado":
                st.error("nexxus desenquadrado!")
            elif nexxus_status == "timeout":
                st.error("nexxus em TIMEOUT! Processo demorou além do limite.")
            else:
                st.write(f"Status: {nexxus_status}")

        # ----------------------------------------------------------------------
        # Coluna Final
        # ----------------------------------------------------------------------
        with col_final:
            st.header("Final")
            if nexxus_status == "enquadrado" and regua_status == "pronta":
                st.success("Processo final concluído!")
                if st.button("Baixar CSV - Ordem final"):
                    st.write("Baixando CSV, a aplicação será resetada para seu estado inicial")
                    st.write("Lógica de download do CSV do nexxus aqui...")
                    
                    st.session_state.clear() #limpa o esta da aplicação
                    time.sleep(3) 
                    st.switch_page("app.py")
                    time.sleep(1.5) 
                    st.rerun()  # Recarrega a aplicação


            else:
                st.warning("Aguardando conclusão das etapas anteriores...")


if __name__ == "__main__":

   # checar variável de sessão de mostrar tela de etapa boletagem
   if "show_extra" not in st.session_state:
      st.session_state.show_extra = False

   if st.session_state.show_extra:
      #Tela das etapas da boletagem está habilitada
      if "tela" not in st.session_state:
        st.session_state.tela = TelaFases()

      tela = st.session_state.tela
      tela.run()
   
   else:
      st.write("Para mostrar a tela de Etapas da Boletagem é necessário submeter uma ordem na tela app.")
  
