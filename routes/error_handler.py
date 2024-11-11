from flask import Blueprint, render_template, session, flash, redirect, url_for, request

error_handler_bp = Blueprint('error_handler_bp', __name__)

@error_handler_bp.errorhandler(400)
def bad_request_error(error):
    return render_template('400.html', error=error), 400