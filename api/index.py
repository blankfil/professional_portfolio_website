import os
import sys
from pathlib import Path

# Add the project root to Python path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'online.settings')

# Import Django WSGI application
from django.core.wsgi import get_wsgi_application

django_app = get_wsgi_application()

def handler(request):
    """Vercel serverless function handler for Django"""
    from vercel import Response
    
    # Build WSGI environ from Vercel request
    environ = {
        'REQUEST_METHOD': request.method,
        'SCRIPT_NAME': '',
        'PATH_INFO': request.path,
        'QUERY_STRING': request.query_string or '',
        'CONTENT_TYPE': request.headers.get('Content-Type', ''),
        'CONTENT_LENGTH': str(len(request.body)) if request.body else '',
        'SERVER_NAME': request.headers.get('Host', 'localhost').split(':')[0],
        'SERVER_PORT': request.headers.get('Host', 'localhost').split(':')[1] if ':' in request.headers.get('Host', '') else '80',
        'wsgi.version': (1, 0),
        'wsgi.url_scheme': 'https' if request.headers.get('X-Forwarded-Proto') == 'https' else 'http',
        'wsgi.input': request.body if request.body else b'',
        'wsgi.errors': sys.stderr,
        'wsgi.multithread': False,
        'wsgi.multiprocess': True,
        'wsgi.run_once': False,
    }
    
    # Add HTTP headers
    for key, value in request.headers.items():
        key = key.upper().replace('-', '_')
        if key not in ('CONTENT_TYPE', 'CONTENT_LENGTH'):
            environ[f'HTTP_{key}'] = value
    
    # WSGI response variables
    response_status = [None]
    response_headers = []
    
    def start_response(status, headers):
        response_status[0] = status
        response_headers[:] = headers
    
    # Call Django WSGI app
    response_body = django_app(environ, start_response)
    body = b''.join(response_body)
    
    # Parse status code
    status_code = int(response_status[0].split()[0]) if response_status[0] else 200
    
    # Convert headers to dict
    headers_dict = {k: v for k, v in response_headers}
    
    return Response(
        body,
        status=status_code,
        headers=headers_dict
    )
