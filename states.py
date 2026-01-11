from aiogram.fsm.state import State, StatesGroup

class Profile(StatesGroup):
    weight = State() #Вес (в кг)
    height = State() #рост (в см) 
    age = State() #возраст
    activity = State() #Уровень активности (минуты в день)
    city = State() # Город (для получения температуры)
    calories_goal = State() #Цель калорий (по умолчанию рассчитывается, но можно задавать вручную).
    water_goal = State()

class Food(StatesGroup):
    name = State()
    ccals = State()
    grams =State()