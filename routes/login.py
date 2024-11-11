from flask import Blueprint, render_template, session, flash, redirect, url_for, request


login_bp = Blueprint('login', __name__)

# ... existing routes ...

@login_bp.route('/login', methods=['POST'])
def login():
    reg_no = request.form['Registration_number']
    session['Registration_number'] = reg_no
    return redirect(url_for('main.dashboard_bp.dashboard'))

# ... other routes ...
