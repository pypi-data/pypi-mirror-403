import asyncio
import aio_pika
import json

class RabbitMQConsumer:
    def __init__(
        self,
        *,
        host: str,
        queue: str,
        username: str,
        password: str,
        vhost: str = "/",
        prefetch_count: int = 1
    ):
        self.host = host
        self.queue = queue
        self.username = username
        self.password = password
        self.vhost = vhost
        self.connection = None
        self.channel = None
        self.prefetch_count = prefetch_count

    async def connect(self):
        self.connection = await aio_pika.connect_robust(
            host=self.host,
            login=self.username,
            password=self.password,
            virtualhost=self.vhost,
            heartbeat=600,
        )
        self.channel = await self.connection.channel()
        await self.channel.set_qos(prefetch_count=self.prefetch_count)
        await self.channel.declare_queue(self.queue, durable=True)

    async def start_consuming(self, callback):
        while True:
            try:
                if not self.channel:
                    raise RuntimeError("❌ Canal RabbitMQ não conectado. Chame connect() antes.")

                queue = await self.channel.get_queue(self.queue)
                

                async def on_message(message):
                    async with message.process():
                        try:
                            mensagem = json.loads(message.body.decode())
                            resultado = await callback(mensagem)

                            if resultado is False:
                                await message.nack(requeue=False)
                            else:
                                await message.ack()
                                
                        except Exception as e:
                            print(f"❌ Erro ao processar mensagem: {e}")
                            await message.nack(requeue=False)

                await queue.consume(on_message, no_ack=False)  # registra callback

                print(f'[*] Aguardando mensagens na fila "{self.queue}". Para sair pressione CTRL+C')

                await asyncio.Future()
            except Exception as e:
                print(f"🔄 Consumer caiu, reconectando... {e}")
                await asyncio.sleep(5)

    async def close(self):
        if self.channel and not self.channel.is_closed:
            await self.channel.close()

        if self.connection and not self.connection.is_closed:
            await self.connection.close()
