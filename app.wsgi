# ~/public_html/app.wsgi
import os, sys

# Point to your venv (pick the correct one)
VENV = os.path.expanduser('~/venv')  # or '~/your-project/venv'

# (Optional) help mod_wsgi find your venv’s site-packages
activate_this = os.path.join(VENV, 'bin', 'activate_this.py')
if os.path.exists(activate_this):
    with open(activate_this) as f:
        exec(f.read(), {'__file__': activate_this})

# Add your project folder to PYTHONPATH
sys.path.insert(0, os.path.expanduser('~/your-project'))

# Import your Flask app object as "application"
from app import app as application   # change to your real module:app if different
