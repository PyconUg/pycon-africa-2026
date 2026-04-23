from __future__ import absolute_import
from django.shortcuts import render, reverse
from .models import *
from django.http import HttpRequest, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, redirect
from sponsor_us.models import SponsorshipTier

# Create your views here.


def Prospectus(request):
    context = {}
    template = "prospectus.html"
    return render(request, template, context)


def sponsors(request, year):
    # Define sponsors directly in the view, similar to schedule
    sponsors_data = [
        {
            "id": "gold",
            "label": "Gold Sponsors",
            "sponsors": [
                {
                    "name": "Python Software Foundation",
                    "logo": "psf.png",
                    "website": "https://www.python.org/psf/",
                    "description": "The Python Software Foundation is the non-profit organization behind the Python programming language, supporting and promoting Python development worldwide.",
                },
                {
                    "name": "JetBrains",
                    "logo": "2026/img/sponsors/jetbrains.png",
                    "website": "https://www.jetbrains.com/",
                    "description": "JetBrains creates intelligent developer tools used by software teams around the world.",
                },
            ],
        },
    ]

    # Check if we have any sponsors
    has_sponsors = any(tier["sponsors"] for tier in sponsors_data)

    context = {
        "sponsors_data": sponsors_data,
        "has_sponsors": has_sponsors,
        "year": year,
    }

    return render(request, f"{year}/sponsors/sponsors.html", context)


def sponsors_list(request, year):
    event_year = get_object_or_404(EventYear, year=year)
    sponsors = Sponsor.objects.filter(event_year=event_year, is_visible=True).order_by(
        "sponsor_type", "name"
    )
    context = {
        "sponsors": sponsors,
        "year": year,
    }
    return render(request, f"{year}/sponsors/list.html", context)


def sponsor_detail(request, year, slug):
    sponsor = get_object_or_404(Sponsor, slug=slug, event_year__year=year)
    context = {
        "sponsor": sponsor,
        "year": year,
    }
    return render(request, f"{year}/sponsors/detail.html", context)
