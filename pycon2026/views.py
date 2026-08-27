from django.shortcuts import render, get_object_or_404
from .schedule_data import SCHEDULE_DATA

TALK_CATEGORY_LABELS = {
    "GP / Web": "General Python, Web/DevOps",
    "GC": "General Community",
    "ET": "Emerging Technologies",
    "Education": "Education",
    "O": "Other",
}

ACCEPTED_POSTERS_2026 = [
    {
        "name": "Frances Adelakun",
        "talk_category": "ET",
        "elevator_pitch": "Many rural communities still don't have a reliable way to know if their water is safe, mainly because testing is expensive and lab access is limited. So we're building a low-cost, offline water quality monitoring system that can work in those environments.\n\nThe system uses simple sensors like pH, turbidity, and temperature sensors, and a lightweight deep learning model running on a Raspberry Pi Zero to detect unusual water conditions in real time. Since getting labeled data in rural areas is difficult, we're using self-supervised learning so the model can learn from raw sensor data with less dependence on annotations.\n\nWhen contamination is detected, the system sends SMS alerts through a GSM module. The goal is to make real-time water monitoring affordable and practical for communities that usually don't have access to these kinds of tools.",
    },
    {
        "name": "Ubaydah Abdulwasiu",
        "talk_category": "GP / Web",
        "elevator_pitch": "Most audit logs are treated as side effects — a separate table recording that “something changed.” This poster explores a different model: append-only event streams where every state transition becomes immutable, replayable, and tamper-evident.\n\nUsing real production-inspired patterns from fintech systems, the poster demonstrates how Python can be used to build audit trails that preserve history, reconstruct past states, and detect retroactive modifications using hash chaining.\n\nAttendees will leave with practical patterns, architectural intuition, and lightweight Python implementations they can adapt to real systems.",
    },
    {
        "name": "Chidera Frankie",
        "talk_category": "ET",
        "elevator_pitch": "Most payment tutorials show you how to charge a card. They don't show you what happens after splitting funds across sellers, crediting wallets, and handling failed webhooks. This poster does.",
    },
    {
        "name": "Chintu Simweene",
        "talk_category": "Education",
        "elevator_pitch": "My poster explores how outdated colonial-era curricula and limited access to educational technology are affecting medical student learning outcomes in Zambian universities. Using a mixed-methods research approach, I examine how digital inequities, infrastructure challenges, and gaps in technology-enhanced learning impact graduate preparedness and healthcare workforce development.\n\nThe project also highlights opportunities for Python-powered educational technologies, AI-assisted learning systems, offline-first platforms and open-source innovation to support more equitable and sustainable medical education across Africa.",
    },
    {
        "name": "Seun Olufemi",
        "talk_category": "GC",
        "elevator_pitch": "A practical playbook for using open source tools to onboard non-technical scientists into open science communities, drawn from two years of grassroots capacity building in Nigeria.",
    },
    {
        "name": "Tariq Ahmed Morio",
        "talk_category": "GC",
        "elevator_pitch": "This poster is designed for educators, developers, community leaders, and students interested in using technology for social impact. It presents a grassroots education initiative from rural Pakistan that provides free academic support to underprivileged children. The focus is on how basic digital literacy and Python programming can be introduced in low-resource communities to improve learning outcomes and future opportunities. It highlights real challenges in rural education and shows how simple, open-source tools can help bridge the gap between traditional education and modern technology-driven skills development.",
    },
    {
        "name": "Muyomba William",
        "talk_category": "GC",
        "elevator_pitch": "Bake and Sign is a trailblazing social enterprise based in Kira Town, Kampala, designed to tackle high unemployment rates within Uganda's deaf and hard of hearing community. By providing specialized vocational training in culinary arts and baking, we equip deaf youth with practical, market ready skills. Distinctively, our products champion sustainable agri-business by utilizing local Ugandan staple crops such as matooke, cassava and bananas into high quality, professional baked goods. Bake and Sign isn't just a bakery it is an inclusive movement proving that communication barriers disappear when a community is given the right tools, skills and platform to thrive.",
    },
    {
        "name": "Victor Egbe",
        "talk_category": "ET",
        "elevator_pitch": "VisionX AI is focused on creating practical solutions for two major challenges: clean energy and clean water. The project explores how smart technology and sustainable systems can help communities access safer water and affordable clean energy in a simple and scalable way. Our goal is to turn innovative ideas into real solutions that improve lives, protect the environment, and support a more sustainable future.",
    },
    {
        "name": "Glory Bagai",
        "talk_category": "ET",
        "elevator_pitch": "Many industries still depend on reactive and scheduled maintenance approaches, where equipment is repaired only after failure or serviced at fixed intervals regardless of actual condition. These methods often lead to unexpected breakdowns, increased downtime, high operational costs, and reduced productivity. Critical industrial equipment, such as turbines, pumps, and compressors, requires continuous monitoring to ensure efficient operation and prevent costly failures. Therefore, there is a need for intelligent predictive maintenance systems that can accurately detect equipment faults early using real-time sensor data and machine learning techniques.\n\nResearch Gaps\nMost existing studies benchmark individual ML classifiers independently without designing ensemble architectures that exploit complementary decision boundaries of heterogeneous learners. Stacking ensembles under class imbalance in industrial IoT fault detection has received limited attention, particularly in the Nigerian and African manufacturing context.",
    },
    {
        "name": "Abubakar Muktar",
        "talk_category": "ET",
        "elevator_pitch": "340 Nigerian children die from malaria every day. GreenChild is a Python-powered platform that turns mothers into a distributed early warning network — collecting daily symptom reports via WhatsApp and USSD, fusing them with climate data, and predicting outbreaks 7–14 days before they reach clinics.",
    },
    {
        "name": "Faruq Afolabi",
        "talk_category": "ET",
        "elevator_pitch": "What if a farmer in rural Nigeria could diagnose a crop disease in under two seconds, with no internet connection, on a phone that costs less than $50? MobileCrop makes that real. It is a production Android app powered by a 2.74 MB knowledge-distilled MobileNetV2 model, built entirely in Python and TensorFlow, covering 17 disease classes across Cassava, Maize, and Tomato. This poster walks through the full pipeline from training to on-device deployment and shares honest findings including a dramatic quantization failure and what it taught us.",
    },
    {
        "name": "Francis Bogere",
        "talk_category": "GC",
        "elevator_pitch": "Many telecom and field engineering operations across Africa face unreliable connectivity, fragmented reporting systems, and limited offline capabilities. This poster explores how Python-powered offline-first systems can support telecom field operations, infrastructure reporting, and community connectivity initiatives in low-resource environments.\n\nThe project highlights practical approaches for data collection, synchronization, automation, and infrastructure monitoring using open technologies and lightweight software systems tailored for African deployment realities.",
    },
    {
        "name": "Moses Cursor Ssebunya",
        "talk_category": "GC",
        "elevator_pitch": "Community is often the invisible force behind successful developers and creatives. This poster explores how mentorship, open-source contribution, collaboration, and local tech communities help individuals grow from learners into confident contributors. Through stories, experiences, and insights from community ecosystems like WordPress and open source in Uganda and beyond, attendees will discover why people grow faster when they grow together.",
    },
    {
        "name": "Daniel Oloki",
        "talk_category": "GP / Web",
        "elevator_pitch": "A Python-powered smart monitoring system designed to help schools and universities track electricity consumption, solar energy performance, and operational efficiency in real time. The project demonstrates how Python, IoT integration, dashboards, and automation can support sustainable and affordable digital transformation in African educational institutions.",
    },
    {
        "name": "Joy Olusanya",
        "talk_category": "O",
        "elevator_pitch": "My target audience includes researchers, developers, and practitioners working in NLP, particularly those interested in low-resource African languages, multilingual machine translation, and culturally aware AI systems.\n\nThe poster explores how well large language models and neural machine translation systems translate Yoruba idioms into English, a challenging task because idioms are deeply cultural and often non-literal. The key focus is to understand where current models fail in capturing cultural meaning and why low-resource African languages like Yoruba remain underrepresented in translation quality. This work will be of interest to anyone building or evaluating language technologies for under-resourced languages, especially in African NLP and culturally grounded machine translation.",
    },
    {
        "name": "Justice Ohene Amofa",
        "talk_category": "ET",
        "elevator_pitch": "Can a Python-based deep learning pipeline reliably support tuberculosis detection using heterogeneous clinical and imaging data?\n\nThis work presents a reproducible machine learning system built in Python that integrates chest X-ray imaging and multivariate patient data to support TB classification, explainability, and deployment in resource-constrained environments.",
    },
]

