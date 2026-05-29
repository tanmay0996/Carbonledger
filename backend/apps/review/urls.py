from django.urls import path
from . import views

urlpatterns = [
    path('rows/<int:pk>/approve/', views.ApproveView.as_view(), name='approve'),
    path('rows/<int:pk>/reject/', views.RejectView.as_view(), name='reject'),
    path('rows/<int:pk>/flag/', views.FlagView.as_view(), name='flag'),
    path('rows/<int:pk>/audit-log/', views.AuditLogListView.as_view(), name='audit-log'),
    path('batches/<int:pk>/approve-all/', views.BulkApproveView.as_view(), name='bulk-approve'),
    path('audit-log/', views.GlobalAuditLogView.as_view(), name='global-audit-log'),
]
