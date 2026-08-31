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
        "talk_abstract": "Access to safe drinking water remains a critical challenge in rural Nigerian communities, where contamination goes undetected due to lack of laboratory infrastructure and infrequent manual testing. Existing monitoring approaches rely on expensive equipment or constant internet connectivity - neither of which is realistic in low-resource field settings. This work presents an ongoing effort to develop a real-time, internet-free water quality monitoring system that is affordable, deployable, and AI-powered. The system is built around three low-cost sensors: pH, turbidity, and temperature, with a target hardware cost under ₦50,000 per unit. Central to the system is a lightweight Temporal Convolutional Network (TCN) running on a Raspberry Pi Zero, which processes raw sensor readings to detect contamination anomalies in real time. To address the scarcity of labeled data in rural field settings, the model is trained using self-supervised learning, reducing dependence on large annotated datasets. Upon detecting an anomaly, the system triggers SMS-based alerts via a GSM module. The system is currently being evaluated on publicly available water quality datasets with simulated low-cost sensor noise profiles. The expected result is a robust, low-cost monitoring framework that puts real-time contamination detection in the hands of communities that need it most.",
    },
    {
        "name": "Ubaydah Abdulwasiu",
        "talk_category": "GP / Web",
        "talk_abstract": "When a compliance or security team asks:\n\n> “What was the exact state of this invoice on March 3rd at 2:00 PM, and who changed it?”\n\nTraditional CRUD systems struggle to answer reliably. Rows get overwritten, timestamps are modified, and historical truth becomes difficult to verify.\n\nThis poster presents an append-only event sourcing approach for building tamper-evident audit trails in Python. Instead of mutating records in place, every state transition is recorded as an immutable event. Current state becomes a projection of history rather than a mutable database row.\n\nThe poster walks through:\n* Why mutable database patterns fail under audit pressure\n* Designing an append-only event store in PostgreSQL\n* Reconstructing the historical state through event replay\n* Detecting tampering using SHA-256 hash chaining\n* Practical tradeoffs of immutable event architectures\n* Lightweight Python implementations using Pydantic v2, SQLAlchemy Core, asyncpg, dataclasses, and hashlib\n\nThe visual design of the poster is structured around a live event stream timeline inspired by Git history and distributed systems diagrams, helping attendees intuitively understand immutability, projections, and integrity verification.\nThe goal is to provide practical engineering guidance for systems where historical integrity matters — particularly fintech, audit, compliance, and security-sensitive applications.",
    },
    {
        "name": "Chidera Frankie",
        "talk_category": "ET",
        "talk_abstract": "Building payment systems for African markets comes with challenges that most tutorials ignore. How to split a single transaction across multiple sellers, credit wallets in real time, and handle the inevitable failed or delayed webhook from Paystack. This poster walks through the architecture of BookLoop, a second-hand book marketplace built for the Nigerian market, as a case study for multi-vendor payment infrastructure in Python. Using Paystack as the payment provider, we explore how a single buyer payment triggers a chain of backend logic: fee deduction, seller wallet crediting, and withdrawal processing. Python code snippets illustrate each step from webhook verification to wallet balance updates giving attendees a practical blueprint they can adapt for their own platforms. Whether you're building a marketplace, a fintech product, or any application where money moves between multiple parties, this poster gives you the mental model and the code patterns to get it right.",
    },
    {
        "name": "Chintu Simweene",
        "talk_category": "Education",
        "talk_abstract": "Impact of Outdated Curriculum and Limited Technology Integration on Student Learning Outcomes in Zambian Medical Universities\n\nZambia's medical education system continues to face significant structural challenges rooted in colonial-era curricular frameworks and unequal access to educational technology. Despite increasing global adoption of Technology-Enhanced Learning (TEL), many medical universities in Zambia—particularly in rural regions—still struggle with limited digital infrastructure, inadequate faculty training, unreliable internet connectivity, and unsustainable technology implementation models.\n\nThis study investigates how outdated curricula and limited technology integration collectively affect student learning outcomes, graduate competence, and healthcare workforce preparedness across Zambian medical universities. Using a mixed-methods convergent parallel design, the research combines quantitative surveys with qualitative interviews and focus group discussions involving final-year medical students, faculty members, and recent graduates from both urban and rural institutions.\n\nThe study explores curriculum relevance, technological inequities, and barriers to TEL adoption, including infrastructural limitations, funding instability, and gaps in competency-based pedagogy training. Findings are expected to demonstrate how curricular misalignment and digital inequity contribute to poor clinical preparedness, reduced engagement with virtual learning tools, and continued healthcare workforce migration.\n\nThe project further proposes context-sensitive recommendations for curriculum reform, sustainable digital learning ecosystems, faculty capacity building, and equitable educational policy implementation aligned with Zambia's National Health Strategic Plan and broader Sustainable Development Goals (SDGs).\n\nThis poster contributes to ongoing discussions at the intersection of education, healthcare and technology by highlighting how Python-driven educational technologies, digital health systems, data-informed policy design, and low-resource innovation can support more resilient and equitable medical education systems across Africa.",
    },
    {
        "name": "Seun Olufemi",
        "talk_category": "GC",
        "talk_abstract": "Bioinformatics is growing fast — but in Nigeria, over 60% of aspiring bioinformaticians lack access to structured training, computational tools, and research infrastructure. This poster presents the work of Bioinformatics Outreach Nigeria (BON), a grassroots initiative using Python and open source tools to bridge that gap through a sustainable Community of Practice.\nBON ran two workshop iterations. In 2024, 48 participants were trained from 232 applicants. In 2025 — supported by the Society of Research Software Engineering and the Open Life Science Resident Fellowship — the program attracted nearly 1,000 applications, trained 60 participants, and provided mobile-data support to 45 Nigeria-based attendees to reduce access barriers. Sessions covered Git/GitHub workflows, FAIR data principles, open repositories, licensing, and reproducible research, facilitated by experts from OLS, DataCite, the Carpentries, and the Open Bioinformatics Foundation. Pre- and post-training assessments showed significant knowledge gains across both cohorts.\nThis poster offers a practical framework for Python practitioners and community builders in research or education contexts: how to onboard non-technical scientists into open source workflows, design sustainable community infrastructure (Code of Conduct, contributor pathways, open licensing), and overcome real-world barriers like connectivity constraints and cultural hesitancy around sharing work-in-progress.",
    },
    {
        "name": "Tariq Ahmed Morio",
        "talk_category": "GC",
        "talk_abstract": "This poster presents a community-led education initiative from rural Sindh, Pakistan, focused on supporting underprivileged students through free academic assistance and informal learning support. The project addresses educational inequality by working directly with students who lack access to quality schooling and learning resources.\n\nA key focus of this initiative is exploring how Python programming and open-source digital tools can be introduced at a basic level in low-resource environments. The goal is to promote early digital literacy and demonstrate how simple technology can enhance learning, teaching, and problem-solving skills.\n\nThe poster highlights the real challenges faced in rural education systems, including limited infrastructure, lack of trained educators, and minimal exposure to technology. It also presents practical, scalable, community-driven solutions that can help bridge this gap without requiring high-cost infrastructure.\n\nThe long-term vision of this work is to integrate basic programming and digital skills into community education centers, enabling students to develop future-ready competencies and improve their academic and career opportunities.",
    },
    {
        "name": "Muyomba William",
        "talk_category": "GC",
        "talk_abstract": "1: Background & Problem\nThe Challenge: Deaf and hard-of-hearing youth in Uganda face severe systemic barriers to education, vocational training, and conventional employment, leading to economic exclusion.\nThe Opportunity: Uganda's abundant local agricultural products remain an untapped opportunity for market value addition.\n\n2: The Innovation (Bake and Sign)\nBased in Kira Town, this project solves both challenges through a dual impact model\nInclusive Technical Training Delivers tailored culinary and hospitality training structured for deaf learners through visual methodologies and sign language.\nAgricultural Value Addition. Innovates baking recipes by substituting imported wheat with local Ugandan staples (matooke, cassava, and bananas) supporting local farmers while reducing production costs.\n\n3: Objectives & Expected Impact\n1. Skill Acquisition: Train and certify deaf youth in professional baking, food safety, and micro-business management.\n2. Employment Creation: Provide direct jobs at our flagship bakery and mentor graduates to launch independent micro-enterprises.\n3. Community Advocacy: Break down social stigmas by establishing a community hub where hearing and deaf patrons naturally interact.\n\n4: Poster Delivery\nOur poster visually illustrates:\nThe step-by-step framework of our vocational curriculum.\nOur local-crop product innovation.\nThe scalable socio-economic impact of inclusive entrepreneurship in Uganda.\n\nSummary: Bake and Sign empowers deaf youth in Uganda through inclusive culinary training and local agricultural value addition, promoting economic inclusion and social integration.",
    },
    {
        "name": "Victor Egbe",
        "talk_category": "ET",
        "talk_abstract": "This poster presents VisionX AI, a sustainability-focused initiative exploring smarter ways to improve access to clean energy and clean water in communities. The project highlights how technology-driven solutions can support environmental protection, reduce waste, and provide practical alternatives for everyday energy and water challenges.\nThe poster explains the inspiration behind the idea, the problem it aims to solve, and the proposed approach for building affordable and scalable systems that can benefit underserved areas. It also shows how innovation, sustainability, and community impact can work together to support global development goals, especially in the areas of clean energy, clean water, and climate action.\nThe target audience includes students, researchers, innovators, sustainability advocates, organizations, and anyone interested in renewable energy, environmental solutions, and technology for social impact.",
    },
    {
        "name": "Glory Bagai",
        "talk_category": "ET",
        "talk_abstract": "Predictive Maintenance (PdM) helps industries detect equipment faults before failure occurs, reducing downtime and maintenance costs. However, industrial datasets are often imbalanced because fault cases occur less frequently than normal operations, making accurate prediction difficult. This study benchmarks 4 ML classifiers (Logistic Regression, Random Forest, SVM, and XGBoost) for binary fault detection in rotating industrial machinery across 7,672 real-time sensor readings. To address class imbalance (~90% normal, 10% fault), a stacking ensemble combining SVM, Random Forest, and XGBoost under a Logistic Regression meta-learner is proposed. The ensemble achieved 98.37% accuracy, F1 of 91.35, and AUC of 0.987, outperforming all individual classifiers. SHAP analysis identified temperature and pressure as dominant fault predictors, providing a deployable foundation for Industry 4.0 predictive maintenance in the Nigerian industry.",
    },
    {
        "name": "Abubakar Muktar",
        "talk_category": "ET",
        "talk_abstract": "GreenChild is an AI-powered community health surveillance platform built to stop climate-driven malaria outbreaks before they kill children.\n\nThe core insight: by the time a child arrives at a clinic with malaria, 5–10 children in the same compound already have symptoms. Mothers see this signal days earlier — but no system has ever captured it. GreenChild does.\n\nThis poster walks through how Python and FastAPI power GreenChild's AI risk engine, which fuses mother-reported symptoms (collected via WhatsApp/USSD — no smartphone needed) with hyperlocal rainfall and temperature data from NASA's CHIRPS API to compute a real-time outbreak risk score per ward, updated every 24 hours.\n\nKey technical topics covered:\n- Designing a lightweight Python/FastAPI ML pipeline for low-resource environments\n- Integrating open climate datasets (NASA CHIRPS) with community-generated health signals\n- Building for USSD and WhatsApp — reaching mothers on basic 2G phones\n- Visualising geospatial health risk data with Leaflet.js\n\nThe pilot targets 5 LGAs across Katsina and Kano — two of Nigeria's highest malaria burden states. The architecture is designed to scale to 10 million mothers across West and Central Africa.",
    },
    {
        "name": "Faruq Afolabi",
        "talk_category": "ET",
        "talk_abstract": "MobileCrop is a complete TinyML system for offline crop disease diagnosis targeting smallholder farmers in Sub-Saharan Africa. Using knowledge distillation from EfficientNetB0 to MobileNetV2, the student model achieves 83.81% test accuracy across 17 disease classes, marginally exceeding the teacher. Full INT8 quantization produces a 2.74 MB deployment binary for a production native Android application named Crop Doctor, built in Kotlin with TensorFlow Lite. A companion Progressive Web App delivers Float16 and Dynamic-Range TFLite variants achieving 92.67% accuracy at 2.55 MB. The poster covers the Python training pipeline, the quantization accuracy paradox where INT8 collapsed to 23.67% due to missing calibration data while Float16 gained 9 percentage points, per-class performance across three crops, and field testing results on real Nigerian farm photographs. MobileCrop is the first multi-crop TinyML diagnostic system for West African agriculture deployed as a production Android application.",
    },
    {
        "name": "Francis Bogere",
        "talk_category": "GC",
        "talk_abstract": "Across many African regions, telecom field operations and infrastructure deployment teams often operate in environments with unstable internet connectivity and limited digital tooling. This creates challenges in reporting, infrastructure maintenance, monitoring, and coordination.\n\nThis poster presents the concept and architecture of offline-first telecom field systems built using Python and open technologies. It explores how lightweight applications, local-first data storage, synchronization workflows, and automation tools can improve operational efficiency for field engineers and community connectivity projects.\n\nThe poster also discusses the broader role of open-source technologies in supporting African digital infrastructure, particularly in underserved and rural communities where resilient software systems are critical.\n\nThe work draws inspiration from ongoing experimentation around telecom operations tooling, field data systems, and community-focused connectivity initiatives in East Africa.",
    },
    {
        "name": "Moses Cursor Ssebunya",
        "talk_category": "GC",
        "talk_abstract": "# Code Alone Doesn't Build Developers\n## The Role of Community in Growing Creatives and Technologists\n\nTechnology skills can be learned individually, but sustainable growth rarely happens in isolation. Communities play a critical role in shaping developers and creatives by providing mentorship, collaboration opportunities, accountability, exposure, and a sense of belonging.\n\nThis poster explores how open-source and technology communities contribute to personal and professional growth for both developers and creatives. Drawing from experiences within local and global tech ecosystems, including WordPress communities, meetups, contributor teams, and mentorship spaces, the poster demonstrates how participation in communities accelerates learning and creates opportunities that many people would never access alone.\n\nThe poster highlights how communities help individuals:\n- Build confidence\n- Develop technical and soft skills\n- Find mentors and collaborators\n- Access global opportunities\n- Discover purpose and belonging\n- Transition from consumers to contributors\n\nSpecial attention is given to emerging ecosystems like Uganda, where community-driven learning often bridges gaps in access to traditional opportunities. The poster also emphasizes that thriving technology ecosystems are not built by developers alone, but also by designers, organizers, writers, educators, and other creatives.\n\nThrough storytelling, visuals, and contribution journeys, this poster encourages attendees to intentionally participate in and invest in healthy tech communities as a foundation for innovation, inclusion, and long-term growth.\n\n**Core message:**\nPeople grow faster where they feel seen, supported, and connected.",
    },
    {
        "name": "Daniel Oloki",
        "talk_category": "GP / Web",
        "talk_abstract": "SolarEdu is a smart energy monitoring and analytics platform developed using Python to help educational institutions improve energy efficiency and sustainability. Many schools and universities across Africa experience high electricity costs, unreliable power supply, and limited visibility into energy usage patterns.\n\nThe project integrates Python-based data collection, IoT sensors, solar power analytics, and web dashboards to monitor electricity consumption in real time. The system provides automated reports, predictive maintenance alerts, and usage visualization tools that support better decision-making for administrators and technical teams.\n\nThe poster demonstrates:\n- Real-time energy monitoring using Python\n- Solar system analytics and reporting\n- Web dashboard integration\n- Data visualization and automation\n- Sustainable technology solutions for education\n\nThe project highlights how Python can be applied beyond software engineering into practical infrastructure management, sustainability, and smart-campus innovation across Africa.",
    },
    {
        "name": "Joy Olusanya",
        "talk_category": "O",
        "talk_abstract": "Large language models (LLMs) and Neural Machine Translation (NMT) systems have demonstrated strong performance across a wide range of translation tasks. However, translating culturally grounded content such as idiomatic expressions remains a persistent challenge due to their non-compositional nature. This challenge is particularly pronounced in low-resource African languages such as Yoruba, where idioms carry deep cultural meaning yet remain underrepresented in machine translation research. In this study, we evaluate three models: GPT-4o mini, Qwen2.5-7B-Instruct, and NLLB-200 on Yoruba-to-English idiom translation. We examine direct machine translation as well as zero-shot and few-shot prompting strategies using a curated dataset of Yoruba idioms annotated with their literal meanings and corresponding English idiomatic equivalents. Evaluation is conducted using BLEU, chrF+, and BERTScore F1, alongside human evaluation based on adequacy, fluency, and preservation of literal meaning. The results show that GPT-4o mini performs best overall, particularly in the zero-shot and few-shot settings, according to the chrF+ metric. Notably, GPT-4o mini consistently achieves the highest scores for literal meaning across all models in human evaluation. This suggests a tendency for LLMs to default to literal translations when handling culturally grounded expressions. These findings highlight the limitations of current translation models in capturing figurative and pragmatic meaning, and underscore the need for culturally grounded corpora for low-resource African languages, particularly Yoruba, to support the preservation of cultural identity in language technologies.",
    },
    {
        "name": "Justice Ohene Amofa",
        "talk_category": "ET",
        "talk_abstract": "Machine learning is increasingly used in medical diagnostics, but many models remain difficult to reproduce, interpret, or deploy in real-world systems.\nThis work presents a Python-based deep learning pipeline for tuberculosis detection using chest X-ray images combined with multivariate patient data, including age, comorbidities, socioeconomic indicators, and radiological features.\nThe system is implemented using a modular Python ML stack and integrates transfer learning, classical machine learning models, and explainable AI techniques.\nKey components include:\nA deep learning pipeline built on a pre-trained ResNet50 backbone with custom classification layers\nClassical ML models (SVM, decision trees) for comparative evaluation\nA dataset of 4,800 chest X-ray images used for training and validation\nPerformance metrics including Accuracy (~99%), Precision (100% TB class), F1-score (~0.9787), and AUC (~0.9989)\nExplainable AI methods to improve interpretability and clinical trust\nA Streamlit-based interface for interactive inference and deployment\nThe architecture follows a standard Python ML workflow:\nData preprocessing and normalization\nFeature integration across clinical and imaging modalities\nModel training, evaluation, and validation\nLightweight deployment using Python web tooling\nBeyond the current system, the project is designed to be modular and extensible for multimodal expansion, including the incorporation of additional imaging modalities such as ocular/eye-based visual biomarkers in future iterations. This reflects a broader direction toward multi-source diagnostic intelligence systems.\nWe also discuss important real-world limitations, particularly domain shift in TB presentation across regions (e.g., Mycobacterium africanum prevalence in West Africa), emphasizing the need for regionally representative datasets and retraining strategies.\nOverall, the work focuses on:\nReproducible ML pipeline design in Python\nBridging research-grade models and deployable tools\nExplainable AI for healthcare trust and usability\nPractical constraints in low-resource deployment environments\nProject Links\nGitHub: https://github.com/iamamofa/TB-detection",
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
