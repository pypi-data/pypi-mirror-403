
from pymongo.errors import BulkWriteError

class ArquivoRepository:
    def __init__(self, db):
        self.__db = db

    async def inserir_arquivo(self, arquivo: dict) -> bool:
        try:
            arquivo_no_db = await self.__db.arquivos.find_one(
                {"cnpj": arquivo["cnpj"], "cpf": arquivo["cpf"]}
            )

            if arquivo_no_db is None:
                await self.__db.arquivos.insert_one(arquivo)
                return True

            await self.__db.arquivos.delete_one(
                {"cnpj": arquivo["cnpj"], "cpf": arquivo["cpf"]}
            )
            await self.__db.arquivos.insert_one(arquivo)
            return True
        except Exception as e:
            print(f"❌ Erro ao inserir o arquivo: {e}")
            return False
        
    async def inserir_arquivos_em_lote(self, arquivos: list[dict]) -> bool:
        try:
            if not arquivos:
                return False

            # Agora usar apenas cnpj e cpf para deletar
            filtros = [{"cnpj": a["cnpj"], "cpf": a["cpf"]} for a in arquivos]
            await self.__db.arquivos.delete_many({"$or": filtros})

            await self.__db.arquivos.insert_many(arquivos)
            return True
        except BulkWriteError as bwe:
            print(f"❌ Erro de escrita em lote: {bwe.details}")
            return False
        except Exception as e:
            print(f"❌ Erro ao inserir arquivos em lote: {e}")
            return False

    async def remover_arquivo(self, cnpj: str) -> bool:
        try:
            await self.__db.arquivos.delete_many({"cnpj": cnpj})
            return True
        except Exception as e:
            print(f"❌ Erro ao remover o arquivo: {e}")
            return False

    async def buscar_por_cnpj(self, cnpj: str) -> list[dict]:
        try:
            return await self.__db.arquivos.find({"cnpj": cnpj}, {"_id": 0}).to_list(length=None)
        except Exception as e:
            print(f"❌ Erro ao buscar por cnpj: {e}")
            return []