# Rakel Python SDK 🐍🍡

Uma biblioteca de WhatsApp infinitamente superior para desenvolvedores Python.

## Instalação

```bash
pip install rakel-api
```

## Como usar

```python
from rakel import RakelClient, MochiFlow
import asyncio

async def main():
    client = RakelClient()

    # Define um fluxo de conversa
    pizza_flow = MochiFlow("pizza") \
        .start("greeting", "Olá! Qual seu nome?") \
        .ask("name", next_step="sabor") \
        .ask("sabor", "Prazer {name}! Qual sabor você quer?") \
        .end("end", "Pedido de {sabor} anotado!")

    @client.on("message")
    async def handle_message(msg):
        print(f"Mensagem de {msg['from']}: {msg['text']}")

    await client.connect()
    
    # Mantém o loop rodando
    while True:
        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())
```

## Paradigma MochiMochi
Este SDK segue o paradigma **MochiMochi**, focado em minimalismo afetivo e código limpo.

- **Fácil**: API intuitiva e direta.
- **Rápido**: Baseado em `asyncio`.
- **Estético**: Estrutura organizada e logs bonitos com `loguru`.

## Licença
MIT
