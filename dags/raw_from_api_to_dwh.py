from datetime import datetime
from airflow.decorators import dag, task
from airflow.providers.postgres.hooks.postgres import PostgresHook
from sqlalchemy import create_engine
import requests
import pandas as pd
import keys

def send_telegram_alert(context):
    """Отправка уведомления в Telegram при ошибке"""
    token = keys.telegram_token
    chat_id = keys.chat_id

    task_instance = context.get('task_instance')
    dag_id = context.get('dag').dag_id
    task_id = task_instance.task_id
    execution_date = context.get('execution_date')

    message = f"""
ОШИБКА В AIRFLOW DAG
DAG: {dag_id}
Task: {task_id}
Время: {execution_date}
Лог: {task_instance.log_url}
    """

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    requests.post(url, data={"chat_id": chat_id, "text": message})

@dag(
    start_date=datetime(2025, 12, 1),
    schedule_interval='0 */2 * * *',  # Каждые 2 часа
    catchup=False,
    tags=['bybit', 'crypto', 'dwh'],
    default_args={
        'on_failure_callback': send_telegram_alert
    }
)

def bybit_to_postgres():
    @task
    def extract_from_api():
        """
        Получсаем данные из API ByBit
        :return: data
        """
        url = "https://api.bybit.com/v5/market/tickers"
        try: # Создаем проверку выгрузки данных из API
            response = requests.get(url, params={"category": "spot"}, timeout=15)
            data = response.json()
            return data
        except requests.exceptions.RequestException as e:
            raise AirflowException(f"API request failed: {e}")

    @task
    def transform_from_api(data):
        """
        Получаем из extract_from_api() данные, трансформируем и насыщаем их
        """
        current_time = datetime.now()
        transformed_data = []

        for item in data["result"]["list"]: # Парсим JSON и берем что нам нужно
            transformed_data.append({
                'coin': item["symbol"],
                'last_price': float(item["lastPrice"]),
                'max_price_24h': float(item["highPrice24h"]),
                'min_price_24h': float(item["lowPrice24h"]),
                'loaded_at': current_time
            })

        return transformed_data

    @task
    def load_to_dwh(transformed_data):
        """
        загружаем данные в DWH (PostgreSQL),
        который мы развернули в Docker'е для этой цели.
        """
        engine = create_engine(
            "postgresql://postgres:postgres@postgres_dwh:5432/postgres"
        ) # Подключаемся к DWH
        df = pd.DataFrame(transformed_data)

        df.to_sql(
            name='crypto_prices',
            con=engine,
            if_exists='append',
            index=False
        ) # Добавляем данные в DWH

    # Создается оркестрация
    raw_data = extract_from_api()
    transformed = transform_from_api(raw_data)
    load_to_dwh(transformed)

dag = bybit_to_postgres() # создаем DAG