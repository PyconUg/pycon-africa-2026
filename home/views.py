from django.shortcuts import render,  get_object_or_404, redirect
from django.utils import timezone
from django.views.generic import ListView
from django.template import RequestContext
from django.views.generic.detail import DetailView
from .forms import *
from hitcount.views import HitCountDetailView
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from next_prev import next_in_order, prev_in_order 
from django.utils.timezone import now
from .models import *  
from .models import EventYear
from pycon2026.views import SPONSORS_2026

def homepage(request):
    current_year = now().year
    upcoming_pycon_events = PyConEvent.objects.filter(start_date__gte=now()).exclude(year=current_year)
    pycon_africa_this_year = EventYear.objects.filter(year=current_year).first()
    
    context = {
        'upcoming_pycon_events': upcoming_pycon_events,
        'pycon_africa_this_year': pycon_africa_this_year,
        'current_year': current_year,
        'sponsors_data': SPONSORS_2026,
        'has_sponsors': any(tier["sponsors"] for tier in SPONSORS_2026),
    }
    
    return render(request, 'home/home.html', context)


def home_for_year(request, year):
    event_year = EventYear.objects.get(year=year)
    template_name = f"{event_year.template_path}"
    context = {
        # Your context data here
        'event_year': event_year,
    }
    return render(request, template_name, context)

 
 


def handler404(request, exception):
    return render(request, '404.html', locals())

 
