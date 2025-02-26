import pandas as pd
ordem = pd.read_csv("/Volumes/desafio_kinea/boletagem_cp/files/Ordem/Ordem.csv",sep='\t')
def JuntarReguas():
    ordem = pd.read_csv("/Volumes/desafio_kinea/boletagem_cp/files/Ordem/Ordem.csv",sep='\t')
    ordem['qtde'] = ordem['qtde'].str.replace(',', '').astype(float)
    input_nexxus = pd.DataFrame()
    for i in dbutils.fs.ls("/Volumes/desafio_kinea/boletagem_cp/files/Reguas/"):
        ativo:str = i.name.split("_")[1].removesuffix(".csv")    
        ativo_na_ordem = ordem[ordem['ticker'] == ativo]
        qtde_ativo = ativo_na_ordem['qtde'].values[0]
        preco_ativo = ativo_na_ordem['preco'].values[0]
        valor_ativo = ativo_na_ordem['qtde'].values[0] * ativo_na_ordem['preco'].values[0]
        
        df = pd.read_csv(f"/Volumes/desafio_kinea/boletagem_cp/files/Reguas/{i.name}", sep=",", encoding="utf-8")
        qtdes = round((valor_ativo *df['percentual_alocacao'])/preco_ativo)
        if qtde_ativo < qtdes.sum():
            idx_maior = qtdes.argmax()
            qtdes[idx_maior] -=  qtdes.sum() - qtde_ativo
        if qtde_ativo > qtdes.sum():
            idx_maior = qtdes.argmax()
            qtdes[idx_maior] +=  qtde_ativo - qtdes.sum()

        df['ATIVO'] = ativo
        df['QTDE'] = qtdes
        df['PU'] = preco_ativo
        df['VALOR'] = df['QTDE'] * df['PU']
        df = df.drop(columns='percentual_alocacao').rename(columns={"fundo":"FUNDO"})
        input_nexxus = pd.concat([input_nexxus, df])
    input_nexxus.to_csv("/Volumes/desafio_kinea/boletagem_cp/files/InputNexxus/input_nexxus.csv")
if __name__ == '__main__':
    JuntarReguas()