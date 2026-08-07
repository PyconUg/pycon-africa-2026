from django.urls import path, include
from . import views
from .views import *
 



app_name = 'speakers'
urlpatterns = [
    path('', Speakers.as_view(), name='speakers'),
    path('search/', views.speaker_search, name='speaker_search'),
    path('<profile_id>/', SpeakerDetailView.as_view(), name='speaker_detail'),
    path('hitcount/', include(('hitcount.urls', 'hitcount'), namespace='hitcount')),
]


