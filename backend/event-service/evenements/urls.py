from django.urls import path
from .views import (EvenementListView, EvenementDetailView,
                    SuggestionListView, CategorieListCreateView,
                    MesEvenementsView, MonEvenementDetailView, SoumettreView)

urlpatterns = [
    # Public
    path('', EvenementListView.as_view()),
    path('<int:pk>/', EvenementDetailView.as_view()),
    path('suggestions/', SuggestionListView.as_view()),
    path('categories/', CategorieListCreateView.as_view()),
    # Organisateur
    path('mine/', MesEvenementsView.as_view()),
    path('mine/<int:pk>/', MonEvenementDetailView.as_view()),
    path('mine/<int:pk>/submit/', SoumettreView.as_view()),
]