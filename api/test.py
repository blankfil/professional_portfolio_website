from vercel import Response

def handler(request):
    """Simple test handler"""
    return Response(
        b"Hello from Vercel! Handler is working.",
        status=200,
        headers={'Content-Type': 'text/plain'}
    )
