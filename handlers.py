from aiogram import Router
from aiogram.types import Message, FSInputFile
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext 
import httpx
from states import Profile, Food
from database import save_food, save_profile, save_water, amount_of_water_per_day, get_profile, save_workout, amount_of_workout_per_day, amount_of_food_per_day
from config import WEATHER_API_KEY
import requests
from graph import water_progress_graph, ccal_progress_graph


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
        "/log_water <количество> - Сохраняет, сколько воды выпито.Показывает, сколько осталось до выполнения нормы.\n"
        "/log_food <название продукта> - Бот использует API OpenFoodFacts) для получения информации о продукте. Сохраняет калорийность.\n"
        "/log_workout <тип тренировки> <время (мин)> - Фиксирует сожжённые калории.\n"
        "/check_progress - Показывает, сколько воды и калорий потреблено, сожжено и сколько осталось до выполнения цели.\n"
        "/water_progress_graph - График прогресса по воде\n"
        "/ccal_progress_graph - Графики прогресса по калориям\n"
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
    if temp > 25:
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
async def cmd_log_water(message: Message):
    amount = int(message.text.split()[1])

    client = await get_profile(message.from_user.id)

    await save_water(message.from_user.id,amount)

    amount_today = await amount_of_water_per_day(client.user_id)
    delta = client.water_goal - amount_today
    await message.reply(
        f"Вода: \n"
        f"- Выпито: {amount_today} мл из {client.water_goal } мл.\n"
        f"- Осталось: {delta} мл."
    )



# Пример поиска калорийности продукта. Работает так себе и ищет не то что нужно, но для нашего задания пойдет
def get_food_info(product_name):
    url = f"https://world.openfoodfacts.org/cgi/search.pl?action=process&search_terms={product_name}&json=true"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        products = data.get('products', [])
        if products:  # Проверяем, есть ли найденные продукты
            first_product = products[0]
            return {
                'name': first_product.get('product_name', 'Неизвестно'),
                'calories': first_product.get('nutriments', {}).get('energy-kcal_100g', 0)
            }
        return None
    print(f"Ошибка: {response.status_code}")
    return None


# Обработчик команды /log_food <название продукта>
@router.message(Command("log_food"))
async def cmd_log_food(message: Message, state: FSMContext):
    food_name = message.text.split()[1]

    food_stats = get_food_info(food_name)
    if not food_stats:
        await message.reply("еда не найдена")
        return

    caloric_value = food_stats["calories"]

    await state.update_data(name=food_name)
    await state.update_data(ccals=caloric_value)

    await message.reply(f"{food_name} — {caloric_value} ккал на 100 г. Сколько грамм вы съели?")
    await state.set_state(Food.grams)  

@router.message(Food.grams)
async def process_food_grams(message: Message, state: FSMContext):
    data = await state.get_data()
    grams = int(message.text)

    total_caloric_value = data["ccals"]*grams/100

    await save_food(message.from_user.id, name=data['name'], ccals=total_caloric_value)

    await message.reply(f"Записано: {total_caloric_value} ккал.\n"
    )
    await state.clear()
    
    
# Обработчик команды /log_workout <тип тренировки> <время (мин)>
@router.message(Command("log_workout"))
async def cmd_log_workout(message: Message):
    type_workout = message.text.split()[1]
    amount = float(message.text.split()[2])
    act_ccals = amount * 10
    client = await get_profile(message.from_user.id)


    await save_workout(user_id=message.from_user.id, name=type_workout, amount= act_ccals)
    
    water_plus = 200*(float(amount)//30)

    # при добавлении воды учитываю время одной тренировки а не суммарное время тренировок за день. 
    if amount > 30:
        client.water_goal += water_plus
        await save_profile(client.user_id, {
            "weight": client.weight,
            "height": client.height,
            "age": client.age,
            "activity": client.activity,
            "city": client.city,
            "calories_goal": client.calories_goal,
            "water_goal": client.water_goal
        })

        await message.reply(f"{type_workout} {amount} минут — {act_ccals} ккал. Дополнительно: выпейте {water_plus} мл воды.")
    else:
        # если тренировка меньше 30 минут. никаких плюсов по воде  нет 
        await message.reply(f"{type_workout} {amount} минут — {act_ccals} ккал.")

# Обработчик команды /check_progress
@router.message(Command("check_progress"))
async def cmd_check_progress(message: Message):
    amount_of_food = await amount_of_food_per_day(message.from_user.id) or 0 
    amount_of_water = await amount_of_water_per_day(message.from_user.id) or 0 
    amount_of_workout = await amount_of_workout_per_day(message.from_user.id) or 0
    client = await get_profile(message.from_user.id)
    await message.reply(
        f"📊 Прогресс: \n"
        f"Вода:\n"
        f"- Выпито: {amount_of_water} мл из {client.water_goal} мл.\n"
        f"- Осталось: {client.water_goal - amount_of_water} мл.\n"
        f"Калории:\n"
        f"- Потреблено: {amount_of_food} ккал из {client.calories_goal} ккал.\n"
        f"- Сожжено: {amount_of_workout} ккал.\n"
        f"- Баланс: {amount_of_food - amount_of_workout} ккал.\n"
    )

# Обработчик команды /water_progress_graph
@router.message(Command("water_progress_graph"))
async def cmd_water_progress_graph(message: Message):
    graph_path = await water_progress_graph(message.from_user.id)
    graph = FSInputFile(graph_path)
    await message.answer_photo(photo=graph)

# Обработчик команды /ccal_progress_graph
@router.message(Command("ccal_progress_graph"))
async def cmd_ccal_progress_graph(message: Message):
    graph_path = await ccal_progress_graph(message.from_user.id)
    graph = FSInputFile(graph_path)
    await message.answer_photo(photo=graph)   


# Функция для подключения обработчиков
def setup_handlers(dp):
    dp.include_router(router)