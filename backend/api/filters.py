import django_filters
import logging
from django.db.models import Q
from .models import Recipe, Favorite, ShoppingCart, Ingredient

logger = logging.getLogger(__name__)

class IngredientFilter(django_filters.FilterSet):
    """Фильтр для ингредиентов."""
    name = django_filters.CharFilter(lookup_expr='startswith')

    class Meta:
        model = Ingredient
        fields = ('name',)

class RecipeFilter(django_filters.FilterSet):
    """Фильтр для рецептов."""
    author = django_filters.NumberFilter(field_name='author__id')
    is_favorited = django_filters.CharFilter(method='get_is_favorited')
    is_in_shopping_cart = django_filters.CharFilter(method='get_is_in_shopping_cart')

    class Meta:
        model = Recipe
        fields = ('author', 'is_favorited', 'is_in_shopping_cart')

    def get_is_favorited(self, queryset, name, value):
        user = self.request.user
        logger.info(f"Filter is_favorited called with value: {value}, type: {type(value)}")
        
        if not user.is_authenticated:
            logger.info("User not authenticated, returning all recipes")
            return queryset
        
        # c BoleanFilter не работало, реализовал так
        true_values = ['1', 'true', 'True', 'yes', 'Yes', 'y', 'Y']
        if value in true_values:
            logger.info(f"Filtering favorites for user: {user.id}")
            favorites_queryset = queryset.filter(favorites__user=user).distinct()
            logger.info(f"Found {favorites_queryset.count()} favorite recipes")
            return favorites_queryset
        
        logger.info("Not filtering by favorites")
        return queryset

    def get_is_in_shopping_cart(self, queryset, name, value):
        user = self.request.user
        logger.info(f"Filter is_in_shopping_cart called with value: {value}, type: {type(value)}")
        
        if not user.is_authenticated:
            logger.info("User not authenticated, returning all recipes")
            return queryset
        
        # c BoleanFilter не работало, реализовал так
        true_values = ['1', 'true', 'True', 'yes', 'Yes', 'y', 'Y']
        if value in true_values:
            logger.info(f"Filtering shopping cart for user: {user.id}")
        
            cart_queryset = queryset.filter(shopping_cart__user=user).distinct()
            logger.info(f"Found {cart_queryset.count()} recipes in shopping cart")
            return cart_queryset
        
        logger.info("Not filtering by shopping cart")
        return queryset 