"""
Middleware to redirect all requests to africa.pycon.org
"""
from django.http import HttpResponsePermanentRedirect
from django.conf import settings


class AppendSlashMiddleware:
    """
    Eagerly redirects any path that lacks a trailing slash to the same path
    with a trailing slash (301)

    This complements Django's APPEND_SLASH / CommonMiddleware behaviour, which
    only redirects when the slash-appended URL resolves to a known pattern.
    Because several routes (e.g. /merch, /tickets) live under the /2026/
    prefix in Django's urlconf but are served without that prefix by the
    web-server layer, CommonMiddleware alone cannot detect the match and
    skips the redirect.  This middleware handles that gap.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path
        # Only act when APPEND_SLASH is enabled (respects project settings)
        if getattr(settings, 'APPEND_SLASH', True):
            last_segment = path.rstrip('/').rsplit('/', 1)[-1]
            if path != '/' and not path.endswith('/') and '.' not in last_segment:
                redirect_url = path + '/'
                if request.GET:
                    redirect_url = f"{redirect_url}?{request.GET.urlencode()}"
                return HttpResponsePermanentRedirect(redirect_url)
        return self.get_response(request)


class RedirectToAfricaMiddleware:
    """
    Middleware that redirects all requests from ug.pycon.org to africa.pycon.org
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check if request is coming from ug.pycon.org
        host = request.get_host()
        
        # Only redirect if host is ug.pycon.org (with or without www)
        if host in ['ug.pycon.org', 'www.ug.pycon.org']:
            redirect_url = f"https://africa.pycon.org{request.path}"
            if request.GET:
                # Preserve query parameters if any
                query_string = request.GET.urlencode()
                redirect_url = f"{redirect_url}?{query_string}"
            
            return HttpResponsePermanentRedirect(redirect_url)
        
        # If no redirect needed, continue with normal request processing
        return self.get_response(request)


class RedirectFromAfricaMiddleware:
    """
    Middleware that redirects specific paths from africa.pycon.org to pyconafrica.pythonanywhere.com
    Handles redirects for:
    - /2024/ => https://pyconafrica.pythonanywhere.com/2024/
    - /2020/ => https://pyconafrica.pythonanywhere.com/2020/
    - /2019/ => https://pyconafrica.pythonanywhere.com/2019/
    """
    REDIRECT_PATHS = ['/2024/', '/2020/', '/2019/']
    TARGET_DOMAIN = 'https://pyconafrica.pythonanywhere.com'
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check if request is coming from africa.pycon.org
        host = request.get_host()
        
        # Check if host is africa.pycon.org (with or without www)
        if host in ['africa.pycon.org', 'www.africa.pycon.org']:
            # Check if path matches any of the redirect paths
            path = request.path
            if path in self.REDIRECT_PATHS or path.startswith('/2024/') or path.startswith('/2020/') or path.startswith('/2019/'):
                redirect_url = f"{self.TARGET_DOMAIN}{path}"
                if request.GET:
                    # Preserve query parameters if any
                    query_string = request.GET.urlencode()
                    redirect_url = f"{redirect_url}?{query_string}"
                
                return HttpResponsePermanentRedirect(redirect_url)
        
        # If no redirect needed, continue with normal request processing
        return self.get_response(request)
