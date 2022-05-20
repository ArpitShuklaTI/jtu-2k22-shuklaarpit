from django.urls import path
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken import views

from restapi.views import UserViewSet, CategoryViewSet, GroupViewSet, ExpensesViewSet, index, logout, get_balance, \
    process_logs


router = DefaultRouter()
router.register('users', UserViewSet)
router.register('categories', CategoryViewSet)
router.register('groups', GroupViewSet)
router.register('expenses', ExpensesViewSet)

urlpatterns = [
    path('', index, name='index'),
    path('auth/logout/', logout),
    path('auth/login/', views.obtain_auth_token),
    path('balances/', get_balances),
    path('process-logs/', process_logs)
]

urlpatterns += router.urls
