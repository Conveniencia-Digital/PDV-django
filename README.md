## Este projeto foi feito com:

* [Python 3.12.4](https://www.python.org/)
* [Django 5.1.5](https://www.djangoproject.com/)
* [Django-Ninja 1.3.0](https://django-ninja.dev/)
* [AlpineJS](https://alpinejs.dev/)

## Como rodar o projeto?

* Clone esse repositório.
* Crie um virtualenv com Python 3.
* Ative o virtualenv.
* Instale as dependências.
* Rode as migrações.

```
git clone https://github.com/Conveniencia-Digital/PDV-django.git pdv-django
cd pdv-django

python -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt

python contrib/env_gen.py

docker-compose up -d

python manage.py migrate
python manage.py createsuperuser
```
