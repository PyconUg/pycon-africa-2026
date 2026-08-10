from .views import SPONSORS_2026


def sponsors(request):
    return {
        "sponsors_data": SPONSORS_2026,
        "has_sponsors": any(tier["sponsors"] for tier in SPONSORS_2026),
    }
