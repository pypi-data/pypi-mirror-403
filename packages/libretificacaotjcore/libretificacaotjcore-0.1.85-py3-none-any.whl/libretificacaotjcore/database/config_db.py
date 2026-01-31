import motor.motor_asyncio
import certifi

class ConfigDb:
    def __init__(self, host: str, user: str, password: str, port: int, db_name: str):
        self.host = host
        self.user = user
        self.password = password
        self.port = port
        self.db_name = db_name
        
        auth = f"{self.user}:{self.password}@" if self.user and self.password else ""
        # self.client = motor.motor_asyncio.AsyncIOMotorClient(
        #     f"mongodb+srv://{auth}{self.host}",
        #     tls=True,
        #     tlsCAFile=certifi.where(),
        #     tlsAllowInvalidCertificates=False,
        #     serverSelectionTimeoutMS=30000,
        #     socketTimeoutMS=20000,
        #     connectTimeoutMS=20000,
        #     retryWrites=True,
        #     w='majority'
        # )

        self.client = motor.motor_asyncio.AsyncIOMotorClient(
            f"mongodb://{auth}{self.host}:{self.port}/"
        )
        self.__db = self.client[self.db_name]
        self.db_initialized = False
        
        
    async def criar_schema(self):
        global _db_initialized
        if not self.db_initialized:
            if "arquivos" not in (await self.__db.list_collection_names()):
                await self.__db.create_collection("arquivos")
            
            await self.__db.arquivos.create_index([("cnpj", 1)])
            await self.__db.arquivos.create_index(
                [("cnpj", 1), ("cpf", 1)], 
                unique=True,
                partialFilterExpression={
                    "cnpj": {"$exists": True},
                    "cpf": {"$exists": True}
                })
            self.db_initialized = True

            if "rubricas" not in (await self.__db.list_collection_names()):
                await self.__db.create_collection("rubricas")
                
            await self.__db.rubricas.create_index([("cnpj", 1)])
            await self.__db.rubricas.create_index([("solicitacaoId", 1)], unique=True)
            await self.__db.rubricas.create_index([("id", 1)], unique=True)
            self.db_initialized = True
            
            if "solicitacao_xmls" not in (await self.__db.list_collection_names()):
                await self.__db.create_collection("solicitacao_xmls")

            await self.__db.solicitacao_xmls.create_index([("solicitacaoId", 1)], unique=True)
            self.db_initialized = True
            
            if "dependente_invalido_1210" not in (await self.__db.list_collection_names()):
                await self.__db.create_collection("dependente_invalido_1210")

            await self.__db.dependente_invalido_1210.create_index([("solicitacaoId", 1)])
            self.db_initialized = True
            
    async def get_db(self):
        await self.criar_schema()
        return self.__db