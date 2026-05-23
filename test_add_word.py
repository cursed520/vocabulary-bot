import asyncio
from database import add_word

async def main():
    await add_word(12345, "кошка", "cat")
    await add_word(12345, "собака", "dog")
    print("Слова добавлены. Проверьте базу данных.")

if __name__ == "__main__":
    asyncio.run(main())


