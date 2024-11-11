from flask import Blueprint, render_template, session, flash, redirect, url_for
import pandas as pd


home_bp = Blueprint('home_bp', __name__)

# Existing routes ...

@home_bp.route('/')
def home():
    # Render the login page
    return render_template('login.html')

# Other routes ...
