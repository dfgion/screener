import os

from fastapi import FastAPI, Request

from contextlib import asynccontextmanager

from aiogram.types import Update

from bot.config import bot, dp, set_commands
from bot.handlers import basic

WEBHOOK_URL = f"{os.getenv('WEBHOOK_PATH')}/bot"

@asynccontextmanager
async def lifespan(_):
    webhook_info = await bot.get_webhook_info()
    if webhook_info != WEBHOOK_URL:
        await bot.set_webhook(
            drop_pending_updates=True,
            allowed_updates=dp.resolve_used_update_types(),
            url=WEBHOOK_URL
        )
        await set_commands(bot)
        dp.include_routers(basic.router)
    yield
    await bot.session.close()

app = FastAPI(lifespan=lifespan)


@app.post(path='/bot')
async def bot_webhook(request: Request):
    res = await request.json()
    print(res)
    telegram_update = Update.model_validate(await request.json(), context={"bot": bot})
    await dp.feed_update(bot=bot, update=telegram_update)