from django.urls import path
from . import views


app_name = 'fin_aid'
urlpatterns = [
    path('', views.fin_aid, name='fin_aid'),
    path('apply/', views.fin_aid_apply, name='fin_aid_apply'),
    path('my-application/', views.fin_aid_my_application, name='fin_aid_my_application'),
    path(
        'my-application/edit/',
        views.fin_aid_application_edit,
        name='fin_aid_application_edit',
    ),
    path('reviews/', views.fin_aid_reviews_list, name='fin_aid_reviews'),
    path('reviews/success/', views.fin_aid_review_success, name='fin_aid_review_success'),
    path('reviews/<int:pk>/', views.fin_aid_review_detail, name='fin_aid_review_detail'),
    path('edit/<int:pk>/', views.fin_aid_edit, name='fin_aid_edit'),
]