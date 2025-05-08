from aiogram import Router, F
from aiogram.filters import CommandStart
from dotenv import load_dotenv
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
import aiohttp
import os

import keyboard as kb


load_dotenv()
router = Router(name=__name__)
API_KEY = os.getenv('API_KEY')
tasks = {}


class Main(StatesGroup):
    amount = State()
    currency2 = State()


@router.message(CommandStart())
async def cmd(mes: Message):
    await mes.answer('Добро пожаловать здесь вы можите смотреть курс валют!', reply_markup=kb.main)


@router.message(F.text == 'Выбрать валюту')
async def choice_currency_1(mes: Message, state: FSMContext):
    await mes.answer('Выберите первую валюту', reply_markup=await kb.currency_kb())
    await state.set_state(Main.currency2)


@router.message(Main.currency2)
async def your_amout(mes: Message, state: FSMContext):
    await mes.answer('Введите сумму конвертации', reply_markup=await kb.amout_count())
    await state.update_data(currency2=mes.text)
    await state.set_state(Main.amount)


@router.message(Main.amount)
async def exchange_rate_usd(mes: Message, state: FSMContext):
    try:
        currencys = {
            "Доллар США $": "USD",
            "Евро €": "EUR",
            "Российский рубль ₽": "RUB",
            "Британский фунт £": "GBP",
            "Японская иена ¥": "JPY",
            "Китайский юань ¥": "CNY",
            "Швейцарский франк ₣": "CHF",
            "Канадский доллар $": "CAD",
            "Австралийский доллар $": "AUD",
            "Новая турецкая лира ₺": "TRY",
            "Индийская рупия ₹": "INR",
            "Бразильский реал R$": "BRL",
            "Сингапурский доллар $": "SGD",
            "Норвежская крона kr": "NOK",
            "Шведская крона kr": "SEK",
            "Польский злотый zł": "PLN",
            "Украинская гривна ₴": "UAH",
            "Казахстанский тенге ₸": "KZT",
            "Гонконгский доллар $": "HKD",
            "Дирхам ОАЭ د.إ": "AED"
        }
        await state.update_data(amount=mes.text)
        data_state = await state.get_data()
        amount = float(data_state.get('amount'))
        currency2 = data_state.get('currency2')
        currency2_symbol = currencys[currency2]

        async with aiohttp.ClientSession() as session:
            url = f"https://api.currencyfreaks.com/latest?apikey={API_KEY}&symbols={currency2_symbol}"
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    rate = data["rates"][currency2_symbol]
                    convert = amount * float(rate)
                    await mes.answer(f"Курс Доллара (USD) к {currency2_symbol} ({currency2_symbol}): {convert}",
                                     reply_markup=kb.main)
                else:
                    await mes.answer(f"Ошибка при получении данных: {response.status}")
        await state.clear()
        await ReplyKeyboardRemove

    except ValueError:
        await mes.answer('Неверный формат ❌. Введите числовое значение')

