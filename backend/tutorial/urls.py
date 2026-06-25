from django.urls import path

from .views import CompleteModuleView, ModuleListView, ProgressView

urlpatterns = [
    path('modules/', ModuleListView.as_view(), name='tutorial-modules'),
    path('progress/', ProgressView.as_view(), name='tutorial-progress'),
    path('complete/', CompleteModuleView.as_view(), name='tutorial-complete'),
]
