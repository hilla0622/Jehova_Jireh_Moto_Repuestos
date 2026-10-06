import urllib.request
import json
import ssl

try:
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    # We don't have session cookies, so this might return 401 Unauthorized because of @login_required
    # Let's try it anyway. If it returns 401, at least the route exists.
    url = "http://localhost:5000/api/finanzas/libro_mayor?cuenta_id=1"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, context=ctx) as response:
        html = response.read()
        print("Status:", response.status)
        print("Response:", html.decode('utf-8'))
except urllib.error.HTTPError as e:
    print("HTTPError:", e.code, e.reason)
    print(e.read().decode('utf-8'))
except Exception as e:
    print("Error:", e)
