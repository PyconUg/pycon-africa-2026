"""pyconafrica URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path
from django.conf.urls import handler404, handler500  
from django_robohash.views import robohash 
from django.views.static import serve  

urlpatterns = [

#Apps
    path('', include('home.urls', namespace='homepage')), 
    path('2019/', include('pyconafrica2019.urls', namespace='pyconafrica2019')),
    path('2020/', include('pycon2020.urls')),
    path('2026/', include('pycon2026.urls')),
    path('<int:year>/', include([
        path('', include('home.urls')),
        path('about/', include('about.urls')),
        path('speakers/', include('speakers.urls')),
        path('schedule/', include('schedule.urls')),
        path('schedule-legacy/', include('conference_schedule.urls')),
        path('our-sponsors/', include('sponsors.urls', namespace='sponsors')),
        path('talks/', include('talks.urls', namespace='talks')),
        path('coc/', include('coc.urls')),
        path('sponsor-us/', include('sponsor_us.urls', namespace='sponsor_us')),
        # Add more apps here following the same pattern
        path('h&g/', include('health_safety_guideline.urls', namespace='health_safety_guideline')),
        path('opportunity-grants/', include('fin_aid.urls', namespace='fin_aid')),
        path('privacy-policy/', include('privacypolicy.urls', namespace='privacypolicy')),
        path('tickets/', include('tickets.urls', namespace='ticket')),
        path('travel-guide/', include('travel_guide.urls', namespace='travel_guide')),

        #Leave this last to catch all pages
        path('', include('cms.urls')),   
    ])),
    path('organizers/', admin.site.urls),  
    path('2025/', include('pycon2025.urls')),

#Thrid party Apps 
    path('summernote/', include('django_summernote.urls')),
    path('tinymce/', include('tinymce.urls')),
    path('accounts/profile/', include('registration.urls', namespace='profiles')),  
    path('accounts/', include('registration.backends.default.urls')),
    path('grappelli/', include('grappelli.urls')), # grappelli URLS
    path('robohash/<string>/', robohash, name='robohash'),
    path('avatar/', include('avatar.urls')),
    path('markdownx/', include('markdownx.urls')),
    re_path(r'hitcount/', include('hitcount.urls', namespace='hitcount')),


] 
if settings.DEBUG:
    from debug_toolbar.toolbar import debug_toolbar_urls
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += debug_toolbar_urls()


# Adds ``STATIC_URL`` to the context of error pages, so that error
# pages can use JS, CSS and images.

handler404 = 'home.views.handler404'

# Modifies default django admin titles and headers with custom app detail.
admin.site.site_header = "PyCon Uganda Admin"
admin.site.site_title = "PyCon Uganda Admin Portal"
admin.site.index_title = "Welcome to PyCon Uganda Portal"