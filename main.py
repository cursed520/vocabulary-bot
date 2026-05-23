import discord
from discord.ext import commands
from database import init_db, add_word, get_random_word, update_score, get_stats, get_leaderboard, create_translation_quiz

TOKEN = "Token"  # Замени на реальный токен (не публикуй на GitHub!)
PREFIX = "prefix"

intents = discord.Intents.all()
bot = commands.Bot(command_prefix=PREFIX, intents=intents)

@bot.event
async def on_ready():
    print(f'Бот {bot.user} запущен!')
    try:
        await init_db()
        print("✅ База данных успешно подключена и готова к работе!")
    except Exception as e:
        print(f"❌ Ошибка при подключении к базе данных: {e}")

@bot.command(name="word_ru")
async def word_ru(ctx, word_ru: str, word_en: str):
    user_id = ctx.author.id
    await add_word(user_id, word_ru, word_en)
    await ctx.send(f'Слово "{word_ru}" → "{word_en}" успешно добавлено!')

@bot.command(name="stats")
async def stats(ctx):
    user_id = ctx.author.id
    score, words_count = await get_stats(user_id)  # ← исправлено
    await ctx.send(f'📊 Твоя статистика:\n🏆 Очков: {score}\n📚 Слов в словаре: {words_count}')

@bot.command(name="top")
async def leaderboard(ctx):
    users = await get_leaderboard()
    if not users:
        await ctx.send('Пока нет пользователей с очками!')
        return

    message = "🏆 **Топ пользователей**\n"
    for i, user in enumerate(users, 1):
        try:
            member = await ctx.guild.fetch_member(user.id)
            name = member.display_name
        except:
            name = f"User_{user.id}"
        message += f"{i}. {name} — {user.score} очков\n"

    await ctx.send(message)

@bot.command(name="quiz")
async def quiz(ctx):
    quiz_data = await create_translation_quiz(ctx.author.id)
    if quiz_data is None:
        await ctx.send("❌ У тебя пока нет слов в словаре. Добавь через `!word_ru`")
        return
    await ctx.send(quiz_data['question'], view=quiz_data['view'])

bot.run(TOKEN)