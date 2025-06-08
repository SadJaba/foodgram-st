from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken import views

from .views import (
    CustomUserViewSet, IngredientViewSet, RecipeViewSet
)

app_name = 'api'

router = DefaultRouter()
router.register('users', CustomUserViewSet)
router.register('ingredients', IngredientViewSet)
router.register('recipes', RecipeViewSet)

urlpatterns = [
    path('users/me/avatar/',
         CustomUserViewSet.as_view({'put': 'set_avatar', 'delete': 'delete_avatar'})),
    path('', include(router.urls)),
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]