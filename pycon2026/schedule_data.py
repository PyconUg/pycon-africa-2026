import os
import re

E = {"title": "", "speaker": ""}


SCHEDULE_DATA = [
    {
        "id": "day1",
        "label": "Wed, Oct 7 — Workshops & PyData Summit",
        "rooms": ["Victoria Ball Room", "Majestic Hall", "Royal Hall", "Regal Hall"],
        "slots": [
            {"time": "7:00 – 8:45", "span": True, "title": "Break Tea", "type": "break"},
            {"time": "9:00 – 11:00", "cells": [
                E,
                {"title": "The Essence of Data Visualisation: Mapping from Data to Visual Properties", "speaker": "Hassan Kibirige"},
                {"title": "PyData Summit", "speaker": ""},
                {"title": "Sponsor Workshops", "speaker": ""},
            ]},
            {"time": "11:00 – 13:00", "cells": [
                E,
                {"title": "Build and deploy an ADK agent on Cloud Run", "speaker": "Alouzeh Brandone Mahbuh, Samuel Macharia"},
                {"title": "PyData Summit", "speaker": ""},
                {"title": "Sponsor Workshops", "speaker": ""},
            ]},
            {"time": "13:00 – 14:00", "span": True, "title": "Lunch", "type": "break"},
            {"time": "14:00 – 16:00", "cells": [
                E,
                {"title": "Computer Vision in 10 Lines of Code: Rapid Prototyping with FastAI", "speaker": "Victor Olufemi"},
                {"title": "PyData Summit", "speaker": ""},
                {"title": "Sponsor Workshops", "speaker": ""},
            ]},
            {"time": "16:00 – 18:00", "cells": [
                E,
                {"title": "Building Your First RESTful API", "speaker": "Anthony Addae"},
                {"title": "PyData Summit", "speaker": ""},
                {"title": "Sponsor Workshops", "speaker": ""},
            ]},
        ],
    },
    {
        "id": "day2",
        "label": "Thu, Oct 8 — Workshops & WiDs",
        "rooms": ["Victoria Ball Room", "Majestic Hall", "Royal Hall", "Regal Hall"],
        "slots": [
            {"time": "7:00 – 8:45", "span": True, "title": "Break Tea", "type": "break"},
            {"time": "9:00 – 11:00", "cells": [
                E,
                {"title": "Demystifying Robotics & IoT with MicroPython", "speaker": "Zenas Awuku"},
                {"title": "Humble Data workshop", "speaker": "Cecilia Tivir"},
                {"title": "WiDs", "speaker": "", "link": "/2026/co-events/women_in_data_science/#program-schedule"},
            ]},
            {"time": "11:00 – 13:00", "cells": [
                E,
                {"title": "LLMs Expert Session", "speaker": "GDEs"},
                {"title": "Securing Django 6.0 Apps with Built-in Content Security Policy", "speaker": "Kiringabakwe Ibrahim"},
                {"title": "WiDs", "speaker": "", "link": "/2026/co-events/women_in_data_science/#program-schedule"},
            ]},
            {"time": "13:00 – 14:00", "span": True, "title": "Lunch", "type": "break"},
            {"time": "14:00 – 16:00", "cells": [
                E,
                {"title": "Hands-On: Building an AI Agent with Python to Detect Risky Customers", "speaker": "Hussein Kizza"},
                {"title": "Building Pearl-Chat: Overcoming the Technical Challenges of Architecting a Native Luganda LLM in Pure JAX", "speaker": "Wesley Kambale"},
                {"title": "WiDs", "speaker": "", "link": "/2026/co-events/women_in_data_science/#program-schedule"},
            ]},
            {"time": "16:00 – 18:00", "cells": [
                E,
                {"title": "SQLAlchemy: the Swiss Army Knife of Databases for Python", "speaker": "ZOKORA ELVIS GBAGNON"},
                {"title": "CPython Internals", "speaker": "Lincoln Angufibo"},
                E,
            ]},
        ],
    },
    {
        "id": "day3",
        "label": "Fri, Oct 9 — Conference Day 1",
        "rooms": [
            "Victoria Ball Room",
            "Majestic Hall",
            "Royal Hall",
            "Regal Hall",
        ],
        "slots": [
            {"time": "7:00 – 8:45", "span": True, "title": "Break Tea", "type": "break"},
            {"time": "9:00 – 9:15", "span": True, "title": "Opening Remarks"},
            {"time": "9:15 – 10:15", "span": True, "title": "Opening Keynote"},
            {"time": "10:20 – 11:05", "cells": [
                {"title": "Automating Hardware Diagnostics: Resurrecting Motherboards with Python and a Raspberry Pi", "speaker": "Collins Mesue", "label": "Talk · AI/ML"},
                {"title": "MLOPs with MLFLow (A Value Estimation Example)", "speaker": "Ronald Matovu", "label": "Talk · AI/Agentic"},
                {"title": "Django Girls Workshop", "speaker": ""},
                {"title": "Community Summit", "speaker": ""},
            ]},
            {"time": "11:10 – 11:55", "cells": [
                {"title": "Getting started with mechanistic interpretability", "speaker": "Rashid Kisejjere", "label": "Talk · AI/ML"},
                {"title": "GenAI Inside: Embedding AI into Enterprise Workflows with Python", "speaker": "Muhammad Aliyu", "label": "Talk · AI/Agentic"},
                {"title": "Django Girls Workshop", "speaker": ""},
                {"title": "Community Summit", "speaker": ""},
            ]},
            {"time": "12:00 – 12:45", "cells": [
                {"title": "CPython Under Load: NoGIL, Green Threads, AsyncIO vs Other Langs — Deep-Dive and Benchmarks", "speaker": "Petr Andreev", "label": "Talk · AI/ML"},
                {"title": "Mastering Deep Learning: One Python Script at a Time", "speaker": "Charles Moruri", "label": "Talk · AI/Agentic"},
                {"title": "Django Girls Workshop", "speaker": ""},
                {"title": "Community Summit", "speaker": ""},
            ]},
            {"time": "12:50 – 13:00", "span": True, "title": "Sponsor Plenary Talk"},
            {"time": "13:00 – 14:00", "span": True, "title": "Lunch", "type": "break"},
            {"time": "14:05 – 14:50", "cells": [
                {"title": "Turning Food into Medicine with Local LLMs: The Future of Chronic Disease Management", "speaker": "Daniel Samuel Etukudo", "label": "Talk · AI/ML"},
                {"title": "From Hospital Records to REST API: Training and Serving XGBoost Disease Prediction Models in Python", "speaker": "Ernest Essien", "label": "Talk · AI/Agentic"},
                {"title": "Django Girls Workshop", "speaker": ""},
                {"title": "Community Summit", "speaker": ""},
            ]},
            {"time": "14:55 – 15:40", "cells": [
                {"title": "The Mathematical Representation of Vision: From Linear Algebra to Deepfake Detection", "speaker": "Mark Lubega", "label": "Talk · AI/ML"},
                {"title": "From Zero to GPU: Serverless ML Inference on a Budget with Modal and Python", "speaker": "Arnold Ighiwiyisi", "label": "Talk · AI/Agentic"},
                {"title": "Django Girls Workshop", "speaker": ""},
                {"title": "Community Summit", "speaker": ""},
            ]},
            {"time": "15:50 – 16:50", "span": True, "title": "Closing Keynote\nBuilding the Agentic Future with Google Antigravity\nJohn Kimani, Developer Ecosystem Lead for Sub-Saharan Africa, Google"},
            {"time": "16:50 – 17:20", "span": True, "title": "Lightning Talks"},
        ],
    },
    {
        "id": "day4",
        "label": "Sat, Oct 10 — Conference Day 2",
        "rooms": [
            "Victoria Ball Room",
            "Majestic Hall",
            "Royal Hall",
            "Regal Hall",
            "Pavilion",
        ],
        "slots": [
            {"time": "7:00 – 8:45", "span": True, "title": "Break Tea", "type": "break"},
            {"time": "9:00 – 9:15", "span": True, "title": "Opening Remarks"},
            {"time": "9:15 – 10:15", "span": True, "title": "Opening Keynote\nBuilding AI-Powered Lending Infrastructure (Chris Orwa)"},
            {"time": "10:20 – 11:05", "cells": [
                {"title": "Let the Computer Run Your Unit Tests: Property-Based Testing with Hypothesis in Python", "speaker": "Batamye Umar Isabirye", "label": "Talk · Core Python"},
                {"title": "Building Real-Time Voice Agents That Listen and Respond in Python", "speaker": "Glory Bagai", "label": "Talk · AI/Agentic"},
                {"title": "Python in the Browser: No install, No barrier", "speaker": "Hypolit Zeuchieu", "label": "Talk · Security/Web"},
                {"title": "Pyladies Africa", "speaker": "Ruvimbo Delia Hakata, Adeline Makokha, Blossom Dugbatey", "link": "/2026/co-events/pyladies/", "no_link": True},
                {"title": "Posters", "speaker": "", "link": "/2026/schedule/accepted-posters/"},
            ]},
            {"time": "11:10 – 11:40", "cells": [
                {"title": "Working with Audio in Python (Pythonic Approach)", "speaker": "Bashir Kasujja", "label": "Short Talk · Core Python"},
                {"title": "Detecting Firmware Implants with Python Assisted Bare-Metal Forensics", "speaker": "Arrhat Nag", "label": "Short Talk · AI/Agentic"},
                {"title": "Enhancing FastMCP Server Security", "speaker": "Mugoya Hillarious", "label": "Short Talk · Security/Web"},
                {"title": "Pyladies Africa", "speaker": "Ruvimbo Delia Hakata, Adeline Makokha, Blossom Dugbatey", "link": "/2026/co-events/pyladies/", "no_link": True},
                {"title": "Posters", "speaker": "", "link": "/2026/schedule/accepted-posters/"},
            ]},
            {"time": "11:45 – 12:15", "cells": [
                {"title": "Python for Microcontrollers: Introduction to MicroPython & Wokwi Simulator", "speaker": "Samuel Lunghe", "label": "Short Talk · Core Python"},
                {"title": "Building Event-Driven Systems in Python That Survive Production", "speaker": "Abdulmateen Tairu", "label": "Short Talk · AI/Agentic"},
                {"title": "Python at Scale: A Practical Guide to Serving 1 Million Users with FastAPI and Flask", "speaker": "Moses Daudu", "label": "Short Talk · Security/Web"},
                {"title": "Pyladies Africa", "speaker": "Ruvimbo Delia Hakata, Adeline Makokha, Blossom Dugbatey", "link": "/2026/co-events/pyladies/", "no_link": True},
                {"title": "Posters", "speaker": "", "link": "/2026/schedule/accepted-posters/"},
            ]},
            {"time": "12:20 – 13:00", "span": True, "title": "Open Source, Research and Industry Panel"},
            {"time": "13:00 – 14:00", "span": True, "title": "Lunch", "type": "break"},
            {"time": "14:05 – 14:35", "cells": [
                {"title": "Deterministic Python: Implementing RTOS Design Concepts in MicroPython", "speaker": "Shawal Mbalire", "label": "Short Talk · Core Python"},
                {"title": "Designing Python APIs for Data You Don't Control", "speaker": "Saurav Jain", "label": "Short Talk · AI/Agentic"},
                {"title": "When Step 3 Fails: Reliable Multi-Step Workflows in Celery Using the Saga Pattern", "speaker": "Douglas Amoo-Sargon", "label": "Short Talk · Security/Web"},
                {"title": "Pyladies Africa", "speaker": "Ruvimbo Delia Hakata, Adeline Makokha, Blossom Dugbatey", "link": "/2026/co-events/pyladies/", "no_link": True},
                {"title": "Posters", "speaker": "", "link": "/2026/schedule/accepted-posters/"},
            ]},
            {"time": "14:40 – 15:10", "cells": [
                {"title": "Building Low-Power IoT Systems with LoRaWAN and Python", "speaker": "Job mbugua", "label": "Short Talk · Core Python"},
                E,
                {"title": "Async Python and FastAPI: How It Actually Works", "speaker": "Theresa Seyram Agbenyegah", "label": "Short Talk · Security/Web"},
                {"title": "Pyladies Africa", "speaker": "Ruvimbo Delia Hakata, Adeline Makokha, Blossom Dugbatey", "link": "/2026/co-events/pyladies/", "no_link": True},
                {"title": "Posters", "speaker": "", "link": "/2026/schedule/accepted-posters/"},
            ]},
            {"time": "15:15 – 15:45", "cells": [
                {"title": "Back to the Fixtures", "speaker": "Steve Yonkeu", "label": "Short Talk · Core Python"},
                {"title": "Advanced Design Patterns for ML Systems", "speaker": "Victor Ashioya", "label": "Short Talk · AI/Agentic"},
                {"title": "Delivering with Django: Boring Tech, Real Impact in Africa's Startups", "speaker": "Bernard Katamanso", "label": "Short Talk · Security/Web"},
                {"title": "Pyladies Africa", "speaker": "Ruvimbo Delia Hakata, Adeline Makokha, Blossom Dugbatey", "link": "/2026/co-events/pyladies/", "no_link": True},
                {"title": "Posters", "speaker": "", "link": "/2026/schedule/accepted-posters/"},
            ]},
            {"time": "15:50 – 16:50", "span": True, "title": "Closing Keynote"},
            {"time": "16:50 – 17:20", "span": True, "type": "lightning", "title": "Lightning Talks", "talks": [
                {"title": "Django Deployment Isn't What It Used to Be.", "speaker": "Victoria Nyamai"},
                {"title": "Using Python to Automate API Testing in Open Source Projects", "speaker": "Clency Christine"},
                {"title": "Securing Networks with Python: A Deep Dive into Intrusion Detection, Phishing Prevention, and Vulnerability Scoring", "speaker": "Alpha Lee Munene"},
                {"title": "What Nobody Tells You About Running a Developer Community as a Student", "speaker": "Bernard Katamanso"},
                {"title": "The Informal Economy Doesn't Have an API", "speaker": "John Pangara"},
                {"title": "Design isn't just for the Frontend: Why backend developers should care about UX.", "speaker": "Angella Miriam Birungi"},
            ]},
        ],
    },
    {
        "id": "day5",
        "label": "Sun, Oct 11 — Conference Day 3",
        "footnote": "★ Remote session",
        "rooms": [
            "Victoria Ball Room",
            "Majestic Hall",
            "Royal Hall",
            "Regal Hall",
        ],
        "slots": [
            {"time": "7:00 – 8:45", "span": True, "title": "Break Tea", "type": "break"},
            {"time": "9:00 – 9:15", "span": True, "title": "Opening Remarks"},
            {"time": "9:15 – 10:15", "span": True, "title": "Opening Keynote\nA Decade of Language AI: A Reflection on the Insanity (Jade Abbot)"},
            {"time": "10:20 – 11:05", "cells": [
                {"title": "Hacking for Good: Cybersecurity and Ethical Hacking with Python", "speaker": "Mvenyi Donald Mbutu", "label": "Talk · Security/Web"},
                {"title": "The Lazy Wizard's Guide to Federated Learning: Building ML Models in Difficult Places", "speaker": "Johannes Kolbe", "label": "Talk · ML/Data Science"},
                {"title": "From Single Agents to Production Teams: Building Multi-Agent Systems with Python, MCP, and Persistent Memory", "speaker": "David Agbolade", "label": "Talk · AI/Agentic"},
                {"title": "Refugee Program", "speaker": "", "link": "/2026/co-events/persons_of_concern/#workshop-schedule"},
            ]},
            {"time": "11:10 – 11:40", "cells": [
                {"title": "Breaking Bad in Python: A Chaos Engineering Story", "speaker": "Joyce Dzifa Lokko", "label": "Short Talk · Security/Web"},
                {"title": "V-MATH and Veri-Math: Step Level Verification for Enhancing Mathematical Reasoning in Large Language Models", "speaker": "John Paul Rugaba Rugaba", "label": "Short Talk · ML/Data Science"},
                {"title": "Designing Python-First AI Programs for African Universities: A Practical Framework", "speaker": "Elvira Khwatenge", "label": "Short Talk · AI/Agentic"},
                {"title": "Refugee Program", "speaker": "", "link": "/2026/co-events/persons_of_concern/#workshop-schedule"},
            ]},
            {"time": "11:45 – 12:15", "cells": [
                {"title": "How I Used Python to Control Kubernetes with Voice Notes on Telegram", "speaker": "Daniel Mwiine", "label": "Short Talk · Security/Web"},
                {"title": "Federated Learning as a Distributed Systems Problem: Designing Production-Grade ML Systems in Python", "speaker": "David Asem", "label": "Short Talk · ML/Data Science"},
                {"title": "Speech Synthesis Unpacked: Building a Voice Cloning TTS Model with Python", "speaker": "Nunsi Shiaki", "label": "Short Talk · AI/Agentic"},
                {"title": "Refugee Program", "speaker": "", "link": "/2026/co-events/persons_of_concern/#workshop-schedule"},
            ]},
            {"time": "12:20 – 13:00", "cells": [
                {"title": "Dedicated Expo Hall Time", "speaker": ""},
                {"title": "Dedicated Expo Hall Time", "speaker": ""},
                {"title": "Dedicated Expo Hall Time", "speaker": ""},
                {"title": "Refugee Program", "speaker": "", "link": "/2026/co-events/persons_of_concern/#workshop-schedule"},
            ]},
            {"time": "13:00 – 14:00", "span": True, "title": "Lunch", "type": "break"},
            {"time": "14:05 – 14:35", "cells": [
                {"title": "Delivering with Django: Boring Tech, Real Impact in Africa's Startups", "speaker": "Bernard Katamanso", "label": "Short Talk · Security/Web"},
                {"title": "Continuous translation with Weblate in the age of AI", "speaker": "Gersona Andrianarijaona", "label": "Short Talk · ML/Data Science"},
                {"title": "Deploying Intelligence at the Edge: Building Real-World Perception Systems with Python on Constrained Hardware", "speaker": "Obed Honour Eje", "label": "Short Talk · AI/Agentic"},
                {"title": "Refugee Program", "speaker": "", "link": "/2026/co-events/persons_of_concern/#workshop-schedule"},
            ]},
            {"time": "14:40 – 15:10", "cells": [
                {"title": "PaSSw0rdVib3s!: Finding Passwords in Digital Evidence", "speaker": "Anne Fleur van Luenen", "label": "Short Talk · Security/Web"},
                {"title": "Building Clinical Tools in Data-Constrained Environments: Python, ML, and the Human Spine", "speaker": "Christine Akoto-Nimoh", "label": "Short Talk · ML/Data Science"},
                {"title": "Trust Is a Dependency: Securing the Modern Software Supply Chain", "speakers": [{"name": "Famious Orishaba"}, {"name": "Tabitha Namwone"}], "label": "Tutorial"},
                {"title": "Refugee Program", "speaker": "", "link": "/2026/co-events/persons_of_concern/#workshop-schedule"},
            ]},
            {"time": "15:15 – 15:45", "cells": [
                {"title": "Background Jobs at Scale: Designing Reliable Python Worker Systems", "speaker": "Efe Omoregie", "label": "Short Talk · Security/Web"},
                {"title": "Building Civic Tech with Python: APIs, Data, and Systems for Public Good", "speaker": "Alamin Magaga", "label": "Short Talk · ML/Data Science"},
                {"title": "Trust Is a Dependency: Securing the Modern Software Supply Chain", "speakers": [{"name": "Famious Orishaba"}, {"name": "Tabitha Namwone"}], "label": "Tutorial"},
                {"title": "Refugee Program", "speaker": "", "link": "/2026/co-events/persons_of_concern/#workshop-schedule"},
            ]},
            {"time": "15:50 – 16:50", "span": True, "title": "Closing Keynote\nThe Evolution of Python: Lessons from Its Creator (Guido van Rossum)", "star": True},
            {"time": "16:50 – 17:20", "span": True, "type": "lightning", "title": "Lightning Talks", "talks": [
                {"title": "Your Code is Great...but Who Knows?", "speaker": "Sarah Muwanguzi"},
                {"title": "Python for Impact: Building Climate Solutions Rooted in African Communities", "speaker": "Tendai Jack"},
                {"title": "Open Source Is Infrastructure. Why We Must Stop Treating It Like a Hobby", "speaker": "Gertrude Abagale Abagale"},
                {"title": "Python for Community Impact: Simple Tech Solutions for Refugee and Rural Communities in Africa", "speaker": "Makala Sankara Anzuruni"},
            ]},
        ],
    },
]


