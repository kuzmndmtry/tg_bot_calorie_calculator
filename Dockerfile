FROM python:3.10

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY . .


ENV TOKEN=""
ENV DB_URL=""
ENV WEATHER_API_KEY=""

CMD ["python", "bot.py"]