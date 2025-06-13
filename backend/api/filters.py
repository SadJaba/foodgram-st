import django_filters
from .models import Recipe, Favorite, ShoppingCart

class RecipeFilter(django_filters.FilterSet):
    is_favorited = django_filters.NumberFilter(method='get_is_favorited')
    is_in_shopping_cart = django_filters.NumberFilter(method='get_is_in_shopping_cart')
    author = django_filters.NumberFilter(field_name='author__id')

    class Meta:
        model = Recipe
        fields = ('is_favorited', 'is_in_shopping_cart', 'author')

    def get_is_favorited(self, queryset, name, value):
        if value == 1 and self.request.user.is_authenticated:
            return queryset.filter(favorites__user=self.request.user)
        if value == 0 and self.request.user.is_authenticated:
            return queryset.exclude(favorites__user=self.request.user)
        return queryset

    def get_is_in_shopping_cart(self, queryset, name, value):
        if value == 1 and self.request.user.is_authenticated:
            return queryset.filter(shopping_cart__user=self.request.user)
        if value == 0 and self.request.user.is_authenticated:
            return queryset.exclude(shopping_cart__user=self.request.user)
        return queryset 