_SPEAKER_IMAGE_STATIC_DIR = "2026/img/speakerImages"
_SPEAKER_IMAGE_FS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "static", *_SPEAKER_IMAGE_STATIC_DIR.split("/"),
)
_SPEAKER_IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png")


def _normalize_speaker_name(name):
    name = re.sub(r"[_\-]+", " ", name.strip().lower())
    return re.sub(r"\s+", " ", name)


def _build_speaker_image_lookup():
    lookup = {}
    if not os.path.isdir(_SPEAKER_IMAGE_FS_DIR):
        return lookup
    for filename in os.listdir(_SPEAKER_IMAGE_FS_DIR):
        stem, ext = os.path.splitext(filename)
        if ext.lower() not in _SPEAKER_IMAGE_EXTENSIONS:
            continue
        full_path = os.path.join(_SPEAKER_IMAGE_FS_DIR, filename)
        if os.path.getsize(full_path) == 0:
            continue
        lookup[_normalize_speaker_name(stem)] = f"{_SPEAKER_IMAGE_STATIC_DIR}/{filename}"
    return lookup


def _attach_image(entry, lookup, name_key="speaker"):
    name = entry.get(name_key)
    if not name:
        return
    image = lookup.get(_normalize_speaker_name(name))
    if image:
        entry["image"] = image


def _attach_speaker_images(schedule_data):
    lookup = _build_speaker_image_lookup()
    for day in schedule_data:
        for slot in day.get("slots", []):
            for cell in slot.get("cells", []):
                _attach_image(cell, lookup)
                for speaker in cell.get("speakers", []):
                    _attach_image(speaker, lookup, name_key="name")
            for talk in slot.get("talks", []):
                _attach_image(talk, lookup)
    return schedule_data


_attach_speaker_images(SCHEDULE_DATA)
