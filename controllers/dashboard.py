from flask import render_template

# Template directory
TEMPLATES_DIR = 'map/'

def home():
    return render_template(f'{TEMPLATES_DIR}dashboard.html')