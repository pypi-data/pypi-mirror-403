import uuid

class DepententeInvalido1210Repository:
    def __init__(self, db):
        self.__db = db

    async def inserir(self, depentente_invalido: dict) -> bool:
        
        try:
            dep_ja_cadastrado = await self.__db.dependente_invalido_1210.find_one({"solicitacaoId": depentente_invalido["solicitacaoId"], "cpf": depentente_invalido["cpf"], "cpf_dep": depentente_invalido["cpf_dep"], "per_apur": depentente_invalido["per_apur"]})
            if dep_ja_cadastrado:
                print(f"⚠️ Dependente inválido 1210 já cadastrado: {dep_ja_cadastrado}")
                return False

            await self.__db.dependente_invalido_1210.insert_one(depentente_invalido)
            return True
        except Exception as e:
            print(f"❌ Erro ao inserir o dependente inválido 1210: {e}")
            return False
        
    async def buscar_por_solicitacao_id(self, solicitacaoId: int) -> list:
        try:
            return await self.__db.dependente_invalido_1210.find({"solicitacaoId": solicitacaoId}, {"_id": 0}).to_list(length=None)
        except Exception as e:
            print(f"❌ Erro ao buscar dependente inválido 1210 por solicitacaoId: {e}")
            return []
    
    async def remover(self, solicitacaoId: int, cpf_colaborador: str) -> bool:
        try:
            await self.__db.dependente_invalido_1210.delete_many({"solicitacaoId": solicitacaoId, "cpf": cpf_colaborador})
            return True
        except Exception as e:
            print(f"❌ Erro ao remover dependente inválido 1210: {e}")
            return False
