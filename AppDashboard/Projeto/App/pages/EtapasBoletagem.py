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
      self.__timer_nexus = None

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
   
   def __baixa_resultado_arquivo(self,path_volume:str)->pd.DataFrame | None:
        """
        Baixa o arquivo do resultado final
        """
        path_arquivo:str = f"/Volumes/desafio_kinea/boletagem_cp/files/{path_volume}"
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

   def get_status_resultado_final(self) -> Literal['enquadrado', 'desenquadrado', 'esperando']:
        """
        Retorna o status do nexxus (mock), de dentro do session_state.
        """
        conteudo_dir_nexxus:list = self.__listdir_databricks("ResultadoFinal")  #arquivos nesse dir
        valor_debug:bool = st.session_state.mock_final_status
        
        return valor_debug or len(conteudo_dir_nexxus) != 0

   def get_backend_status(self):
        """
        pega os status dos componentes do back-end:

        -> Régua tem os status: pronta ou processando

        -> nexxus tem os status: esperando_calculo (quando a régua para input no nexxus não está pronta) e pronto_input (quando 
        a reǵua foi calculada e ele está esperando o input do usuário)

        -> resultado_final: É true ou False

        """
        status_data = {
            "regua_otimizada": {
                "status": "processando",        
            },
            "nexxus": {
                "status": "esperando_calculo", #2 estados: esperando_calculo e pronto_input
            },
            "resultado_final" : False
        }

        #verifica status da régua otimizada
        status_regua = self.get_status_regua()
        
        if status_regua:  # Régua otimizada está disponível
            status_data["regua_otimizada"]["status"] = "pronta"

            if self.__timer_nexus is None: #seta timer do nexxus se ele for none
                self.__timer_nexus = datetime.now()
            else: # Verifica se nexxus deu timeout
                tempo_decorrido = datetime.now() - self.__timer_nexus
                if tempo_decorrido >= self.__TIMEOUT_NEXUS: 
                    status_data["nexxus"]["status"] = "timeout"
                    status_data["logs"].append("Timeout no nexxus após 15 minutos de espera.")

            st.session_state.mock_nexxus_status  = "pronto_input" #nexxus está processando input
            status_data["nexxus"]["status"] = "pronto_input"
        else:  # Ainda  Calculando régua 
            status_data["regua_otimizada"]["status"] = "processando"
            self.__timer_nexus = None
            
            if st.session_state.mock_nexxus_status  == "pronto_input": #regua tava processando mas desenquadrou
                status_data["nexxus"]["status"] = "esperando_calculo" #agora nexxus vai esperar uma nova reǵua
                time.sleep(2) #sleep para poder mostrar mensagem para o user
                st.session_state.mock_nexxus_status  = 'esperando_calculo'
            

        resultado_final:bool = self.get_status_resultado_final() #status do resultado final
        if resultado_final:
            status_data["resultado_final"] = True
        
        return status_data

   # Função principal do Streamlit
   def run(self):
        st.title("Dashboard de Processo")

        # Criamos controles de estado no session_state.
        # Se não existirem, inicializamos com valores default.
        if "mock_regua" not in st.session_state:
            st.session_state.mock_regua = False  # False = ainda processando
        if "mock_nexxus_status" not in st.session_state:
            st.session_state.mock_nexxus_status = "esperando"
        if "mock_final_status" not in st.session_state:
            st.session_state.mock_final_status = False

        # Barra lateral para manipular o estado simulado da régua e do nexxus
        st.sidebar.title("Testar Cenários de Back-end")

        st.sidebar.subheader("Régua")
        if st.sidebar.button("Régua -> PRONTA"):
            st.session_state.mock_regua = True
        if st.sidebar.button("Régua -> PROCESSANDO"):
            st.session_state.mock_regua = False

        st.sidebar.subheader("Resultado Final")
        if st.sidebar.button("Resultado Final -> Pronto"):
            st.session_state.mock_final_status = True
        if st.sidebar.button("Resultado Final -> Esperando"):
            st.session_state.mock_final_status = False
       
        # Refresh automático (a cada 5s)
        st_autorefresh(interval=5000, limit=None, key="autorefresh")

        # Carrega o status vindo do “back-end”
        status_data = self.get_backend_status()

        # Monta a interface com 3 colunas, cada uma representando uma fase
        col_regua_otimizada, col_nexxus, col_final = st.columns(3)

        # Coluna da “Régua Inicial”
        with col_regua_otimizada:
            st.header("Régua Otimizada")
            
            regua_status = status_data["regua_otimizada"]["status"]            
            if regua_status == "pronta":
                st.success("Status: Régua Pronta")
                st.info("CSV disponível para download.")
                    
                df:pd.DataFrame | None  = self.__baixa_resultado_arquivo("InputNexxus/input_nexxus_ali.csv") #df da régua no formato do nexxus
                if df is not None: #df valido
                    csv_data = df.to_csv(index=False).encode('utf-8')
                
                    # botão de baixar CSV
                    st.download_button(
                                label="Clique para baixar CSV",
                                data=csv_data,
                                file_name="input_nexxus.csv",
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

        # Coluna do “nexxus” (nexxus)
        with col_nexxus:
            st.header("Nexxus")     
            nexxus_status = status_data["nexxus"]["status"]
       
            if nexxus_status == "esperando_calculo":
                st.warning("Aguardando cálculo de régua para o Nexxus")
            elif nexxus_status == "pronto_input":
                st.success("Nexxus está pronto para receber régua")
            elif nexxus_status == "timeout":
                st.error(f"nexxus em TIMEOUT! Processo demorou além do limite de {str(self.__TIMEOUT_NEXUS)}.")
            else:
                st.write(f"Status: {nexxus_status}")

        # ----------------------------------------------------------------------
        # Coluna Final
        # ----------------------------------------------------------------------
        with col_final:
            st.header("Final")
            resultado_final = status_data["resultado_final"]
            if resultado_final:
                
                st.success("Processo final concluído!")
                st.write("Ao baixar o CSV, a aplicação será resetada para seu estado inicial")
                    
                df:pd.DataFrame | None  = self.__baixa_resultado_arquivo("ResultadoFinal/resultado_final.csv") #df da régua no formato do resultado final
                if df is not None: #df valido
                    csv_data = df.to_csv(index=False).encode('utf-8')
                    
                    # botão de baixar CSV
                    click_download = st.download_button(
                                    label="Clique para baixar CSV final",
                                    data=csv_data,
                                    file_name="resultado_final.csv",
                                    mime="text/csv",
                    )

                    if click_download: #clicou em baixar
                        st.session_state.clear() #limpa o esta da aplicação
                        time.sleep(5) 
                        st.switch_page("app.py")
                        time.sleep(4) 
                        st.rerun()  # Recarrega a aplicação
                
                else: #df não valido por algum motivo
                        st.warning("Falha ao baixar CSV do resultado final.")
                    
               
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
  
