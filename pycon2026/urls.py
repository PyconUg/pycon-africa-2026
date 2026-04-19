from django.urls import path
from . import views

from django.views.generic import TemplateView, RedirectView

app_name = 'pycon2026'
urlpatterns = [
    path('', view=views.home2026, name='home2026'),
    path('about/', view=views.about, name='about'),
    path('about/pycon-africa-2026/', view=views.about_pycon_africa_2026, name='about_pycon_africa_2026'),
    path('about/privacy-policy/', view=views.privacy_policy, name='privacy_policy'),
    path('about/contact-us/', view=views.contact_us, name='contact_us'),
    path('talks/submit/', view=views.submit, name='submit'),
    path('talks/proposals/', view=views.proposals, name='proposals'),
    path('talks/how_to_apply/', view=views.how_to_apply, name='how_to_apply'),
    path('talks/guide/', RedirectView.as_view(pattern_name='pycon2026:proposing_a_talk', permanent=True)),
    path('talks/proposing_a_talk/', view=views.proposing_a_talk, name='proposing_a_talk'),
    path('talks/recording-release/', view=views.recording_release, name='recording_release'),
    path('talks/mentorship/', view=views.mentorship, name='mentorship'),
    path('region/kenya-region/', view=views.about_kenya_region, name='about_kenya_region'),
    path('region/rwanda-region/', view=views.about_rwanda_region, name='about_rwanda_region'),
    path('region/tanzania-region/', view=views.about_tanzania_region, name='about_tanzania_region'),
    path('region/south-sudan-region/', view=views.about_south_sudan_region, name='about_south_sudan_region'),
    path('venue-hotels/', view=views.venue_hotels, name='venue_hotels'),
    path('conduct/', view=views.conduct, name='conduct'),
    path('coc/', view=views.coc, name='coc'),
    path('coc/eporting-guidelines/', TemplateView.as_view(template_name='conduct/eporting-guidelines/eporting-guidelines.html')),
    path('coc/guidelines/', TemplateView.as_view(template_name='conduct/guidelines/guidelines.html')),
    path('sponsor-us/', view=views.sponsor_us, name='sponsor_us'),
    path('speakers_list/', view=views.speakers, name='speakers'),
    path('schedule/', view=views.scheduIe, name='schedule'),
    path('our-sponsors/', view=views.sponsors, name='sponsors'),
    path('register/', view=views.register, name='register'),
    path('travel/', view=views.traveladvice, name='traveladvice'),
    path('visa/apply/', view=views.visa_apply, name='applying_for_visa'),
    path('visa/letter/', view=views.visa_letter, name='visa_letter'),
    path('visa/bus/', view=views.visa_bus, name='visa_bus'),
    path('visa/flying/', view=views.visa_flying, name='visa_flying'),
    # path('fin-aid/', view=views.fin_aid, name='fin_aid'),
    path('team/', view=views.team, name='team'),
    path('report/', view=views.report, name='report'),
    path('platform/', view=views.hopin, name='hopin'), 
    path('co-events/pyladies/', view=views.pyladies, name='pyladies'),
    path('co-events/django-girls/', view=views.django_girls, name='django_girls'),
    # path('co-events/pyladies-wksp/', view=views.pyladies_wksp, name='pyladies_wksp'),   
    # path('co-events/pyladies_con_africa/', views.pyladies_con_africa, name='pyladies_con_africa'),
    path('co-events/persons_of_concern/', views.persons_of_concern, name='persons_of_concern'),
    # path('co-events/women_in_data_science/', views.women_in_data_science, name='women_in_data_science'),   
    # path('co-events/ngombor/', view=views.ngombor, name='ngombor')
    path('past-events/', view=views.past_events, name='past_events'),

]


