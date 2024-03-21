import json

import websockets

import asyncio

import time

import ast

import aio_pika
import logging

import os
from tickers import tickers

class Screener:
    def __init__(self, mq_user, mq_password, hostname) -> None:
        self.stop_event = None
        self.mq_user = mq_user
        self.mq_password = mq_password
        self.hostname = hostname
        
    async def _callback(self, message: aio_pika.IncomingMessage):
        async with message.process():
            logging.info('message in short')
            payload, message = message.body.decode().split(' ') # message format is "{timeframe},{percent} {option}"
            logging.info(f'message short {message}')
            payload = payload.split(',')
            if message == 'start':
                self.stop_event = asyncio.Event()
                task = asyncio.create_task(self.websocket_connection(event=self.stop_event, payload=payload), name='bybit_connection')
            elif message == 'stop':
                self.stop_event.set()

    async def rabbit_connection_tg(self):
        connection = await aio_pika.connect_robust(f'amqp://{self.mq_user}:{self.mq_password}@{self.hostname}:5672/')
        logging.info('Connected')
        async with connection:
            channel = await connection.channel()
            queue = await channel.declare_queue(name='tgbybit_short')
            await queue.consume(callback=self._callback)
            try:
                await asyncio.Future()
            finally:
                await connection.close()
            
    async def rabbit_send_to_telegram(self, data: str):
        connection = await aio_pika.connect_robust(f"amqp://{self.mq_user}:{self.mq_password}@{self.hostname}:5672/")
        channel = await connection.channel()
        logging.info('sending to tg')
    
        await channel.default_exchange.publish(
            aio_pika.Message(body=data.encode()),
            routing_key='bybittg'
        )

        await connection.close()
            
    async def websocket_connection(self, event: asyncio.Event, payload: list):
        websocket_data = {}
        timeframe, percent = payload # 5 5
        start_expiration = time.time() + float(timeframe)*60 # minutes to seconds 492429492 + 300
        async with websockets.connect('wss://stream.bybit.com/v5/public/linear') as websocket:
            await websocket.send(json.dumps({
                                            "op": "subscribe",
                                            "args": tickers
                                            }))
            while not event.is_set():
                message = await websocket.recv()
                try:
                    message = ast.literal_eval(message)
                    current_time = time.time()
                    name = message['data']['symbol']
                except:
                    logging.info(message)
                    continue
                if message.get('type') == 'delta':
                    current_oi = message['data'].get('openInterestValue')
                    current_price = message['data'].get('lastPrice')
                    if current_price:
                        websocket_data[name]['lastPrice'] = current_price
                    if current_oi:
                        if current_time <= websocket_data[name]['expiration']:
                            delta_percent = (float(current_oi)/float(websocket_data[name]['oi']))*100-100
                            if delta_percent <= float(percent):
                                logging.info(f'{name} pass condition')
                                delta_price = (float(websocket_data[name]['lastPrice'])/float(websocket_data[name]['firstPrice']))*100-100
                                try:
                                    time_refresh = websocket_data[name]['refresh_count']
                                    if time_refresh < time.time():  
                                        websocket_data[name]['refresh_count'] = time_refresh+86400
                                        websocket_data[name]['count_signal'] = 0
                                    websocket_data[name]['count_signal'] += 1
                                    task = asyncio.create_task(self.rabbit_send_to_telegram(data=f"{name} {timeframe} {delta_percent} {delta_price} {websocket_data[name]['count_signal']}"), name='send a signal to tg')
                                except Exception as e:
                                    logging.error(e)
                                updated_expiration = time.time() + float(timeframe)*60
                                websocket_data[name]['expiration'] = updated_expiration
                                websocket_data[name]['firstPrice'] = websocket_data[name]['lastPrice']
                                websocket_data[name]['oi'] = current_oi
                        else:
                            websocket_data[name]['oi'] = current_oi
                    if (current_time >= websocket_data[name]['expiration']) and current_oi:
                        updated_expiration = time.time() + float(timeframe)*60
                        websocket_data[name]['expiration'] = updated_expiration
                        websocket_data[name]['firstPrice'] = websocket_data[name]['lastPrice']
                    
                else:
                    websocket_data[name] = {
                        'expiration': start_expiration, 
                        'oi': message['data']['openInterestValue'], 
                        'firstPrice': message['data']['lastPrice'],
                        'lastPrice': message['data']['lastPrice'],
                        'count_signal': 0,
                        'refresh_count': time.time()+86400
                        }
            else:
                logging.info('Connection has been closed due to tg user')

async def main():
    client = Screener(mq_user=os.getenv('RMUSER'), mq_password=os.getenv('RMPASSWORD'), hostname=os.getenv('HOSTNAME'))
    await client.rabbit_connection_tg()              

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, filename="py_log_short.log",filemode="w",
                    format="%(asctime)s %(levelname)s %(message)s")
    asyncio.run(main())