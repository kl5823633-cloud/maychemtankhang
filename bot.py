# bot.py
import discord
from discord.ext import commands, tasks
import os
from dotenv import load_dotenv
import json
import asyncio
import logging

# Cấu hình logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Cấu hình bot
TOKEN = os.getenv('DISCORD_TOKEN')
PREFIX = os.getenv('PREFIX', '!')
ADMIN_ID = os.getenv('ADMIN_ID', '')

# Kiểm tra token
if not TOKEN:
    logger.error("Không tìm thấy DISCORD_TOKEN trong .env")
    exit(1)

# Khởi tạo bot với intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix=PREFIX, intents=intents)

# Sự kiện khi bot ready
@bot.event
async def on_ready():
    logger.info(f'✅ Bot đã đăng nhập với tên: {bot.user.name}')
    logger.info(f'🆔 Bot ID: {bot.user.id}')
    logger.info(f'📊 Số server: {len(bot.guilds)}')
    
    # Set status
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name=f"{len(bot.guilds)} servers | {PREFIX}help"
        )
    )
    
    # Bắt đầu background tasks
    update_status.start()

# Background task: Update status mỗi 5 phút
@tasks.loop(minutes=5)
async def update_status():
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name=f"{len(bot.guilds)} servers | {PREFIX}help"
        )
    )

# Command cơ bản
@bot.command(name='ping', help='Kiểm tra độ trễ')
async def ping(ctx):
    latency = round(bot.latency * 1000)
    await ctx.send(f'🏓 Pong! {latency}ms')

@bot.command(name='hello', help='Chào hỏi')
async def hello(ctx):
    await ctx.send(f'👋 Xin chào {ctx.author.mention}!')

@bot.command(name='info', help='Thông tin bot')
async def info(ctx):
    embed = discord.Embed(
        title="🤖 Thông tin Bot",
        color=discord.Color.blue(),
        timestamp=ctx.message.created_at
    )
    
    embed.add_field(name="Tên bot", value=bot.user.name, inline=True)
    embed.add_field(name="ID", value=bot.user.id, inline=True)
    embed.add_field(name="Ping", value=f"{round(bot.latency * 1000)}ms", inline=True)
    embed.add_field(name="Prefix", value=PREFIX, inline=True)
    embed.add_field(name="Server", value=len(bot.guilds), inline=True)
    embed.add_field(name="Uptime", value="Online", inline=True)
    
    embed.set_footer(text=f"Yêu cầu bởi {ctx.author.name}")
    
    await ctx.send(embed=embed)

# Command admin only
@bot.command(name='clear', help='Xóa tin nhắn (admin only)')
@commands.has_permissions(administrator=True)
async def clear(ctx, amount: int = 5):
    if amount > 100:
        amount = 100
    deleted = await ctx.channel.purge(limit=amount + 1)
    await ctx.send(f'✅ Đã xóa {len(deleted)-1} tin nhắn!', delete_after=3)

# Command lỗi handler
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send(f"❌ Command không tồn tại! Gõ `{PREFIX}help` để xem danh sách commands.")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ Bạn không có quyền sử dụng command này!")
    else:
        logger.error(f"Command error: {error}")
        await ctx.send("❌ Có lỗi xảy ra khi thực thi command!")

# Chạy bot
if __name__ == "__main__":
    logger.info("🚀 Đang khởi động bot...")
    try:
        bot.run(TOKEN)
    except discord.LoginFailure:
        logger.error("Token Discord không hợp lệ!")
    except Exception as e:
        logger.error(f"Lỗi khi chạy bot: {e}")
