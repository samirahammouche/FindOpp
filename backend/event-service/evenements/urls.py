from django.urls import path

from . import views

urlpatterns = [
    # Public
    path('', views.EvenementListView.as_view()),
    path('<int:pk>/', views.EvenementDetailView.as_view()),
    path('suggestions/', views.SuggestionListView.as_view()),
    path('categories/', views.CategorieListCreateView.as_view()),

    # Organisateur
    path('mine/', views.MesEvenementsView.as_view()),
    path('mine/<int:pk>/', views.MonEvenementDetailView.as_view()),
    path('mine/<int:pk>/submit/', views.SoumettreView.as_view()),

    # Admin
    path('moderation/', views.ModerationListView.as_view()),
    path('moderation/<int:pk>/', views.ModerationDetailView.as_view()),
    path('moderation/<int:pk>/approve/', views.ApprouverView.as_view()),
    path('moderation/<int:pk>/reject/', views.RejeterView.as_view()),
]