from django.urls import path

from . import views

urlpatterns = [
  path('answer', views.question, name='question'),
  path('outcome', views.outcome, name='outcome'),
]