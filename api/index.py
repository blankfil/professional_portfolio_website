import os
import sys
from pathlib import Path
from io import BytesIO

# Add the project root to Python path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'online.settings')

# Import Django WSGI application
from django.core.wsgi import get_wsgi_application

# Initialize Django app (do this once at module level)
django_app = get_wsgi_application()

def handler(request):
    """Vercel serverless function handler for Django"""
    from vercel import Response
    
    try:
        # Get request details safely with defaults
        method = getattr(request, 'method', 'GET')
        path = getattr(request, 'path', '/')
        query_string = getattr(request, 'query_string', '') or ''
        headers = getattr(request, 'headers', {}) or {}
        body = getattr(request, 'body', b'') or b''
        
        # Handle path - remove leading slash if present for PATH_INFO
        path_info = path if path.startswith('/') else '/' + path
        
        # Build WSGI environ from Vercel request
        host = headers.get('Host', 'localhost')
        server_name = host.split(':')[0] if ':' in host else host
        server_port = host.split(':')[1] if ':' in host else '80'
        
        environ = {
            'REQUEST_METHOD': method,
            'SCRIPT_NAME': '',
            'PATH_INFO': path_info,
            'QUERY_STRING': query_string,
            'CONTENT_TYPE': headers.get('Content-Type', ''),
            'CONTENT_LENGTH': str(len(body)),
            'SERVER_NAME': server_name,
            'SERVER_PORT': server_port,
            'wsgi.version': (1, 0),
            'wsgi.url_scheme': 'https' if headers.get('X-Forwarded-Proto') == 'https' else 'http',
            'wsgi.input': BytesIO(body),
            'wsgi.errors': sys.stderr,
            'wsgi.multithread': False,
            'wsgi.multiprocess': True,
            'wsgi.run_once': False,
        }
        
        # Add HTTP headers to environ (WSGI format)
        for key, value in headers.items():
            key_upper = key.upper().replace('-', '_')
            if key_upper not in ('CONTENT_TYPE', 'CONTENT_LENGTH'):
                environ[f'HTTP_{key_upper}'] = value
        
        # WSGI response variables
        response_status = [None]
        response_headers = []
        
        def start_response(status, headers):
            response_status[0] = status
            response_headers[:] = headers
        
        # Call Django WSGI app
        response_body = django_app(environ, start_response)
        body_bytes = b''.join(response_body)
        
        # Parse status code
        status_code = 200
        if response_status[0]:
            status_code = int(response_status[0].split()[0])
        
        # Convert headers to dict
        headers_dict = {k: v for k, v in response_headers}
        
        return Response(
            body_bytes,
            status=status_code,
            headers=headers_dict
        )
        
    except Exception as e:
        import traceback
        # Return error response for debugging
        error_details = f"Error: {str(e)}\n\nTraceback:\n{traceback.format_exc()}"
        return Response(
            error_details.encode(),
            status=500,
            headers={'Content-Type': 'text/plain; charset=utf-8'}
        )
