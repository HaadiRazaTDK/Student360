from flask import Blueprint, render_template, session, flash, redirect, url_for
import pandas as pd
from services.helpers import get_current_semester, get_low_gpa_semesters, process_courses_for_warnings_suggestions, predict_graduation, custom_load_model

timely_graduation_forecast_bp = Blueprint('timely_graduation_forecast_bp', __name__)

@timely_graduation_forecast_bp.route('/timely_graduation_forecast', methods=['GET', 'POST'])
def timely_graduation_forecast():
    # Reset factors, suggestions, and warnings at the beginning of the request
    factors, warnings, suggestions = [], [], []
    course_info = pd.read_csv(r'data/coursedifficulty.csv')
    # Retrieve the student data from the session
    student_data_json = session.get('student_data_graduation')

    if student_data_json:
        # Convert JSON string back to DataFrame
        student_data_graduation = pd.read_json(student_data_json, orient='split')
    else:
        flash("No student data available for graduation forecast.")
        return redirect(url_for('main.dashboard_bp.dashboard'))  # Redirect to dashboard if no data

    # Get the current semester
    reg_no = session.get('Registration_number')
    if not reg_no:
        flash("Please log in to view this page.")
        return redirect(url_for('home'))

    current_semester = get_current_semester(reg_no)
    if not current_semester:
        flash("Could not determine the current semester.")
        return redirect(url_for('main.dashboard_bp.dashboard'))
    
    # Get semesters with GPA < 2
    low_gpa_semesters = get_low_gpa_semesters(student_data_graduation, current_semester)
    is_bcs = 'BCS' in reg_no.upper()
    
    if is_bcs:
        course_data1 = pd.read_csv(r'data/DashboardSemesterWiseCourseInfoCS.csv')
    else:
        course_data1 = pd.read_csv(r'data/DashboardSemesterWiseCourseInfoSE.csv')

    # Process courses for factors, warnings, and suggestions
    factors, warnings, suggestions = process_courses_for_warnings_suggestions(low_gpa_semesters, course_data1, course_info)

    # Load the graduation model
    model_path = 'Model_Files/Voting_graduation0.9207.pkl'
    model = custom_load_model(model_path)
    if model is None:
        flash('could not load the model.')
        return redirect(url_for('main.dashboard_bp.dashboard'))  # Handle the case when model fails to load

    # Perform the prediction
    student_data_graduation, predictions, probabilities = predict_graduation(student_data_graduation, model)

    # Extract the prediction result and probability
    graduation_status = "On-Time" if predictions[0] == 1 else "Late"
    confidence = f"{probabilities[0][predictions[0]]:.2%}" if probabilities is not None else "N/A"
        
    # Return data to the template
    return render_template(
        'timely_graduation_forecast.html',
        graduation_status=graduation_status,
        confidence=confidence,
        current_semester=current_semester,
        factors=factors,
        warnings=warnings,
        suggestions=suggestions
    )
