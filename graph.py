import matplotlib.pyplot as plt
from datetime import date, timedelta
from database import amount_of_water_per_day, async_session, amount_of_food_per_day

async def water_progress_graph(client_id):
    days = []
    water_amount = []

    async with async_session() as session:
     for i in reversed(range(7)):
        day = date.today() - timedelta(days=i)
        days.append(day)
        amount = await amount_of_water_per_day(client_id,day)
        water_amount.append(amount)

    plt.figure(figsize=(8, 4))
    plt.bar(days, water_amount)
    plt.title("Прогресс по воде")
    plt.xlabel("Дата")
    plt.ylabel("Кол-во воды, мл")

    filename = "water_progress_graph.png"
    plt.savefig(filename)
    plt.close()
    return filename


async def ccal_progress_graph(client_id):
    days = []
    ccal_amount = []

    async with async_session() as session:
     for i in reversed(range(7)):
        day = date.today() - timedelta(days=i)
        days.append(day)
        amount = await amount_of_food_per_day(client_id,day)
        ccal_amount.append(amount)
        
    plt.figure(figsize=(8, 4))
    plt.bar(days, ccal_amount)
    plt.title("Прогресс по еде")
    plt.xlabel("Дата")
    plt.ylabel("Кол-во еды, ккал")

    filename = "ccal_progress_graph.png"
    plt.savefig(filename)
    plt.close()
    return filename


