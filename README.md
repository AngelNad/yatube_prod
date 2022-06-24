# yatube_project
<h2 align="center">Социальная сеть блогеров _Yatube_</h2>

### Описание
Благодаря этому проекту можно создать социальную сеть, где можно публиковать личные дневники.<br>
Пользователи смогут заходить на чужие страницы, подписываться на авторов, 
комментировать их записи, отмечать понравившиеся посты лайками.
### Технологии
Python 3.9<br>
Django 2.2.19
CSS
Bootstrap
SQLite
### Запуск проекта в dev-режиме
- Клонируйте репозиторий и перейдите в него в командной строке:
```
git clone https://github.com/AngelNad/yatube_prod

cd yatube_prod
```
- Установите и активируйте виртуальное окружение
```
python -m venv venv

source venv/Scripts/activate
```

- Установите зависимости из файла requirements.txt
```
pip install -r requirements.txt
``` 
- В папке с файлом manage.py выполните команды:
```
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```
### Автор
Надежда Осипова
