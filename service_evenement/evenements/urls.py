from django.urls import path
from .views import EvenementListView, EvenementDetailView, SuggestionListView

urlpatterns = [
    path('evenements/', EvenementListView.as_view()),
    path('evenements/<int:pk>/', EvenementDetailView.as_view()),
    path('suggestions/', SuggestionListView.as_view()),
]