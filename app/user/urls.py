from django.urls import path
from user import views


app_name = 'user'

urlpatterns = [
<<<<<<< HEAD
    path('create/', views.CreateUserView.as_view(), name='create'),
    path('token/', views.TokenView.as_view(), name='token'),
]
=======
    path('create/', views.CreateUserView.as_view(), name='create')
]
>>>>>>> 5ef188385652ef6a58990bdd5deaa229bdec6a82
