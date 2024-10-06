FROM python:3.10
ENV APP_HOME /app
WORKDIR $APP_HOME
COPY . .
RUN pip install -r requirements.txt
EXPOSE 3000

# Запуск обох серверів у різних процесах
CMD ["python", "main.py"]