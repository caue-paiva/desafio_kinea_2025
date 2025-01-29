import pandas as pd
import re
from dataclasses import dataclass
from DadosAlocacao import DadosAlocacao
from databricks.sdk.runtime import *

class VerificadorTabelacar:

    __dados_alocacao = DadosAlocacao()

    __MAPEAMENTO_FUNDOS_TABELACAR = {
          'CAR Baixo Risco':            'desafio_kinea.boletagem_cp.tabelacar_baixorisco',
          'CAR Médio Risco':            'desafio_kinea.boletagem_cp.tabelacar_mediorisco', 
          'CAR Fundos Hibridos':        'desafio_kinea.boletagem_cp.tabelacar_hibridos',
          'Dedicado Alto Risco':        'desafio_kinea.boletagem_cp.tabelacar_dedicadoaltorisco',
          'CAR Fundos HY':              'desafio_kinea.boletagem_cp.tabelacar_hy',
          'CAR Fundos Mistos':          'desafio_kinea.boletagem_cp.tabelacar_criinfra',
          'Dedicado CapitalSolutions':  'desafio_kinea.boletagem_cp.tabelacar_capitalsolutions'
    }

    __dict_tipocar_para_tabelacar: dict[str,pd.DataFrame] #mapea um tipocar para o dataframe de sua tabela
    __dict_fundo_tipo_car: dict[str,str] #mapea um fundo para seu tipo car

    def __init__(self):
        df_mapa_tabelacar =  self.__dados_alocacao.get_mapa_tabelacar() #carrega df do mapa fundo -> tipo_car
        self.__dict_tipocar_para_tabelacar = {}
        self.__dict_fundo_tipo_car = {}
        
        for row in df_mapa_tabelacar.itertuples(): #cria mapeamento fundo -> tipo_car
            fundo:str = row.Fundo
            TipoCar:str = row.TipoCAR
            self.__dict_fundo_tipo_car[fundo] = TipoCar

        for tipo_car,tabelacar in self.__MAPEAMENTO_FUNDOS_TABELACAR.items(): #cria mapeamento tipo_car -> df da tabelacar
            self.__dict_tipocar_para_tabelacar[tipo_car] = spark.sql(f"select * from {tabelacar}").toPandas()


    def __tabelacar_do_fundo(self,fundo:str)->pd.DataFrame:
        tipo_car :str|None = self.__dict_fundo_tipo_car.get(fundo,None)
        if tipo_car is None:
            raise Exception("Fundo não foi mapeado para um tipo car")
    
        df: pd.DataFrame | None = self.__dict_tipocar_para_tabelacar.get(tipo_car,None)
        if df is None:
            raise Exception(f"Não existe tabela para o tipo car {tipo_car}")
        return df
            
    def __primeiro_numero_e_posicao(self,string:str)->tuple[int,int]:
        for i,char in enumerate(string):
            if char.isnumeric():
                return int(char), i
        
        return -1,-1

    def __construir_dict_ratings(self, lista_ratings:list[str],list_niveis:list[int])->dict:
        dict_ratings = {}
        for rating,nivel in zip(lista_ratings,list_niveis):
            valores_nivel = []
            if " a " in rating: #rating é um range
                if "Aaa" in rating:
                    valores_nivel = ["Aaa","Aa2","Aa3"] #Por enquanto vai ficar hardcoded ppq eu n entendi essa parte
                else:
                    primeiro_num, index1 = self.__primeiro_numero_e_posicao(rating)
                    segundo_num,  index2 = self.__primeiro_numero_e_posicao(rating[index1+1:])

                    str_base = rating[:index1]
                    valores_nivel = [
                        f"{str_base}{str(x)}" for x in range(primeiro_num,segundo_num+1)
                    ]
            else:
                valores_nivel = [rating]
            dict_ratings[nivel] = valores_nivel
        return dict_ratings

    def __get_ratings_igual_abaixo(self, rating:str, tabela_car:pd.DataFrame )->list[str]:
        lista_ratings = []
        lista_nivels = []
        for row in tabela_car.itertuples():
            if not hasattr(row, 'RatingKinea'):
                lista_ratings.append(row.IntervaloRating) # Trocar para IntervaloRating
                lista_nivels.append(row.Nivel)
            else:
                lista_ratings.append(row.RatingKinea)
                lista_nivels.append(row.Nivel)
        
        ratings_dict = self.__construir_dict_ratings(lista_ratings,lista_nivels)

        best_level = -1
        for key,val in  sorted(ratings_dict.items(),key= lambda x: x[0]):
            if rating in val: #se o rating esta na lista
                best_level  = key
                break
        if best_level == -1:
            raise RuntimeError("Não foi possível achar nível do rating")
        
        # print(best_level)
        return dict(
            filter(lambda x: x[0] >= best_level,ratings_dict.items()) #essa equação ou inequação é a principal coisa a se mudar caso precise modificar a lógica
        )

    def __guarda_resultado(self, fundo:str, alocacao_inicial:float, resultado_max_pl:dict[str,float], resultado_emissor_anos:dict[str,float], data_dict:dict )->None:
            passou_max_pl,passou_max_emissor,passou_l_anos,passou_todos = False,False,False,False

            if resultado_max_pl["diferenca_porcentagem_pl_rating"] >= 0:
                passou_max_pl = True
            if resultado_emissor_anos["diferenca_porcentagem_emissor"] >= 0:
                passou_max_emissor = True
            if resultado_emissor_anos["diferenca_porcentagem_ano"] >= 0:
                passou_l_anos = True
            passou_todos = passou_max_pl and passou_max_emissor and passou_l_anos

            data_dict["fundo"].append(fundo)
            data_dict["valor_alocacao_inicial"].append(alocacao_inicial)
            data_dict["diferenca_porcentagem_ano"].append(resultado_emissor_anos.get("diferenca_porcentagem_ano", 0))
            data_dict["diferenca_total_ano"].append(resultado_emissor_anos.get("diferenca_total_ano", 0))
            data_dict["diferenca_porcentagem_emissor"].append(resultado_emissor_anos.get("diferenca_porcentagem_emissor", 0))
            data_dict["diferenca_total_emissor"].append(resultado_emissor_anos.get("diferenca_total_emissor", 0))
            data_dict["diferenca_porcentagem_pl_privado"].append(resultado_max_pl.get("diferenca_porcentagem_pl_rating", 0))
            data_dict["diferenca_total_pl_privado"].append(resultado_max_pl.get("diferenca_total_pl_rating", 0))
            data_dict["passou_em_tudo"].append(passou_todos)
            data_dict["passou_max_pl"].append(passou_max_pl)
            data_dict["passou_max_emissor"].append(passou_max_emissor)
            data_dict["passou_l_anos"].append(passou_l_anos)

    def __verificacao_l_anos(self, linha_tabela_car:pd.DataFrame,vencimento_em_anos:int)->float | None:
        """
        Dado um linha da tabelacar, verifica se ela tem info sobre porcentagens de ativos pelo ano, e se tiver, retorna o valor em porcentagem que o ano passado como arg. se encaixa.
        Caso a tabela não tenha verificações, retorna None
        """
        tem_col_anos:bool = False
        prev_col:str = ""
        for col in linha_tabela_car.columns:
            if "ano" in col.lower():
                tem_col_anos = True
                ano_coluna:int = int(re.findall(r'\d+', col)[0])
                if ano_coluna == vencimento_em_anos: #exemplo coluna L8_anos e vencimento de 8 anos
                    return linha_tabela_car[col].values[0]
                elif ano_coluna > vencimento_em_anos: #exemplo colunas L6_anos, L8_anos e vencimento de 7 anos, retorna L6_anos 
                    if prev_col:
                        return linha_tabela_car[prev_col].values[0]
                    else: #não tem coluna anterior
                        return None
                prev_col = col
        
        return None #não tem coluna de ano 
    
    def __df_com_pl_total_e_por_rating(self, rating:str)->pd.DataFrame:
        df_pl_total = self.__dados_alocacao.get_pl_total_fundos()
        df_pl_rating = self.__dados_alocacao.get_pl_fundo_por_rating(rating)
        df_pl_rating = df_pl_rating.rename(columns={"total_credito":"pl_credito_privado_rating"})
        return df_pl_total.merge(df_pl_rating,how="inner",left_on="TradingDesk",right_on="TradingDesk")
    
    def __verificacao_emissor_e_l_anos(
        self,
        emissor_nome:str,
        fundo:str,
        pl_total_fundo:float,
        ratings_igual_ou_abaixo_emissor:dict,
        vencimento_em_anos:int,
        tabela_car_fundo:pd.DataFrame,
        alocacao_porcen:float,
        debug = False
    )->dict[str,float]:
        
        df_pl_por_emissor = self.__dados_alocacao.get_pl_e_rating_por_emissor() #df do pl de cada emissor num fundo
        df_pl_emissor_l_anos = self.__dados_alocacao.get_pl_por_emissor_e_vencimento_anos(vencimento_em_anos)
        linha_tabela_car:pd.DataFrame = tabela_car_fundo[tabela_car_fundo["Nivel"] == int(min(ratings_igual_ou_abaixo_emissor.keys()))] #filtra tabelacar pelos ratings do emissor
        
        porcentagem_max_pelo_ano:float | None = self.__verificacao_l_anos(linha_tabela_car,vencimento_em_anos) #porcentagem maximo do PL de um fundo por emissor
        porcentagem_max_pelo_emissor:float = linha_tabela_car["MaxEmissor"].values[0] #porcentagem maximo do pl de um fundo composta por ativos desse emissor com vencimento igual ou maior a L anos
        if porcentagem_max_pelo_ano is None: #a tabela não restringe por ano dos ativos, então a porcentagem que vamos olha é a do emissor (que é equivalente ao de L0 anos, representando nenhuma restrição quanto a data de vencimento)
            porcentagem_max_pelo_ano = porcentagem_max_pelo_emissor


        pl_emissor_no_fundo:float = df_pl_por_emissor[(df_pl_por_emissor["Emissor"] ==  emissor_nome) & (df_pl_por_emissor["TradingDesk"] == fundo)]["pl_emissor"].values[0] #valor liquido que o emissor tem naquele fundo para todos os ativos
        
        pl_emissor_l_anos_fundo:float = df_pl_emissor_l_anos[ (df_pl_emissor_l_anos["Emissor"] ==  emissor_nome) & (df_pl_emissor_l_anos["TradingDesk"] == fundo)]["pl_emissor"].iloc[0] #valor liquido que o emissor tem no fundo, apenas contando ativos que vencem em L ou mais anos

    
        if debug:
            print(f"Novo Pl total do emissor no fundo: {novo_pl_emissor}, Novo pl do emissor contando apenas ativos com vencimento de {vencimento_em_anos} anos ou mais: {novo_pl_l_anos}")
            print(f"porcentagens maximas pelo emissor: {porcentagem_max_pelo_emissor} e pelo ano: {porcentagem_max_pelo_ano}")

        porcentagem_real_pelo_ano:float =  (pl_emissor_l_anos_fundo / pl_total_fundo) + alocacao_porcen #porcentagem real depois da alocação
        porcentagem_real_emissor:float =  (pl_emissor_no_fundo / pl_total_fundo) + alocacao_porcen

        return {
            "diferenca_porcentagem_ano": porcentagem_max_pelo_ano - porcentagem_real_pelo_ano ,
            "diferenca_total_ano": (porcentagem_max_pelo_ano - porcentagem_real_pelo_ano) * pl_total_fundo,
            "diferenca_porcentagem_emissor":  porcentagem_max_pelo_emissor - porcentagem_real_emissor,
            "diferenca_total_emissor": (porcentagem_max_pelo_emissor - porcentagem_real_emissor) * pl_total_fundo,
        }

    def __verificacao_max_pl (self, linha_tabela_car:pd.Series, fundo:str, alocacao_porcen: float)->dict[str,float]:
        # TODO TODO TODO TODO !!!!!Pedir para o Rapha mudar nome da coluna p/ IntervaloRating para Tabela Car "Fundos Hibridos"!!!!!!
        if("IntervaloRating" not in linha_tabela_car.columns):
            linha_tabela_car.rename(columns={"RatingKinea":"IntervaloRating"},inplace=True)
        maior_rating_linha_tabela_car = linha_tabela_car["IntervaloRating"].values[0].split(" ")[0]  #acha o maior rating se for um range
       
        fundo_pl_cred_priv_pl_total = self.__df_com_pl_total_e_por_rating(maior_rating_linha_tabela_car) #pega PL de credito privado de um fundo  de um fundo filtrado por esse  rating
        df_pl_fltrado = fundo_pl_cred_priv_pl_total[fundo_pl_cred_priv_pl_total["TradingDesk"] == fundo]  #filtra pelo fundo
        pl_total:float = df_pl_fltrado["PL"].values[0] #pl total do fundo
        pl_credito_privado_rating: float = df_pl_fltrado["total_credito_rating"].values[0] #pl de credito pelo rating


        porcen_real_credito_privado_rating:float = (pl_credito_privado_rating / pl_total) + alocacao_porcen
        porcen_max_credito_privado_rating: float = linha_tabela_car["MaxPL"].values[0] #porcentagem maxima permitida pela tabelacar
        
        return {
            "diferenca_porcentagem_pl_rating": porcen_max_credito_privado_rating - porcen_real_credito_privado_rating,
            "diferenca_total_pl_rating": (porcen_max_credito_privado_rating - porcen_real_credito_privado_rating) * pl_total,
            "pl_total_fundo": pl_total
        }

    def verifica_alocacao(self,alocacao:pd.DataFrame,ativo:str)->pd.DataFrame:
        """
        Verifica uma alocação de um ativo em diversos fundos (alocação por porcentagem do PL de cada fundo) de acordo com as regras das tabelasCar (Associando o rating do ativo, rating de emissor e anos de vecimento dos ativos com limites de crédito de um fundo).

        Args:
            alocacao (pd.DataFrame): df das alocações, com uma coluna "fundo" com  a lista de fundos que o ativo será alocado e uma coluna "percentual_alocacao" com a lista de alocação (em percentual) de cada fundo (com o mesmo índice)
            ativo (str): nome do ativo que será alocado
        Return:
            (pd.DataFrame): df com as informações de cada fundo, a diferença total e em precentual de cada verificação com o maximo da tabelaCar (negativo => passou do limite) se passou ou não em cada uma das regras
        """
        data_dict = {
                "fundo": [],
                "valor_alocacao_inicial": [],
                "diferenca_porcentagem_ano": [],
                "diferenca_total_ano": [],
                "diferenca_porcentagem_emissor": [],
                "diferenca_total_emissor": [],
                "diferenca_porcentagem_pl_privado": [],
                "diferenca_total_pl_privado": [],
                "passou_em_tudo": [],
                "passou_max_pl": [],
                "passou_max_emissor": [],
                "passou_l_anos": []
        }
        #Transformando alocação em Dicionário
        fundos = alocacao['fundo']
        percentual_alocacao = alocacao['percentual_alocacao']
        alocacao_dict = {
            "fundo": fundos,
            "percentual_alocacao": percentual_alocacao
        }
    
        df_ativos = self.__dados_alocacao.get_info_rating_ativos() 
        #Pegar dados sobre o ativo,seus rating, o seu emissor e rating do emissor
        df_ativo_filtrado = df_ativos[df_ativos["Ativo"] == ativo]
        rating_ativo:str = df_ativo_filtrado["RatingOp"].values[0] 
        rating_emissor:str = df_ativo_filtrado["RatingGrupo"].values[0]
        emissor_nome:str = df_ativo_filtrado["Emissor"].values[0]
        vencimento_anos_ativo:int = int(df_ativo_filtrado["ExpiracaoAnos"].values[0])
        for i,fundo in enumerate(alocacao_dict["fundo"]):
            tabela_car_fundo: pd.DataFrame = self.__tabelacar_do_fundo(fundo)
            alocacao_valor: float = alocacao_dict["percentual_alocacao"][i] #valor a ser alocado
            ratingOP = df_ativos[df_ativos["Ativo"] == ativo]["RatingOp"].values[0]
            ratingGrupo = df_ativos[df_ativos["Ativo"] == ativo]["RatingGrupo"].values[0]
            ratings_igual_abaixo:dict = self.__get_ratings_igual_abaixo(df_ativos[df_ativos["Ativo"] == ativo]["RatingOp"].values[0],
                                                            tabela_car_fundo)
            
            ratings_igual_abaixo_emissor:dict = self.__get_ratings_igual_abaixo(df_ativos[df_ativos["Ativo"] == ativo]["RatingGrupo"].values[0],
                                                            tabela_car_fundo)
    
            # Linha referente ao rating do ativo específico e a tabela car referente ao fundo
            # Pega o maior rating da linha da tabela car relacionada ao ativo. Ex: rating_ativo = Baa3, linha = "Baa1 a Baa4" ->
            # Retornará Baa1. Será utilizado para pegar dos CSV's já salvos com a soma do position de todos os ativos abaixo de Baa1.
            # Caso seja apenas Baa3 no campo de rating da linha da tabela car, será pego o CSV relacionado à esse rating + os ativos abaixo 
            linha_tabela_car_ativo:pd.DataFrame = tabela_car_fundo[tabela_car_fundo["Nivel"] == int(min(ratings_igual_abaixo.keys()))] #df de uma linha
            resultado_max_pl = self.__verificacao_max_pl(
                linha_tabela_car_ativo,fundo,alocacao_valor
            )
            pl_total_fundo :float = resultado_max_pl["pl_total_fundo"]
            resultado_emissor_e_ano = self.__verificacao_emissor_e_l_anos(
                emissor_nome,fundo,pl_total_fundo,ratings_igual_abaixo_emissor,vencimento_anos_ativo,tabela_car_fundo,alocacao_valor
            )
            self.__guarda_resultado(fundo, alocacao_valor,resultado_max_pl,resultado_emissor_e_ano,data_dict) #append dos resultados no dict do resultado final

            # Variável fundo_porcentagem_pl_cred_priv poderá fazer a validação relacionada ao maxPL da tabela car da variável tabela_car_fundo
            # Variável pl_emissor_no_fundo poderá fazer a validação relacionada ao maxEmissor na da tabela car da variável tabela_car_fundo
            # TODO: Fazer validação se há as colunas de anos, e fazer a validação deles, caso seja válido. (Não lembro se era para substituir a validação de maxPL ou maxEmissor por essa de anos, ou se é uma validação à parte).
            # TODO: Gerar o output da forma que Sarah e João querem (fundo | excedente) (será em porcentagem? será que não deveriamos estar fazendo por quantidade de cotas excedentes? ou pela quantidade de PL excedente?) 

        df_final = pd.DataFrame(data_dict) #transforma o dict do resultado final em um Dataframe
        return df_final


if __name__ == "__main__":
    verificador = VerificadorTabelacar()
    ativo = 'ENMTA4'
    fundo_dist_regua = {
        'fundo': ['RFA', 'APO', 'ID2'],
        'percentual_alocacao': [sum([0.4753, 0.2623, 0.3275]),
                sum([0.1017, 0.3478, 0.1845]),
                sum([0.4230, 0.3899, 0.4879])]
    }

    df = pd.DataFrame(fundo_dist_regua)
    resultado_df = verificador.verifica_alocacao(df,ativo)
    display(resultado_df)