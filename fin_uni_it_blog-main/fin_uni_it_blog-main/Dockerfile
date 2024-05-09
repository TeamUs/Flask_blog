# Используем базовый образ Python
FROM python:3.9
# Устанавливаем переменную окружения для отключения режима буферизации
ENV PYTHONUNBUFFERED 1
# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /fin_uni_it_blog-main
# Копируем зависимости проекта в контейнер
COPY requirements.txt /fin_uni_it_blog-main/

# Обновление списков пакетов и установка необходимых пакетов
RUN apt-get update && \
    apt-get install -y libhdf5-dev

# Устанавливаем зависимости проекта
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
# Копируем все файлы проекта в контейнер
COPY . /fin_uni_it_blog-main/
# Определяем команду для запуска приложения
CMD ["python", "app.py"]