import os
import pathlib
import aio_pika

from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand, BotCommandScopeDefault
import logging

class Config:
    rmuser = os.getenv('RMUSER')
    rmpassword = os.getenv('RMPASSWORD')
    chat_id = int(os.getenv('CHAT_ID'))
    bot_token = os.getenv('TOKEN')
    hostname = os.getenv('HOSTNAME')

dp = Dispatcher()

bot = Bot(token=Config.bot_token)

async def set_commands(bot: Bot):
    commands = [
        BotCommand(
            command='/start',
            description='Start'
        )
    ]
    await bot.set_my_commands(commands, BotCommandScopeDefault())