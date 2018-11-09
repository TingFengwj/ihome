#conding:utf-8
from flask import Blueprint, current_app, make_response
from flask_wtf.csrf import generate_csrf

html = Blueprint('html', __name__)


@html.route("/<re(r'.*'):file_name>")
def get_html_file(file_name):
    if not file_name:
        file_name = 'index.html'

    if file_name != 'favicon.ico':
        file_name = 'html/'+ file_name
    csrf_token = generate_csrf()
    resp = make_response(current_app.send_static_file(file_name))
    resp.set_cookie("csrf_token", csrf_token)
    return resp