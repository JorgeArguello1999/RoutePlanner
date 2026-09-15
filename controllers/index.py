import os
from flask import render_template

# Template directory
TEMPLATES_DIR = 'public/'

def home():
    # Pass demo credentials so UI always shows correct login (from env or defaults)
    return render_template(
        f'{TEMPLATES_DIR}index.html',
        demo_user=os.getenv("ADMIN_USERNAME", "admin"),
        demo_pass=os.getenv("ADMIN_PASSWORD", "Admin123!"),
    )

def about():
    return render_template(f'{TEMPLATES_DIR}about.html')

def terms():
    return render_template(f'{TEMPLATES_DIR}terms.html')