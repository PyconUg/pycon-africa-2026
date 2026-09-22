from .views import EXPO_SPONSORS_2026, SPONSORS_2026


def sponsors(request):
    return {
        "sponsors_data": SPONSORS_2026,
        "has_sponsors": any(tier["sponsors"] for tier in SPONSORS_2026),
        "expo_sponsors_data": EXPO_SPONSORS_2026,
        "has_expo_sponsors": any(tier["sponsors"] for tier in EXPO_SPONSORS_2026),
    }
