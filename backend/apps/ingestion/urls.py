from django.urls import path
from . import views

urlpatterns = [
    path('upload/', views.UploadView.as_view(), name='upload'),
    path('batches/', views.BatchListView.as_view(), name='batch-list'),
    path('batches/<int:pk>/', views.BatchDetailView.as_view(), name='batch-detail'),
]
