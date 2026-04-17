from django.shortcuts import render

# Create your views here.

def home2026(request):
    context = {}
    template = 'home.html'
    return render(request, template, context)
  
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
    context = {}
    template = '2026/sponsors/sponsors.html'
    return render(request, template, context)

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

def fin_aid(request):
    context = {}
    template = '2026/fin-aid/fin-aid.html'
    return render(request, template, context)

def team(request):
    context = {}
    template = '2026/team/team.html'
    return render(request, template, context)

def report(request):
    context = {}
    template = '2026/report/report.html'
    return render(request, template, context)

def pyladies(request):
    context = {}
    template = '2026/community/pyladies.html'
    return render(request, template, context)
    
def django_girls(request):
    context = {}
    template = '2026/community/django_girls.html'
    return render(request, template, context)

def pyladies_wksp(request):
    context = {
        'title': "Pyladies Open Source Summit",
        'description': "Pyladies Kampala Open Source Summit that will bring together Python enthusiasts and open-source advocates, both new and experienced, for a one-day event aimed at building community and promoting contributions to open source.",
    }
    template = '2026/community/pyladies_wksp.html'
    return render(request, template, context)
def ngombor(request):
    context = {
        'title': 'Pyladies Kampala Open Source Workshop',
        'description': 'PyLadies Uganda is a group of women developers who love the Python programming language.',
    }
    return render(request, '2026/community/ngombor.html', context)


def past_events(request):
    return render(request, '2026/past_events/past_events.html')
