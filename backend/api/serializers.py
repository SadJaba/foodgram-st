from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from djoser.serializers import UserCreateSerializer, UserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework.authtoken.models import Token
import re

from .models import (
    Ingredient, Recipe, IngredientAmount,
    Subscription, Favorite, ShoppingCart
)

User = get_user_model()


class CustomUserCreateSerializer(UserCreateSerializer):
    """Сериализатор создания пользователя."""
    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name',
            'last_name', 'password'
        )
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'required': True},
            'username': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True}
        }

    def validate_username(self, value):
        if not re.match(r'^[\w.@+-]+$', value):
            raise serializers.ValidationError(
                'Имя пользователя должно содержать только буквы, цифры и символы @/./+/-/_'
            )
        return value

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()
        return user


class CustomUserSerializer(UserSerializer):
    """Сериализатор пользователя."""
    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.ImageField(read_only=True)

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name',
            'last_name', 'is_subscribed', 'avatar'
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return Subscription.objects.filter(
            user=request.user, author=obj
        ).exists()


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор ингредиента."""
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class IngredientAmountSerializer(serializers.ModelSerializer):
    """Сериализатор количества ингредиента."""
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = IngredientAmount
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор рецепта."""
    author = CustomUserSerializer(read_only=True)
    ingredients = IngredientAmountSerializer(
        source='ingredient_amounts',
        many=True,
        read_only=True,
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'author', 'ingredients',
            'is_favorited', 'is_in_shopping_cart',
            'name', 'image', 'text', 'cooking_time'
        )

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return Favorite.objects.filter(
            user=request.user, recipe=obj
        ).exists()

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return ShoppingCart.objects.filter(
            user=request.user, recipe=obj
        ).exists()


class RecipeCreateSerializer(serializers.ModelSerializer):
    """Сериализатор создания рецепта."""
    ingredients = serializers.ListField(
        child=serializers.DictField(
            child=serializers.IntegerField(),
        ),
        required=True
    )
    image = Base64ImageField(required=True)
    name = serializers.CharField(required=True, max_length=256)
    text = serializers.CharField(required=True)
    cooking_time = serializers.IntegerField(required=True, min_value=1)

    class Meta:
        model = Recipe
        fields = (
            'ingredients', 'image',
            'name', 'text', 'cooking_time'
        )

    def validate_image(self, value):
        if not value:
            raise serializers.ValidationError(
                'Поле image обязательно для заполнения'
            )
        return value

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError(
                'Список ингредиентов не может быть пустым'
            )
        ingredients_ids = [item.get('id') for item in value]
        if len(ingredients_ids) != len(set(ingredients_ids)):
            raise serializers.ValidationError(
                'Ингредиенты не должны повторяться'
            )
        for item in value:
            if 'id' not in item or 'amount' not in item:
                raise serializers.ValidationError(
                    'Каждый ингредиент должен содержать id и amount'
                )
            if not isinstance(item['id'], int) or not isinstance(item['amount'], int):
                raise serializers.ValidationError(
                    'id и amount должны быть целыми числами'
                )
            if item['amount'] < 1:
                raise serializers.ValidationError(
                    'Количество ингредиента должно быть больше либо равно 1'
                )
            if not Ingredient.objects.filter(id=item['id']).exists():
                raise serializers.ValidationError(
                    f'Ингредиент с id {item["id"]} не найден'
                )
        return value

    def validate_cooking_time(self, value):
        if value < 1:
            raise serializers.ValidationError(
                'Время приготовления должно быть больше либо равно 1'
            )
        return value

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        self._create_ingredients(recipe, ingredients_data)
        return recipe

    def update(self, instance, validated_data):
        if self.context['request'].method == 'PATCH' and 'ingredients' not in validated_data:
            raise serializers.ValidationError(
                {'ingredients': 'Поле ingredients обязательно для заполнения'}
            )
            
        if 'ingredients' in validated_data:
            ingredients_data = validated_data.pop('ingredients')
            instance.ingredients.clear()
            self._create_ingredients(instance, ingredients_data)
        return super().update(instance, validated_data)

    def _create_ingredients(self, recipe, ingredients_data):
        for ingredient_data in ingredients_data:
            ingredient = Ingredient.objects.get(id=ingredient_data.get('id'))
            IngredientAmount.objects.create(
                recipe=recipe,
                ingredient=ingredient,
                amount=ingredient_data.get('amount')
            )

    def to_representation(self, instance):
        return RecipeSerializer(instance, context=self.context).data


