import aio_pika
import asyncio
import logging

from aiogram import Router
from aiogram.filters.command import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from ..statesgroup import MenuStatesGroup, ChangeStatesGroup
from ..markups.reply import timeframes_kb, skip_kb
from ..markups.inline import menu_kb
from ..config import bot, Config


router = Router()

@router.message(Command('start'))
async def start(message: Message, state: FSMContext):
    print('You in start')
    curr = await state.get_state()
    if (curr in MenuStatesGroup) or (curr in ChangeStatesGroup):
        pass
    else:
        logging.basicConfig(level=logging.INFO, filename="py_log_bot.log",filemode="w",
                    format="%(asctime)s %(levelname)s %(message)s")
        try:
            task = asyncio.create_task(rabbit_connection_screener())
        except Exception as e:
            logging.error(e)
        await message.answer(text='Приветствую в боте для отслеживания открытого интереса. Для продолжения работы вам необходимо ввести процент отслеживания и время для отслеживания', reply_markup=skip_kb)
        await message.answer(text='Для начала введите процент отслеживания по периоду роста. (Положительное число большее 1) или нажмите пропустить снизу', reply_markup=skip_kb)
        await state.set_state(MenuStatesGroup.percent_long)
        
@router.message(MenuStatesGroup.percent_long)        
async def get_percent(message: Message, state: FSMContext):
    if message.text == 'Пропустить':
        await state.update_data({'percent_long': '0', 'timeframe_long': '0'})
        await message.answer('Введите проценты по периоду просадки. (Отрицательное число меньшее или равное -1) или нажмите пропустить снизу', reply_markup=skip_kb)
        await state.set_state(MenuStatesGroup.percent_short)
    else:
        try:
            if float(message.text) < 1:
                raise Exception('Unsupported number')
            await state.update_data({'percent_long': message.text})
            await message.answer(f'Процент роста сохранен, далее введите время. (Положительное число большее или равное 10)')
            await state.set_state(MenuStatesGroup.timeframe_long)
        except Exception:
            await message.answer('Введите число большее или равное 1!')
        
@router.message(MenuStatesGroup.timeframe_long)
async def get_timeframe(message: Message, state: FSMContext):
    try:
        if float(message.text) < 10:
            raise Exception('Unsupported number')
        await state.update_data({'timeframe_long': message.text})
        await message.answer(f'Время сохранено, введите данные для просадки')
        await message.answer('Процент роста и время сохранены, далее введите проценты по периоду просадки. (Отрицательное число меньшее или равное -1) или нажмите пропустить снизу', reply_markup=skip_kb)
        await state.set_state(MenuStatesGroup.percent_short)
    except:
        await message.answer('Введите число большее или равное 10!')
             
@router.message(MenuStatesGroup.percent_short)        
async def get_percent(message: Message, state: FSMContext):
    if message.text == 'Пропустить':
        await state.update_data({'percent_short': '0', 'timeframe_short': '0'})
        await state.set_state(MenuStatesGroup.menu)
        await message.answer('Меню\n\n🛠Измененить время - изменить время, по которому сканирует бот\n🛠Изменить процент - изменить процент, по которому сканирует бот\n▶️Начать сканирование - активация бота и сигналов', reply_markup=menu_kb)
    else:
        try:
            if float(message.text) > -1:
                raise Exception('Unsupported number')
            await state.update_data({'percent_short': message.text})
            await message.answer(f'Процент просадки сохранен, далее введите время.(Положительное число большее или равное 10)')
            await state.set_state(MenuStatesGroup.timeframe_short)
        except Exception:
            await message.answer('Введите число меньшее или равное -1!')
    
