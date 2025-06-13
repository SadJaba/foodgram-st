import json
import os

from django.core.management.base import BaseCommand
from django.conf import settings

from api.models import Ingredient


class Command(BaseCommand):
    help = 'Загрузка ингредиентов из JSON файла'

    def handle(self, *args, **options):
        file_path = os.path.join(settings.BASE_DIR, 'data', 'ingredients.json')
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                ingredients = json.load(file)
                
            for ingredient in ingredients:
                Ingredient.objects.get_or_create(
                    name=ingredient['name'],
                    measurement_unit=ingredient['measurement_unit']
                )
                
            self.stdout.write(
                self.style.SUCCESS('Ингредиенты успешно загружены')
            )
            
        except FileNotFoundError:
            self.stdout.write(
                self.style.ERROR(f'Файл {file_path} не найден')
            )
        except json.JSONDecodeError:
            self.stdout.write(
                self.style.ERROR('Ошибка при чтении JSON файла')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Произошла ошибка: {str(e)}')
            ) 