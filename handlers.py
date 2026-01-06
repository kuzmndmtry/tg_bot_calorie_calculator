from aiogram import Router
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
import httpx
from states import Profile
import aiohttp
from database import save_profile
from config import WEATHER_API_KEY


router = Router()

# Обработчик команды /start
@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.reply("Добро пожаловать! Я ваш бот.\nВведите /help для списка команд.")

# Обработчик команды /help
@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.reply(
        "Доступные команды:\n"
        "/start - Начало работы\n"
        "/help - Доступные команды\n"
        "/set_profile  - Настройка профиля пользователя \n"
    )
# Настройка профиля пользователя   
# Обработчик команды /set_profile 
@router.message(Command("set_profile"))
async def cmd_set_profile(message: Message, state: FSMContext):
    await message.reply("Введите ваш вес (в кг):")
    await state.set_state(Profile.weight)

@router.message(Profile.weight)
async def process_weight(message: Message, state: FSMContext):
    await state.update_data(weight=message.text)
    await message.reply("Введите ваш рост (в см):") # следующий вопрос
    await state.set_state(Profile.height)

@router.message(Profile.height)
async def process_height(message: Message, state: FSMContext):
    await state.update_data(height=message.text)
    await message.reply("Введите ваш возраст:")
    await state.set_state(Profile.age) 

@router.message(Profile.age)
async def process_age(message: Message, state: FSMContext):
    await state.update_data(age=message.text)
    await message.reply("Сколько минут активности у вас в день?")
    await state.set_state(Profile.activity) 

@router.message(Profile.activity)
async def process_activity(message: Message, state: FSMContext):
    await state.update_data(activity=message.text)
    await message.reply("В каком городе вы находитесь?")
    await state.set_state(Profile.city) 

@router.message(Profile.city)
async def process_city(message: Message, state: FSMContext):
    await state.update_data(city=message.text)
    await message.reply("Какая ваша цель по каллориям?(0 для автоматического расчёта)")
    await state.set_state(Profile.calories_goal) 
    
@router.message(Profile.calories_goal)
async def process_calories(message: Message, state: FSMContext):
    data = await state.get_data()
    calories_goal = int(message.text.strip())

    if int(data['activity']) == 0:
        coef = 0
    elif int(data['activity']) <= 30:
        coef = 200

    elif int(data['activity']) > 60:
        coef = 400
    else:
        coef = 300

    if  calories_goal == 0:
        calories_goal = int(10*float(data['weight']) + 6.25 * float(data['height']) - 5*int(data['age'])) - coef

    await state.update_data(calories_goal=calories_goal)

    temp = await get_weather(data.get('city'))

    # +500 за жаркую погоду (> 25°C).
    if temp > -25:
        temp_coef = 500
    else: temp_coef = 0
    
    act_coef = 500*(int(data.get('activity'))//30) # +500мл  за каждые 30 минут активности.
    
    water_goal = int(30*float(data['weight'])) + temp_coef + act_coef
    await state.update_data(water_goal=water_goal)

    data = await state.get_data()
    await save_profile(message.from_user.id, data)

    await message.reply(f"Профиль сохранён:\n"
                        f"Вес - {data.get('weight')} кг;\n"
                        f"Рост - {data.get('height')} см;\n"
                        f"Возраст - {data.get('age')}\n"
                        f"Активность - {data.get('activity')} мин.\n"
                        f"Город - {data.get('city')}\n"
                        f"Цель по каллориям - {data.get('calories_goal')} ккал;\n"
                        f"Цель по воде - {data.get('water_goal')} мл;\n"
    )
    await state.clear()

async def get_weather(city: str):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)    
            if response.status_code == 200:
                temp = response.json()['main']['temp']    
                return temp  
            else:
                return response.status_code
    except httpx.RequestError as e:
            return str(e)
    
# Обработчик команды /log_water <количество>
@router.message(Command("log_water"))
async def cmd_set_profile(message: Message, state: FSMContext):
    await message.reply("Введите ваш вес (в кг):")

# Функция для подключения обработчиков
def setup_handlers(dp):
    dp.include_router(router)