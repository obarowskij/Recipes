from django.urls import path
from user import views


app_name = "user"

urlpatterns = [
    path("create/", views.CreateUserView.as_view(), name="create"),
    path("token/", views.TokenView.as_view(), name="token"),
    path("me/", views.RetrieveUser.as_view(), name="me"),
]