class RecipeUpdateSerializer(RecipeCreateSerializer):
    """Сериализатор обновления рецепта."""
    class Meta:
        model = Recipe
        fields = (
            'ingredients', 'image',
            'name', 'text', 'cooking_time'
        )
        extra_kwargs = {
            'ingredients': {'required': True},
            'image': {'required': True},
            'name': {'required': True},
            'text': {'required': True},
            'cooking_time': {'required': True}
        }


class RecipeMinifiedSerializer(serializers.ModelSerializer):
    """Сериализатор для минифицированного представления рецепта."""
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class SubscriptionSerializer(serializers.ModelSerializer):
    """Сериализатор для подписок."""
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id', 'username', 'first_name', 'last_name',
            'email', 'is_subscribed', 'avatar', 'recipes_count',
            'recipes'
        )

    def get_recipes(self, obj):
        """Получение рецептов пользователя."""
        request = self.context.get('request')
        recipes_limit = request.query_params.get('recipes_limit')
        recipes = obj.recipes.all()
        if recipes_limit:
            recipes = recipes[:int(recipes_limit)]
        return RecipeMinifiedSerializer(recipes, many=True).data

    def get_recipes_count(self, obj):
        """Получение количества рецептов пользователя."""
        return obj.recipes.count()

    def get_is_subscribed(self, obj):
        """Проверка подписки на пользователя."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Subscription.objects.filter(
                user=request.user,
                author=obj
            ).exists()
        return False


class SetPasswordSerializer(serializers.Serializer):
    """Сериализатор изменения пароля."""
    new_password = serializers.CharField(required=True)
    current_password = serializers.CharField(required=True)


class TokenCreateSerializer(serializers.Serializer):
    """Сериализатор создания токена."""
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, style={'input_type': 'password'})

    def validate(self, data):
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            raise serializers.ValidationError(
                {'detail': 'Необходимо указать email и пароль'}
            )
            
        user = User.objects.filter(email=email).first()
        
        if not user:
            raise serializers.ValidationError(
                {'detail': 'Пользователь с таким email не найден'}
            )
            
        if not user.check_password(password):
            raise serializers.ValidationError(
                {'detail': 'Неверный пароль'}
            )
            
        self.user = user
        token, _ = Token.objects.get_or_create(user=user)
        return {'auth_token': token.key}


class TokenGetResponseSerializer(serializers.ModelSerializer):
    """Сериализатор ответа с токеном."""
    auth_token = serializers.CharField(source='key')

    class Meta:
        model = Token
        fields = ('auth_token',)


class SetAvatarSerializer(serializers.Serializer):
    """Сериализатор установки аватара."""
    avatar = Base64ImageField(required=True)


class SetAvatarResponseSerializer(serializers.ModelSerializer):
    """Сериализатор ответа установки аватара."""
    class Meta:
        model = User
        fields = ('avatar',)


class RecipeGetShortLinkSerializer(serializers.ModelSerializer):
    """Сериализатор для получения короткой ссылки на рецепт."""
    short_link = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ('short_link',)

    def get_short_link(self, obj):
        return f"http://foodgram.example.org/s/{obj.id}"

    def to_representation(self, instance):
        data = super().to_representation(instance)
        return {'short-link': data['short_link']}


class BaseUserRecipeSerializer(serializers.ModelSerializer):
    """Базовый сериализатор для моделей с отношениями пользователь-рецепт."""
    def to_representation(self, instance):
        """Представление данных."""
        return RecipeMinifiedSerializer(
            instance.recipe,
            context={'request': self.context.get('request')}
        ).data


class FavoriteSerializer(BaseUserRecipeSerializer):
    """Сериализатор для избранного."""
    class Meta:
        model = Favorite
        fields = ('user', 'recipe')

    def validate(self, data):
        """Валидация избранного."""
        if Favorite.objects.filter(
                user=data['user'],
                recipe=data['recipe']
        ).exists():
            raise serializers.ValidationError(
                {'detail': 'Рецепт уже добавлен в избранное'}
            )
        return data


class ShoppingCartSerializer(BaseUserRecipeSerializer):
    """Сериализатор для списка покупок."""
    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe')

    def validate(self, data):
        """Валидация списка покупок."""
        if ShoppingCart.objects.filter(
                user=data['user'],
                recipe=data['recipe']
        ).exists():
            raise serializers.ValidationError(
                {'detail': 'Рецепт уже добавлен в список покупок'}
            )
        return data