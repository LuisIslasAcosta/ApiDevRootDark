from flask import Blueprint

blueprint_home = Blueprint('blueprint',__name__)
@blueprint_home.route('/home')
def home():
    return{"message": "HomeController"}, 200