from flask import Blueprint, render_template, session, flash, redirect, url_for, request


logout_bp = Blueprint('logout_bp', __name__)

# ... existing routes ...

@logout_bp.route('/logout')
def logout():
    # Clear factors, suggestions, and warnings when the user logs out
    session.pop('factors', None)
    session.pop('suggestions', None)
    session.pop('warnings', None)

    # Clear the session data for the registration number and graduation prediction
    session.pop('Registration_number', None)
    session.pop('student_data_graduation', None)
    
    flash('You have been logged out.')
    return redirect(url_for('main.home_bp.home'))

# ... other routes ...