SPONSORS_2026 = [
    {
        "id": "gold",
        "label": "Gold Sponsor",
        "sponsors": [
            {
                "name": "Google",
                "logo": "2026/img/sponsors/google-for-developers.png",
                "website": "https://www.google.com/",
                "description": "Google has long supported the Python language and its community, from core contributions to CPython to backing community programs like Google Summer of Code that bring new contributors into open source projects.\n\nMany of the tools Python developers rely on day to day, from TensorFlow to gRPC to Google Cloud's Python client libraries, come out of Google's broader investment in developer tooling and open source.\n\nWe're grateful for Google's support of PyCon Africa 2026 as we grow the Python community across the continent.",
            },
        ],
    },
    {
        "id": "silver",
        "label": "Silver Sponsor",
        "sponsors": [
            {
                "name": "Black Python Devs",
                "logo": "2026/img/sponsors/black-python-devs.png",
                "website": "https://blackpythondevs.com/",
                "description": "Black Python Devs is a global community for Black software engineers and Python enthusiasts, built around mentorship, networking, and creating visible pathways into the Python ecosystem.\n\nThrough meetups, talks, and online spaces, the community connects developers across the diaspora, including a growing base of members here in Africa, and champions representation within Python events and open source projects.\n\nWe're glad to have Black Python Devs supporting PyCon Africa 2026 as we work together to grow a more inclusive Python community on the continent.",
            },
        ],
    },
    {
        "id": "bronze",
        "label": "Bronze Sponsor",
        "sponsors": [
            {
                "name": "JetBrains",
                "logo": "2026/img/sponsors/jetbrains.png",
                "website": "https://www.jetbrains.com/",
                "description": "JetBrains builds intelligent developer tools used by software teams around the world, including IntelliJ IDEA, PyCharm, and a growing family of language-specific IDEs, alongside collaboration and productivity tools that help teams ship better software faster.\n\nFor Python developers, PyCharm has long been a go-to IDE, offering smart code completion, debugging, and testing support that makes working in Python more productive whether you're building a small script or a large-scale application.\n\nJetBrains has a long history of supporting the Python community through free licenses for open source maintainers, students, and educators, and by sponsoring conferences and meetups across the globe. We're grateful to have them supporting PyCon Africa 2026 as we grow the Python community on the continent.",
            },
            {
                "name": "Posit",
                "logo": "2026/img/sponsors/posit.png",
                "website": "https://posit.co/",
                "description": "Posit builds open-source and professional tools for data science, including RStudio and Posit tools that support both R and Python workflows for analysis, visualisation, and reporting.\n\nWith products like Positron, Posit Connect, and Quarto, the company backs many of the data science tools that Python developers on the data and analytics side already rely on day to day.\n\nWe're thankful for Posit's support of PyCon Africa 2026, helping us bring more data science resources to our community.",
            },
            {
                "name": "Django Software Foundation",
                # Sponsoring at both the Bronze and Diversity levels, so this
                # entry overrides the tier label rather than being listed twice.
                "label": "Bronze & Diversity Sponsor",
                "logo": "2026/img/sponsors/django.svg",
                "website": "https://www.djangoproject.com/foundation/",
                "description": "The Django Software Foundation is the nonprofit organisation behind the Django web framework, responsible for stewarding the project, funding a Django Fellow to maintain the framework, and supporting the wider community through grants and sponsorships.\n\nDjango remains one of the most widely used Python web frameworks, and the Foundation's ongoing investment in the project and its community has helped Django developers around the world, including many here in Africa, build on a solid, well-supported foundation.\n\nThe Foundation is supporting PyCon Africa 2026 as both a Bronze and a Diversity sponsor, with the diversity contribution going directly towards making the conference reachable for attendees who would otherwise be unable to join us. We're grateful for their support as we grow the Python community across the continent.",
            },
        ],
    },
    {
        "id": "inkind",
        "label": "In-Kind Sponsor",
        "sponsors": [
            {
                "name": "O'Reilly",
                "logo": "2026/img/sponsors/oreilly.jpg",
                "website": "https://www.oreilly.com/",
                "description": "O'Reilly has spent decades helping people learn the skills and ideas that shape the technology industry, first through its widely recognised technical books and now through an online learning platform offering live courses, books, videos, and interactive content covering everything from Python fundamentals to advanced data engineering.\n\nMany Python developers got their start with an O'Reilly book on their desk, and that tradition of practical, in-depth technical learning continues today through the platform's expanding library of Python and data science content.\n\nWe're thankful for O'Reilly's in-kind support of PyCon Africa 2026, helping us equip attendees with resources to keep learning long after the conference ends.",
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


def regions(request):
    return render(request, '2026/regions/regions.html', {})


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


def speaker_guidelines(request):
    return render(request, '2026/talks/speaker_guidelines.html', {})

def proposals(request):
    context = {}
    return render(request, '2026/talks/proposals.html', context)

def contact_us(request):
    context = {}
    return render(request, '2026/about/contact_us.html', context)

def scheduIe(request):
    context = {"tabs": SCHEDULE_DATA, "year": 2026}
    template = '2026/schedule/schedule.html'
    return render(request, template, context)


def accepted_posters(request):
    posters = [
        {**poster, "talk_category_label": TALK_CATEGORY_LABELS[poster["talk_category"]]}
        for poster in ACCEPTED_POSTERS_2026
    ]
    context = {"posters": posters, "year": 2026}
    template = '2026/schedule/accepted_posters.html'
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

def health_safety(request):
    context = {}
    return render(request, '2026/health_safety/health_safety.html', context)

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
        'title': 'Python Without Borders @ PyCon Africa 2026',
        'description': 'Python Without Borders is a dedicated Python and Django workshop for refugees and persons of concern at PyCon Africa 2026, organised by PyLadies Kampala.',
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
def community(request):
    co_events = [
        {
            "name": "PyLadiesCon Africa",
            "description": "A dedicated program within PyCon Africa 2026 to empower women in the Python ecosystem across Africa.",
            "url": "/2026/co-events/pyladies/",
        },
        {
            "name": "Django Girls Workshop",
            "description": "A free one-day workshop for women who want to learn to build websites using Python and Django.",
            "url": "/2026/co-events/django-girls/",
        },
        {
            "name": "Python Without Borders",
            "description": "A dedicated Python and Django workshop for refugees and persons of concern, organised by PyLadies Kampala.",
            "url": "/2026/co-events/persons_of_concern/",
        },
        {
            "name": "Women in Data Science (WiDS)",
            "description": "Inspiring and connecting women in data science across Africa through talks, networking, and workshops.",
            "url": "/2026/co-events/women_in_data_science/",
        },
    ]
    return render(request, '2026/community/community.html', {"co_events": co_events})


def women_in_data_science(request):
    context = {
        'title': 'Women in Data Science (WiDS)',
        'description': 'Inspiring and connecting women in data science across Africa.',
    }
    return render(request, '2026/co-events/women_in_data_science.html', context)


def past_events(request):
    return render(request, '2026/past_events/past_events.html')

def tickets(request):
    context = {}
    return render(request, '2026/tickets/tickets.html', context)

def merch(request):
    context = {}
    return render(request, '2026/merch/merch.html', context)
