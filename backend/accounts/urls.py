from django.urls import path
from . import views

urlpatterns = [
    path('personal-signup/', views.personal_signup),
    path('lawyer-signup/', views.lawyer_signup),
    path('login/', views.login_view),
]
