import asyncio
import random
from datetime import datetime, timedelta

from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, FSInputFile, CallbackQuery, ReplyKeyboardRemove

import keyboard as kb
from bot import bot
import database.reqiest as rq

router = Router(name=__name__)
tasks = {}
reply_events: dict[int, asyncio.Event] = {}


@router.message(CommandStart())
async def cmd(mes: Message):
    await mes.answer('Добро пожаловать!🖐, здесь вы можите получить свою кричащию крысу🐀!', reply_markup=kb.start)


@router.message(F.text == "Получить крысу🐀")
async def start_rat(mes: Message):
    tg_id = mes.from_user.id
    user = await rq.get_user_by_tg_id(tg_id)
    now = datetime.now()
    await rq.rat_deaf(tg_id)
    if not user:
        await rq.commit_user(start_time=now, tg_id=tg_id)
    await base_rat(tg_id)
    asyncio.create_task(scream(tg_id))



async def next_scream(start_time: datetime, days_done: int):
    base = start_time + timedelta(days=days_done)
    window_end = base + timedelta(hours=24) - timedelta(minutes=30)
    total_secs = int((window_end - base).total_seconds())
    return base + timedelta(seconds=random.randint(0, total_secs))


async def scream(tg_id: int):
    """
    Бесконечный цикл: для каждого дня ждём случайный момент,
    шлём анимацию и увеличиваем days_survival.
    """

    # 1) Получаем текущие данные из БД
    user = await rq.get_user_by_tg_id(tg_id)
    if not user or not user.time:
        # ещё не инициализирован — ждём, прежде чем пытаться снова
        await asyncio.sleep(5)
        return

    # 2) Парсим базовую дату и счётчик
    start_time = datetime.fromisoformat(user.time)
    days_done = int(user.days_survival)

    # 3) Вычисляем точное время
    next_send = await next_scream(start_time, days_done)  # <--- **await** тут обязательно
    wait = (next_send - datetime.now()).total_seconds()

    # 4) Ждём до нужного момента (если оно ещё в будущем)
    if wait > 0:
        print(f"[{tg_id}] ждём до {next_send}")
        await asyncio.sleep(wait)
    ev = asyncio.Event()
    reply_events[tg_id] = ev
    # 5) Отправляем анимацию
    #    Тут можно повторно использовать тот же base_rat.gif или выбрать другую
    base_path = r"C:\Users\User\PycharmProjects\screaming_rat\awesome_project\rats\scream_rat.gif"
    animation = FSInputFile(base_path)
    await bot.send_animation(tg_id, animation, reply_markup=kb.stop_scream)
    await bot.send_message(tg_id, text='AAAAAAAAAA')


    try:
        await asyncio.wait_for(ev.wait(), timeout=1 * 60)
    except asyncio.TimeoutError:
        # ответа не было — удаляем событие и заканчиваем цикл
        reply_events.pop(tg_id, None)
        base_path = r"C:\Users\User\PycharmProjects\screaming_rat\awesome_project\rats\deaf_rat.gif"
        deaf_animation = FSInputFile(base_path)
        days = await rq.get_days(tg_id)
        await bot.send_animation(tg_id, deaf_animation, caption=f"⚰Ваша крыса🐀 прожила {days}🪦", reply_markup=kb.start)
        await rq.rat_deaf(tg_id)
        return
    else:
        # ответ получен вовремя — убираем событие, инкрементируем счётчик и запускаем новый цикл
        reply_events.pop(tg_id, None)
        asyncio.create_task(scream(tg_id))


@router.message(F.text == 'НАКОРМИТЬ БРАУНИ🍮')
async def stop_scream(mes: Message):
    tg_id = mes.from_user.id
    # если у нас ждут reply именно от этого пользователя — ставим event
    ev = reply_events.get(tg_id)
    ev.set()
    await rq.increment_days(tg_id)
    await base_rat(tg_id)


async def base_rat(tg_id):
    base_path = r"C:\Users\User\PycharmProjects\screaming_rat\awesome_project\rats\base_rat.gif"
    animation = FSInputFile(base_path)
    days = await rq.get_days(tg_id)
    await bot.send_animation(tg_id, animation, reply_markup=ReplyKeyboardRemove())
    await bot.send_message(tg_id, text=f'Ваше крысе {days} дней', reply_markup=kb.main)


@router.callback_query(F.data == "squish_rat")
async def squish_rat(callback: CallbackQuery):
    animation = FSInputFile(r"C:\Users\User\PycharmProjects\screaming_rat\awesome_project\rats\squish_rat.gif")
    await callback.answer()
    await callback.message.answer_animation(animation, reply_markup=kb.return_to_main)


@router.callback_query(F.data == 'return_home')
async def return_to_main(callback: CallbackQuery):
    tg_id = callback.from_user.id
    await callback.answer()
    await base_rat(tg_id)
