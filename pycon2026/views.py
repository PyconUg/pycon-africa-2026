from django.shortcuts import render, get_object_or_404

SPONSORS_2026 = [
    {
        "id": "gold",
        "label": "Gold Sponsors",
        "sponsors": [
            {
                "name": "JetBrains",
                "logo": "2026/img/sponsors/jetbrains.png",
                "website": "https://www.jetbrains.com/",
                "description": "JetBrains creates intelligent developer tools used by software teams around the world.",
            },
        ],
    },
]


def home2026(request):
    context = {
        "sponsors_data": SPONSORS_2026,
        "has_sponsors": any(tier["sponsors"] for tier in SPONSORS_2026),
    }
    return render(request, 'home.html', context)
  
def hopin(request):
    context = {"about": "active"}
    template = '2026/hopin.html'
    return render(request, template, context)

def about(request):
    context = {}
    return render(request, '2026/about/pycon_africa_2026.html', context)


def about_pycon_africa_2026(request):
    context = {}
    return render(request, '2026/about/pycon_africa_2026.html', context)


def about_kenya_region(request):
    context = {}
    return render(request, '2026/about/kenya_region.html', context)


def about_rwanda_region(request):
    context = {}
    return render(request, '2026/about/rwanda_region.html', context)


def about_tanzania_region(request):
    context = {}
    return render(request, '2026/about/tanzania_region.html', context)


def about_south_sudan_region(request):
    context = {}
    return render(request, '2026/about/south_sudan_region.html', context)


def venue_hotels(request):
    context = {}
    return render(request, '2026/venue-hotels/venue-hotels.html', context)


def privacy_policy(request):
    context = {}
    return render(request, '2026/about/privacy_policy.html', context)

def submit(request):
    context = {}
    return render(request, '2026/talks/submit.html', context)

def proposing_a_talk(request):
    context = {}
    return render(request, '2026/talks/proposing_a_talk.html', context)

def mentorship(request):
    context = {}
    return render(request, '2026/talks/mentorship.html', context)

def how_to_apply(request):
    context = {}
    return render(request, '2026/talks/how_to_apply.html', context)

def recording_release(request):
    context = {}
    return render(request, '2026/talks/recording_release.html', context)

def proposals(request):
    context = {}
    return render(request, '2026/talks/proposals.html', context)

def contact_us(request):
    context = {}
    return render(request, '2026/about/contact_us.html', context)

def scheduIe(request):
    context = {}
    template = '2026/schedule/schedule.html'
    return render(request, template, context)

def conduct(request):
    context = {}
    template = '2026/conduct/conduct.html'
    return render(request, template, context)


def coc(request):
    context = {}
    return render(request, '2026/coc/coc.html', context)

def guidelines(request):
    context = {}
    template = '2026/conduct/guidelines.html'
    return render(request, template, context)


def speakers(request):
    context = {}
    template = '2026/speakers/speaker_list.html'
    return render(request, template, context)


def eporting(request):
    context = {}
    template = '2026/conduct/eporting-guidelines/eporting-guidelines.html'
    return render(request, template, context)

def sponsor_us(request):
    context = {}
    template = '2026/sponsor-us/sponsor-us.html'  
    return render(request, template, context)

def sponsors(request):
    context = {
        "sponsors_data": SPONSORS_2026,
        "has_sponsors": any(tier["sponsors"] for tier in SPONSORS_2026),
        "year": 2026,
    }
    return render(request, '2026/sponsors/sponsors.html', context)

def register(request):
    context = {}
    template = '2026/register/register.html'
    return render(request, template, context)

def traveladvice(request):
    context = {}
    template = '2026/travel/travel.html'
    return render(request, template, context)

def visa_apply(request):
    context = {}
    return render(request, '2026/visa/apply.html', context)

def visa_letter(request):
    context = {}
    return render(request, '2026/visa/letter.html', context)

def visa_bus(request):
    context = {}
    return render(request, '2026/visa/bus.html', context)

def visa_flying(request):
    context = {}
    return render(request, '2026/visa/flying.html', context)

def team(request):
    context = {}
    template = '2026/team/team.html'
    return render(request, template, context)

def report(request):
    context = {}
    template = '2026/report/report.html'
    return render(request, template, context)

def pyladies(request):
    context = {
        'title': 'PyLadiesCon Africa @ PyCon Africa 2026',
        'description': 'PyLadiesCon Africa is a dedicated program within PyCon Africa 2026 designed to empower and support women in the Python ecosystem across the continent.',
    }
    return render(request, '2026/co-events/pyladies.html', context)
    
def django_girls(request):
    context = {}
    template = '2026/co-events/django_girls.html'
    return render(request, template, context)

def persons_of_concern(request):
    context = {
        'title': 'Refugee Persons of Concern @ PyCon Africa 2026',
        'description': 'Refugee Persons of Concern is a program within PyCon Africa 2026 that supports refugees and migrants in the Python ecosystem across the continent.',
    }
    template = '2026/co-events/persons_of_concern.html'
    return render(request, template, context)  

# def pyladies_con_africa(request):
#     context = {
#         'title': 'Pyladies Conference Africa',
#         'description': 'Pyladies Conference Africa is a one-day event aimed at building community and promoting contributions to open source.',
#     }
#     return render(request, '2026/community/pyladies_con_africa.html', context)

# def refugee_persons_of_concern(request):
#     context = {
#         'title': 'Refugee Persons of Concern',
#         'description': 'We are committed to helping refugee women and girls in Uganda and other parts of Africa to learn how to code and build careers in technology.',
#     }
#     return render(request, '2026/community/refugee_persons_of_concern.html', context)

# def women_in_data_science(request):
#     context = {
#         'title': 'Women in Data Science',
#         'description': 'We are a group of women who are passionate about data science and want to see more women involved in the field.',
#     }
#     return render(request, '2026/community/women_in_data_science.html', context)
def past_events(request):
    return render(request, '2026/past_events/past_events.html')

def tickets(request):
    context = {}
    return render(request, '2026/tickets/tickets.html', context)

def merch(request):
    context = {}
    return render(request, '2026/merch/merch.html', context)
