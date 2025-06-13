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
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter

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
    RecipeGetShortLinkSerializer, FavoriteSerializer,
    ShoppingCartSerializer
)
from .filters import RecipeFilter
from .pagination import CustomPageNumberPagination

User = get_user_model()


class CustomUserViewSet(UserViewSet):
    """Представление для работы с пользователями."""
    pagination_class = CustomPageNumberPagination

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
            raise ValidationError({'detail': 'Неверный пароль'})
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
        author = get_object_or_404(User, id=id)
        user = request.user
        if request.method == 'POST':
            if user == author:
                raise ValidationError({'detail': 'Нельзя подписаться на самого себя'})
            if Subscription.objects.filter(user=user, author=author).exists():
                raise ValidationError({'detail': 'Вы уже подписаны на этого пользователя'})
            Subscription.objects.create(user=user, author=author)
            serializer = SubscriptionSerializer(author, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        # DELETE
        subscription = Subscription.objects.filter(user=user, author=author)
        if not subscription.exists():
            raise ValidationError({'detail': 'Вы не были подписаны на этого пользователя'})
        subscription.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['put'],
        url_path='avatar',
        permission_classes=[IsAuthenticated]
    )
    def set_avatar(self, request):
        """Установка аватара."""
        if not request.user.is_authenticated:
            return Response(
                {'detail': 'Требуется авторизация'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        user = request.user
        serializer = SetAvatarSerializer(data=request.data)
        if serializer.is_valid():
            if user.avatar:
                user.avatar.delete()
            user.avatar = serializer.validated_data['avatar']
            user.save()
            return Response(
                SetAvatarResponseSerializer(user).data,
                status=status.HTTP_200_OK
            )
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(
        detail=False,
        methods=['delete'],
        url_path='avatar',
        permission_classes=[IsAuthenticated]
    )
    def delete_avatar(self, request):
        """Удаление аватара."""
        if not request.user.is_authenticated:
            return Response(
                {'detail': 'Требуется авторизация'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        user = request.user
        if user.avatar:
            user.avatar.delete()
            user.avatar = None
            user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для ингредиентов."""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('name',)
    search_fields = ('^name',)


class RecipeViewSet(viewsets.ModelViewSet):
    """Представление для работы с рецептами."""
    queryset = Recipe.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_class = RecipeFilter
    pagination_class = CustomPageNumberPagination

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
        try:
            recipe = get_object_or_404(Recipe, id=pk)
            if request.method == 'POST':
                return self._add_to_list(
                    request, recipe, Favorite, FavoriteSerializer, 'избранное'
                )
            return self._remove_from_list(
                request, recipe, Favorite, 'избранного'
            )
        except ValueError:
            return Response(
                {'detail': 'Некорректный ID рецепта'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    def shopping_cart(self, request, pk=None):
        """Добавление/удаление рецепта из списка покупок."""
        try:
            recipe = get_object_or_404(Recipe, id=pk)
            if request.method == 'POST':
                return self._add_to_list(
                    request, recipe, ShoppingCart, ShoppingCartSerializer,
                    'список покупок'
                )
            return self._remove_from_list(
                request, recipe, ShoppingCart, 'списка покупок'
            )
        except ValueError:
            return Response(
                {'detail': 'Некорректный ID рецепта'},
                status=status.HTTP_400_BAD_REQUEST
            )

    def _add_to_list(self, request, recipe, model, serializer_class, list_name):
        """Добавление рецепта в список."""
        data = {
            'user': request.user.id,
            'recipe': recipe.id
        }
        serializer = serializer_class(
            data=data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def _remove_from_list(self, request, recipe, model, list_name):
        """Удаление рецепта из списка."""
        deleted_count, _ = model.objects.filter(
            user=request.user, recipe=recipe
        ).delete()

        if deleted_count:
            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(
            {'detail': f'Рецепт не был добавлен в {list_name}'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        """Скачивание списка покупок."""
        ingredients = self._get_ingredients_for_shopping_cart(request)
        if not ingredients.exists():
            raise ValidationError({'detail': 'Список покупок пуст'})
        shopping_list_content = self._generate_shopping_list_content(ingredients)
        return self._create_file_response(shopping_list_content)

    def _get_ingredients_for_shopping_cart(self, request):
        """Получение ингредиентов для списка покупок."""
        return IngredientAmount.objects.filter(
            recipe__shopping_cart__user=request.user
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(
            amount=Sum('amount')
        ).order_by('ingredient__name')

    def _generate_shopping_list_content(self, ingredients):
        """Генерация содержимого списка покупок."""
        shopping_list = ['Список покупок:\n']
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
        permission_classes=[AllowAny]
    )
    def get_link(self, request, pk=None):
        """Получение короткой ссылки на рецепт."""
        recipe = get_object_or_404(Recipe, id=pk)
        serializer = RecipeGetShortLinkSerializer(recipe)
        return Response(serializer.data)