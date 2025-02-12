import pandas as pd

def JuntarReguas():
    input_nexxus = pd.DataFrame()
    for i in dbutils.fs.ls("/Volumes/desafio_kinea/boletagem_cp/files/Reguas/"):
        ativo:str = i.name.split("_")[1].removesuffix(".csv")
        df = pd.read_csv(f"/Volumes/desafio_kinea/boletagem_cp/files/Reguas/{i.name}", sep=",", encoding="utf-8")
        df['ativo'] = ativo
        input_nexxus = pd.concat([input_nexxus, df])
    input_nexxus.to_csv("/Volumes/desafio_kinea/boletagem_cp/files/InputNexxus/input_nexxus.csv")
if __name__ == '__main__':
    JuntarReguas()