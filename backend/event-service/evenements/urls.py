from django.urls import path
from .views import (EvenementListView, EvenementDetailView,
                    SuggestionListView, CategorieListCreateView)

urlpatterns = [
    path('', EvenementListView.as_view()),
    path('<int:pk>/', EvenementDetailView.as_view()),
    path('suggestions/', SuggestionListView.as_view()),
    path('categories/', CategorieListCreateView.as_view()),
]