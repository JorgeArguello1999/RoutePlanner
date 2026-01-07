from flask import render_template

# Template directory
TEMPLATES_DIR = 'public/'

def home():
    return render_template(f'{TEMPLATES_DIR}index.html')

def about():
    return render_template(f'{TEMPLATES_DIR}about.html')

def terms():
    return render_template(f'{TEMPLATES_DIR}terms.html')