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

# Сохраняем последнее отправленное сообщение для удаления
active_messages: dict[int, list[int]] = {}


async def delete_active_messages(tg_id: int):
    """Удаляет все сохранённые сообщения пользователя."""
    if tg_id in active_messages:
        for msg_id in active_messages[tg_id]:
            try:
                await bot.delete_message(tg_id, msg_id)
            except Exception as e:
                print(f"[{tg_id}] Не удалось удалить сообщение {msg_id}: {e}")
        active_messages[tg_id] = []


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
    user = await rq.get_user_by_tg_id(tg_id)
    if not user or not user.time:
        await asyncio.sleep(5)
        return

    start_time = datetime.fromisoformat(user.time)
    days_done = int(user.days_survival)

    next_send = await next_scream(start_time, days_done)
    wait = (next_send - datetime.now()).total_seconds()

    if wait > 0:
        print(f"[{tg_id}] ждём до {next_send}")
        await asyncio.sleep(wait)

    await delete_active_messages(tg_id)

    ev = asyncio.Event()
    reply_events[tg_id] = ev

    # Отправляем крик
    base_path = r"C:\Users\User\PycharmProjects\screaming_rat\awesome_project\rats\scream_rat.gif"
    animation = FSInputFile(base_path)
    anim_msg = await bot.send_animation(tg_id, animation, reply_markup=kb.stop_scream)
    text_msg = await bot.send_message(tg_id, text='AAAAAAAAAA')

    active_messages[tg_id] = [anim_msg.message_id, text_msg.message_id]

    try:
        await asyncio.wait_for(ev.wait(), timeout=60)
    except asyncio.TimeoutError:
        reply_events.pop(tg_id, None)
        await delete_active_messages(tg_id)

        base_path = r"C:\Users\User\PycharmProjects\screaming_rat\awesome_project\rats\deaf_rat.gif"
        deaf_animation = FSInputFile(base_path)
        days = await rq.get_days(tg_id)
        await bot.send_animation(tg_id, deaf_animation, caption=f"⚰Ваша крыса🐀 прожила {days}🪦", reply_markup=kb.start)
        await rq.rat_deaf(tg_id)
        return
    else:
        reply_events.pop(tg_id, None)
        asyncio.create_task(scream(tg_id))


@router.message(F.text == 'НАКОРМИТЬ БРАУНИ🍮')
async def stop_scream(mes: Message):
    tg_id = mes.from_user.id
    ev = reply_events.get(tg_id)
    if ev:
        ev.set()
        await rq.increment_days(tg_id)
        await base_rat(tg_id)


async def base_rat(tg_id: int):
    await delete_active_messages(tg_id)

    base_path = r"C:\Users\User\PycharmProjects\screaming_rat\awesome_project\rats\base_rat.gif"
    animation = FSInputFile(base_path)
    days = await rq.get_days(tg_id)
    anim_msg = await bot.send_animation(tg_id, animation, reply_markup=ReplyKeyboardRemove())
    text_msg = await bot.send_message(tg_id, text=f'Ваше крысе {days} дней', reply_markup=kb.main)

    active_messages[tg_id] = [anim_msg.message_id, text_msg.message_id]


@router.callback_query(F.data == "squish_rat")
async def squish_rat(callback: CallbackQuery):
    tg_id = callback.from_user.id
    await callback.answer()
    await delete_active_messages(tg_id)

    anim_path = r"C:\Users\User\PycharmProjects\screaming_rat\awesome_project\rats\squish_rat.gif"
    animation = FSInputFile(anim_path)
    anim_msg = await callback.message.answer_animation(animation, reply_markup=kb.return_to_main)

    active_messages[tg_id] = [anim_msg.message_id]


@router.callback_query(F.data == 'return_home')
async def return_to_main(callback: CallbackQuery):
    tg_id = callback.from_user.id
    await callback.answer()
    await base_rat(tg_id)


@router.callback_query(F.data == "kill_rat")
async def kill_rat(callback: CallbackQuery):
    tg_id = callback.from_user.id

    # Удаляем активные сообщения
    await delete_active_messages(tg_id)

    # Обновляем состояние в БД
    await rq.rat_deaf(tg_id)
    days = await rq.get_days(tg_id)

    # Показываем "смерть" крысы
    anim_path = r"C:\Users\User\PycharmProjects\screaming_rat\awesome_project\rats\deaf_rat.gif"
    animation = FSInputFile(anim_path)
    await callback.message.answer_animation(
        animation=animation,
        caption=f"⚰️ Ваша крыса прожила {days} дней 🪦",
        reply_markup=kb.start
    )

    await callback.answer()
