from flask import Blueprint, render_template, session, flash, redirect, url_for
import pandas as pd
from services.helpers import get_current_semester

challenging_courses_forecast_bp = Blueprint('challenging_courses_forecast_bp', __name__)

@challenging_courses_forecast_bp.route('/challenging_courses_forecast')
def challenging_courses_forecast():
    # Ensure the student is logged in
    if 'Registration_number' not in session:
        flash('You are not logged in!')
        return redirect(url_for('home'))

    reg_no = session['Registration_number']
    is_bcs = 'BCS' in reg_no.upper()  # Check if the student belongs to BCS or BSE
    current_semester = get_current_semester(reg_no)

    if not current_semester:
        flash("Could not determine the current semester.")
        return redirect(url_for('dashboard'))

    # Load course difficulty data
    course_difficulty = pd.read_csv('data/coursedifficulty.csv')

    # Load the appropriate course data based on the program (BCS or SE)
    course_data = pd.read_csv(
        'data/DashboardSemesterWiseCourseInfoCS.csv' if is_bcs else 'data/DashboardSemesterWiseCourseInfoSE.csv'
    )

    current_semester_num = int(current_semester.split()[-1])  # Extract semester number

    # Prepare a dictionary to store course details semester-wise
    challenging_courses = {}

    # Loop through each semester from the current semester to the 8th semester
    for semester_num in range(current_semester_num, 9):
        semester_name = f'Semester{semester_num}'

        if semester_name in course_data.columns:
            courses_in_semester = course_data[semester_name].dropna().tolist()
            semester_courses = []

            for course_no in courses_in_semester:
                course_details = course_difficulty[course_difficulty['Course_no'] == course_no]

                if not course_details.empty:
                    course_name = course_details['Title'].values[0]
                    failure_probability = round(course_details['failure_probability'].values[0] * 100, 2)
                    avg_gpa = course_details['average_GPA'].values[0]
                    std_dev = course_details['GPA_standard_deviation'].values[0]
                    difficulty_level = course_details['difficulty_level'].values[0]

                    semester_courses.append({
                        'course_no': course_no,
                        'course_name': course_name,
                        'failure_probability': failure_probability,
                        'avg_gpa': avg_gpa,
                        'std_dev': std_dev,
                        'difficulty_level': difficulty_level
                    })

            if semester_courses:
                challenging_courses[semester_name] = semester_courses

    return render_template('challenging_courses_forecast.html', challenging_courses=challenging_courses)
