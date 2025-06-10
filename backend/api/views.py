from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import render
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAuthenticatedOrReadOnly, SAFE_METHODS
from rest_framework.exceptions import NotFound, PermissionDenied, AuthenticationFailed, ValidationError
from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.http import HttpResponse, FileResponse
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from io import BytesIO

from .models import (
    Ingredient, Recipe, IngredientAmount,
    Subscription, Favorite, ShoppingCart
)
from .serializers import (
    IngredientSerializer, RecipeSerializer,
    RecipeCreateSerializer, SubscriptionSerializer,
    RecipeMinifiedSerializer, SetPasswordSerializer,
    TokenCreateSerializer, TokenGetResponseSerializer,
    SetAvatarSerializer, SetAvatarResponseSerializer,
    RecipeGetShortLinkSerializer
)
from .filters import RecipeFilter

User = get_user_model()


class CustomUserViewSet(UserViewSet):
    """Представление для работы с пользователями."""
    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated]
    )
    def me(self, request):
        """Получение информации о текущем пользователе."""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(
        detail=False,
        methods=['post'],
        permission_classes=[IsAuthenticated]
    )
    def set_password(self, request):
        """Изменение пароля."""
        serializer = SetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        if not user.check_password(serializer.data['current_password']):
            return Response(
                {'detail': 'Неверный пароль'},
                status=status.HTTP_400_BAD_REQUEST
            )
        user.set_password(serializer.data['new_password'])
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated]
    )
    def subscriptions(self, request):
        """Получение списка подписок."""
        user = request.user
        authors = User.objects.filter(following__user=user)
        page = self.paginate_queryset(authors)
        if page is not None:
            serializer = SubscriptionSerializer(
                page, many=True, context={'request': request}
            )
            return self.get_paginated_response(serializer.data)
        serializer = SubscriptionSerializer(
            authors, many=True, context={'request': request}
        )
        return Response(serializer.data)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    def subscribe(self, request, id=None):
        """Подписка/отписка на пользователя."""
        user = request.user
        try:
            author = User.objects.get(id=id)
        except User.DoesNotExist:
            return Response(
                {'detail': 'Пользователь не найден'},
                status=status.HTTP_404_NOT_FOUND
            )

        if request.method == 'POST':
            if user == author:
                return Response(
                    {'detail': 'Нельзя подписаться на самого себя'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if Subscription.objects.filter(
                user=user, author=author
            ).exists():
                return Response(
                    {'detail': 'Вы уже подписаны на этого пользователя'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            subscription = Subscription.objects.create(user=user, author=author)
            serializer = SubscriptionSerializer(
                author, context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            subscription = Subscription.objects.filter(
                user=user, author=author
            )
            if not subscription.exists():
                return Response(
                    {'detail': 'Вы не подписаны на этого пользователя'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['put'],
        permission_classes=[IsAuthenticated]
    )
    def set_avatar(self, request):
        """Установка аватара."""
        serializer = SetAvatarSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        if user.avatar:
            user.avatar.delete()
        user.avatar = serializer.validated_data['avatar']
        user.save()
        return Response(
            SetAvatarResponseSerializer(user).data,
            status=status.HTTP_200_OK
        )

    @action(
        detail=False,
        methods=['delete'],
        permission_classes=[IsAuthenticated]
    )
    def delete_avatar(self, request):
        """Удаление аватара."""
        user = request.user
        if user.avatar:
            user.avatar.delete()
            user.avatar = None
            user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Представление для работы с ингредиентами."""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    search_fields = ('^name',)


class RecipeViewSet(viewsets.ModelViewSet):
    """Представление для работы с рецептами."""
    queryset = Recipe.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_class = RecipeFilter

    def get_serializer_class(self):
        if self.request.method not in SAFE_METHODS:
            return RecipeCreateSerializer
        return RecipeSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_object(self):
        try:
            obj = super().get_object()
            if self.request.method in ['PUT', 'PATCH', 'DELETE']:
                if obj.author != self.request.user:
                    raise PermissionDenied("У вас нет прав на изменение этого рецепта")
            return obj
        except Exception as e:
            if isinstance(e, PermissionDenied):
                raise
            raise NotFound("Рецепт не найден")

    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            self.perform_destroy(instance)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except PermissionDenied:
            raise
        except Exception:
            raise NotFound("Рецепт не найден")

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    def favorite(self, request, pk=None):
        """Добавление/удаление рецепта из избранного."""
        if request.method == 'POST':
            return self._add_to_list(request, pk, Favorite, 'избранном')
        return self._remove_from_list(request, pk, Favorite, 'избранном')

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    def shopping_cart(self, request, pk=None):
        """Добавление/удаление рецепта из списка покупок."""
        if request.method == 'POST':
            return self._add_to_list(request, pk, ShoppingCart, 'списке покупок')
        return self._remove_from_list(request, pk, ShoppingCart, 'списке покупок')

    def _add_to_list(self, request, pk, model, list_name):
        """Добавление рецепта в список."""
        recipe = get_object_or_404(Recipe, id=pk)
        if model.objects.filter(user=request.user, recipe=recipe).exists():
            raise ValidationError(f'Рецепт уже в {list_name}')
        model.objects.create(user=request.user, recipe=recipe)
        serializer = RecipeMinifiedSerializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def _remove_from_list(self, request, pk, model, list_name):
        """Удаление рецепта из списка."""
        recipe = get_object_or_404(Recipe, id=pk)
        if not model.objects.filter(user=request.user, recipe=recipe).exists():
            raise ValidationError(f'Рецепта нет в {list_name}')
        model.objects.filter(user=request.user, recipe=recipe).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        """Скачивание списка покупок."""
        ingredients = self._get_ingredients_for_shopping_cart(request)
        if not ingredients.exists():
            raise ValidationError('Список покупок пуст')
        shopping_list_content = self._generate_shopping_list_content(ingredients)
        return self._create_file_response(shopping_list_content)

    def _get_ingredients_for_shopping_cart(self, request):
        """Получение ингредиентов для списка покупок."""
        return IngredientAmount.objects.filter(
            recipe__shopping_cart__user=request.user
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(amount=Sum('amount'))

    def _generate_shopping_list_content(self, ingredients):
        """Генерация содержимого списка покупок."""
        shopping_list = ['Список покупок:\n\n']
        for ingredient in ingredients:
            name = ingredient['ingredient__name']
            unit = ingredient['ingredient__measurement_unit']
            amount = ingredient['amount']
            shopping_list.append(f'{name} ({unit}) — {amount}\n')
        return ''.join(shopping_list)

    def _create_file_response(self, content):
        """Создание файлового ответа для скачивания."""
        file = BytesIO(content.encode('utf-8'))
        return FileResponse(
            file,
            as_attachment=True,
            filename='shopping_list.txt',
            content_type='text/plain; charset=utf-8'
        )

    @action(
        detail=True,
        methods=['get'],
        permission_classes=[IsAuthenticatedOrReadOnly]
    )
    def get_link(self, request, pk=None):
        """Получение короткой ссылки на рецепт."""
        recipe = get_object_or_404(Recipe, id=pk)
        short_link = f"http://foodgram.example.org/s/{recipe.id}"
        serializer = RecipeGetShortLinkSerializer({'short_link': short_link})
        return Response(serializer.data)