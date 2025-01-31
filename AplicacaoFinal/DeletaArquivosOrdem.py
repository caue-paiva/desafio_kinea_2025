from pathlib import Path

class DeletaArquivosOrdem:

    PATH_VOLUME = Path("/Volumes/desafio_kinea/boletagem_cp/files")

    def __deletar_arquivos(self,diretorio:Path)->bool:
        path = self.PATH_VOLUME / diretorio
        try: 
            for file in path.iterdir():
                if file.suffix == ".csv":
                    file.unlink() 
        except Exception as e:
                print(f"falha ao deletar arquivos CSV do diretório: {diretorio}: {e}")
                return False
        
        return True

    

    def deleta_arquivos_ordem(self,dados_ordem = True, regua_inicial = True, regua_otimizada = True)->bool:
        sucesso_delecao = True
        if dados_ordem:
            sucesso_delecao = sucesso_delecao and self.__deletar_arquivos("Ordem")
        if regua_inicial:
            sucesso_delecao = sucesso_delecao and self.__deletar_arquivos("Reguas")
        if regua_otimizada:
            sucesso_delecao = sucesso_delecao and self.__deletar_arquivos("ReguasOtimizadas")

        return sucesso_delecao
    

if __name__ == "__main__":
    pass
    """
    Cuidado ao testar o código, pq pode deletar todos os arquivos e ai teria que criar uma ordem nova para os testes
    """
    #deleta = DeletaArquivosOrdem()
    #print(deleta.deleta_arquivos_ordem(False,False,False))