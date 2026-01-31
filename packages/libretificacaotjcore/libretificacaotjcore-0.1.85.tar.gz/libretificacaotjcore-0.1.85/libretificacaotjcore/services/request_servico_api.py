import httpx


class RequestServicoApi:
    def __init__(self, url, token):
        self.url = url
        self.token = token
        self.client = httpx.AsyncClient(timeout=1200, verify=False)
        self.status_code_success = [200, 201, 202, 203, 204]

    async def post(self, *, data: dict | list):
        print(self.token)
        response = await self.client.post(self.url, json=data)

        if response.status_code not in self.status_code_success:
            raise Exception(f"Erro ao fazer request ao servico de API: {response.status_code}")
        
        await self.close()

    async def get(self):
        response = await self.client.get(self.url)

        if response.status_code not in self.status_code_success and response.status_code != 404:
            raise Exception(f"Erro ao fazer request ao servico de API: {response.status_code}")

        await self.close()
        return response.json()

    async def delete(self):
        response = await self.client.delete(self.url)

        if response.status_code not in self.status_code_success:
            raise Exception(f"Erro ao fazer request ao servico de API: {response.status_code}")

        await self.close()
        return response.json()

    async def close(self):
        await self.client.aclose()