@router.message(MenuStatesGroup.timeframe_short)
async def get_timeframe(message: Message, state: FSMContext):
    try:
        if float(message.text) < 10:
            raise Exception('Unsupported number')
        await state.update_data({'timeframe_short': message.text})
        await message.answer(f'Время сохранено и проценты просадки сохранены, перенаправление в меню...')
        await message.answer('Меню\n\n🛠Измененить время - изменить время, по которому сканирует бот\n🛠Изменить процент - изменить процент, по которому сканирует бот\n▶️Начать сканирование - активация бота и сигналов', reply_markup=menu_kb)
        await state.set_state(MenuStatesGroup.menu)
    except:
        await message.answer('Введите число большее или равное 10!')
    
@router.callback_query(MenuStatesGroup.menu)    
async def change_options(callback_query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    logging.info(f'{data}')
    if callback_query.data == 'change_long':
        if data.get('scan'):
            await callback_query.answer(text='Сначала остановите сканирование')
        else:
            await bot.send_message(chat_id=callback_query.from_user.id, text='Введите процент отслеживания по периоду роста. (Положительное число большее 1) или 0, если хотите выключить сканирование роста')
            await state.set_state(ChangeStatesGroup.change_long)
    elif callback_query.data == 'change_short':
        if data.get('scan'):
            await callback_query.answer(text='Сначала остановите сканирование')
        else:
            await bot.send_message(chat_id=callback_query.from_user.id, text='Введите процент отслеживания по периоду просадки. (Отрицательно число меньшее или равное -1) или 0, если хотите выключить сканирование просадки')
            await state.set_state(ChangeStatesGroup.change_short)
    elif callback_query.data == 'start_scan':
        if (data.get('long') or data.get('short')):
            await bot.send_message(chat_id=callback_query.from_user.id, text='Сканирование уже началось')
        else:
            if (float(data['percent_long']) > 0) and (float(data['percent_short']) < 0):
                await state.update_data({'long': True, 'short': True})
                await bot.send_message(chat_id=callback_query.from_user.id, text=f"✅ Сканирование роста началось, ожидайте сигналов\n 🕘Время: {data['timeframe_long']}m\n 📈Процет: {data['percent_long']}%")
                await bot.send_message(chat_id=callback_query.from_user.id, text=f"✅ Сканирование просадки началось, ожидайте сигналов\n 🕘Время: {data['timeframe_short']}m\n 📉Процет: {data['percent_short']}%")
                await asyncio.gather(
                    publisher_scneener(data=f"{data['timeframe_long']},{data['percent_long']} start", routing='tgbybit_long'), 
                    publisher_scneener(data=f"{data['timeframe_short']},{data['percent_short']} start", routing='tgbybit_short')
                    )
            elif float(data['percent_long']) > 0:
                await state.update_data({'long': True, 'short': False})
                await publisher_scneener(data=f"{data['timeframe_long']},{data['percent_long']} start", routing='tgbybit_long')
                await bot.send_message(chat_id=callback_query.from_user.id, text=f"✅ Сканирование роста началось, ожидайте сигналов\n🕘 Время: {data['timeframe_long']}m\n 📈Процет: {data['percent_long']}%")
            elif float(data['percent_short']) < 0:
                await state.update_data({'long': False, 'short': True})
                await publisher_scneener(data=f"{data['timeframe_short']},{data['percent_short']} start", routing='tgbybit_short')
                await bot.send_message(chat_id=callback_query.from_user.id, text=f"✅ Сканирование просадки началось, ожидайте сигналов\n 🕘Время: {data['timeframe_short']}m\n 📉Процет: {data['percent_short']}%")
            else:
                await bot.send_message(chat_id=callback_query.from_user.id, text='🛠Задайте проценты для просадки или роста')
    elif callback_query.data == 'stop_scan':
        # print(data)
        if (data.get('long') and data.get('short')):
            await state.update_data({'short': False, 'long': False})
            logging.info('Before stopping')
            await publisher_scneener(data=f'0,0 stop', routing='tgbybit_long')
            await publisher_scneener(data=f'0,0 stop', routing='tgbybit_short')
            logging.info('After stopping')
            await bot.send_message(chat_id=callback_query.from_user.id, text='❌ Сканирование просадки и роста остановлено')
        elif data.get('long'):
            logging.info('Stop only long')
            await state.update_data({'long': False})
            await publisher_scneener(data=f'0,0 stop', routing='tgbybit_long')
            await bot.send_message(chat_id=callback_query.from_user.id, text='❌ Сканирование роста остановлено')
        elif data.get('short'):
            logging.info('Stop only short ')
            await state.update_data({'short': False})
            await publisher_scneener(data=f'0,0 stop', routing='tgbybit_short')
            await bot.send_message(chat_id=callback_query.from_user.id, text='❌ Сканирование просадки остановлено')
        else:
            await bot.send_message(chat_id=callback_query.from_user.id, text=f'😳 Сканирование не активировано')
    elif callback_query.data == 'options':
        logging.info(data.get('percent_short'))
        if (data.get('percent_short') is not None) and (data.get('percent_short') != '0'):
            short = '✅'
            time_short = data.get('timeframe_short')
            percent_short = data.get('percent_short')
        else:
            short = '❌'
            time_short = '❌'
            percent_short = '❌'
        logging.info(data.get('percent_long'))
        if (data.get('percent_long') is not None) and (data.get('percent_long') != '0'):
            long = '✅'
            time_long = data.get('timeframe_long')
            percent_long = data.get('percent_long')
        else:
            long = '❌'
            time_long = '❌'
            percent_long = '❌'
        await bot.edit_message_text(chat_id=callback_query.from_user.id,
                                    message_id=callback_query.message.message_id,
                                    text=f'Меню\n\n🛠Измененить время - изменить время, по которому сканирует бот\n🛠Изменить процент - изменить процент, по которому сканирует бот\n▶️Начать сканирование - активация бота и сигналов\n\nТекущие настройки\nПросадка:{short}\nВремя: {time_short}\nПроцент: {percent_short}\n\nРост: {long}\nВремя: {time_long}\nПроцент: {percent_long}', 
                                    reply_markup=menu_kb)
    
@router.message(ChangeStatesGroup.change_long)
async def change_percent(message: Message, state: FSMContext):
    try:
        if (float(message.text) < 1) and (float(message.text) != 0):
            raise Exception('Unsupported number')
        await state.update_data({'percent_long': message.text})
        if float(message.text) == 0:
            await message.answer(f'Сканирование роста выключно, перенаправление в меню...')
            await state.set_state(MenuStatesGroup.menu)
            await message.answer('Меню\n\n🛠Измененить время - изменить время, по которому сканирует бот\n🛠Изменить процент - изменить процент, по которому сканирует бот\n▶️Начать сканирование - активация бота и сигналов', reply_markup=menu_kb)
        else:
            await message.answer(f'Процент роста сохранен, далее введите время. (Положительное число большее или равное 10)')
            await state.set_state(ChangeStatesGroup.change_time_long)
    except Exception:
        await message.answer('Введите число большее или равное 1!')
        
@router.message(ChangeStatesGroup.change_short)
async def change_percent(message: Message, state: FSMContext):
    try:
        if (float(message.text) > -1) and (float(message.text) != 0):
            raise Exception('Unsupported number')
        await state.update_data({'percent_short': message.text})
        if float(message.text) == 0:
            await message.answer(f'Сканирование просадки выключно, перенаправление в меню...')
            await state.set_state(MenuStatesGroup.menu)
            await message.answer('Меню\n\n🛠Измененить время - изменить время, по которому сканирует бот\n🛠Изменить процент - изменить процент, по которому сканирует бот\n▶️Начать сканирование - активация бота и сигналов', reply_markup=menu_kb)
        else:
            await message.answer(f'Процент просадки сохранен, далее введите время. (Положительное число большее или равное 10)')
            await state.set_state(ChangeStatesGroup.change_time_short)
    except Exception:
        await message.answer('Введите число меньшее или равное -1!')
        
@router.message(ChangeStatesGroup.change_time_long)
async def get_timeframe(message: Message, state: FSMContext):
    try:
        if float(message.text) < 10:
            raise Exception('Unsupported number')
        await state.update_data({'timeframe_long': message.text})
        await state.set_state(MenuStatesGroup.menu)
        data = await state.get_data()
        # print(data)
        await message.answer('Меню\n\n🛠Измененить время - изменить время, по которому сканирует бот\n🛠Изменить процент - изменить процент, по которому сканирует бот\n▶️Начать сканирование - активация бота и сигналов', reply_markup=menu_kb)
    except:
        await message.answer('Введите число большее или равное 10!')
        
@router.message(ChangeStatesGroup.change_time_short)
async def get_timeframe(message: Message, state: FSMContext):
    try:
        if float(message.text) < 10:
            raise Exception('Unsupported number')
        await state.update_data({'timeframe_short': message.text})
        await message.answer(f'Время сохранено, введите данные для просадки')
        await state.set_state(MenuStatesGroup.menu)
        data = await state.get_data()
        # print(data)
        await message.answer('Меню\n\n🛠Измененить время - изменить время, по которому сканирует бот\n🛠Изменить процент - изменить процент, по которому сканирует бот\n▶️Начать сканирование - активация бота и сигналов', reply_markup=menu_kb)
    except:
        await message.answer('Введите число большее или равное 10!')
    
    
    
async def publisher_scneener(data: str, routing: str):
    connection = await aio_pika.connect_robust(f"amqp://{Config.rmuser}:{Config.rmpassword}@{Config.hostname}:5672/")
    if routing == 'tgbybit_short':
        logging.info('message to short is sending')
    if routing == 'tgbybit_long':
        logging.info('message to long is sending')
    channel = await connection.channel()
    await channel.default_exchange.publish(
        aio_pika.Message(body=data.encode()),
        routing_key=routing
    )
    await connection.close()
    
async def rabbit_connection_screener():
    logging.info('Connection is set')
    async def callback(message: aio_pika.IncomingMessage):
        async with message.process():
            name, timeframe, delta_percent, delta_price, count_signal = message.body.decode().split() # message format is "{name} {timeframe} {delta_percent} {delta_price} {count_signal}"
            if int(count_signal) <= 4:
                try:
                    if round(float(delta_percent), 2) < 0:
                        await bot.send_message(chat_id=Config.chat_id, text=f'🪙Сигнал по {name}--{timeframe}m\n📉Процет OI: {round(float(delta_percent), 2)}%\n💲Изменение цены: {round(float(delta_price), 2)}%\nCигнал по счету {count_signal}')
                    else:
                        await bot.send_message(chat_id=Config.chat_id, text=f'🪙Сигнал по {name}--{timeframe}m\n📈Процет OI: {round(float(delta_percent), 2)}%\n💲Изменение цены: {round(float(delta_price), 2)}%\nCигнал по счету {count_signal}')
                except:
                    await asyncio.sleep(5)
                    if round(float(delta_percent), 2) < 0:
                        await bot.send_message(chat_id=Config.chat_id, text=f'🪙Сигнал по {name}--{timeframe}m\n📉Процет OI: {round(float(delta_percent), 2)}%\n💲Изменение цены: {round(float(delta_price), 2)}%\nCигнал по счету {count_signal}')
                    else:
                        await bot.send_message(chat_id=Config.chat_id, text=f'🪙Сигнал по {name}--{timeframe}m\n📈Процет OI: {round(float(delta_percent), 2)}%\n💲Изменение цены: {round(float(delta_price), 2)}%\nCигнал по счету {count_signal}')
    
    connection = await aio_pika.connect_robust(f'amqp://{Config.rmuser}:{Config.rmpassword}@{Config.hostname}:5672/')
    async with connection:
        channel = await connection.channel()
        queue = await channel.declare_queue(name='bybittg')
        await queue.consume(callback=callback)
        try:
            await asyncio.Future()
        finally:
            logging.info('Connection was closed')
            await connection.close()
        
        