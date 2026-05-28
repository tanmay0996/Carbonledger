from django.urls import path
from . import views

urlpatterns = [
    path('', views.EmissionListView.as_view(), name='emission-list'),
    path('summary/', views.SummaryView.as_view(), name='emission-summary'),
]
