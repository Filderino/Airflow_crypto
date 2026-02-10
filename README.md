# Проект для автоматического сбора цен на криптовалюты, их анализа и загрузки в DWH

Для запуска проекта, использовался стандартный docker-compose Airflow
https://airflow.apache.org/docs/apache-airflow/3.1.7/docker-compose.yaml
c добавлением DHW (PostgreSQL):

```docker
postgres_dwh:
    image: postgres:13
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: postgres
    restart: always
    ports:
      - "5432:5432"
```

Использовалось виртуальное окружение:
```bash
python3.13 -m venv venv
```

## Создание DWH.
```sql
-- Создаём таблицу и добавляепм колонки
CREATE TABLE crypto_prices (
    id SERIAL PRIMARY KEY,
    coin VARCHAR(50) NOT NULL,
    last_price DECIMAL(20, 8) NOT NULL,
    max_price_24h DECIMAL(20, 8) NOT NULL,
    min_price_24h DECIMAL(20, 8) NOT NULL,
    loaded_at TIMESTAMP NOT NULL
);
```
##Стек проекта
```mermaid
graph LR
    A[External Crypto APIs] --> B[Apache Airflow];
    B --> C[PostgreSQL DWH];
    
    style A fill:#f9f,stroke:#333
    style B fill:#ccf,stroke:#333
    style C fill:#9cf,stroke:#333
```