from flask import Blueprint, render_template, session, flash, redirect, url_for
import pandas as pd
import random
from services.helpers import (
    get_current_semester, get_courses_by_semester, get_course_details
)

dashboard_bp = Blueprint('dashboard_bp', __name__)


@dashboard_bp.route('/dashboard')
def dashboard():
    if 'Registration_number' not in session:
        flash('You are not logged in!')
        return redirect(url_for('main.home_bp.home'))

    reg_no = session['Registration_number']
    
    # Random teacher names for demonstration
    teachers = ["Dr. Sheneela Naz", "Sadan Ali", "Zahida", "Omer Vikas", "Asma Jabeen", "Dr. Akber Abid Gardezi"]

    
    # Set the student's name
    student_name = "Syed Haadi Raza"

    # Determine the department based on registration number
    is_bcs = 'BCS' in reg_no.upper()
    department = "Computer Science" if is_bcs else "Software Engineering"

    # Extract the batch from the registration number (Assuming format: ciit/sp21-bse-856/isb)
    batch = reg_no.split('/')[1][:4] if '/' in reg_no else "Unknown"

    # Get the current semester
    current_semester = get_current_semester(reg_no)

    if not current_semester:
        flash('Could not determine current semester.')
        return redirect(url_for('main.home_bp.home'))

    # Find student's status from the databaseextracted.csv file based on registration number
    data = pd.read_csv("data/databasextracted.csv")
    student_row = data[data['Registration_number'] == reg_no]

    if not student_row.empty:
        status_id = student_row['Status_id'].values[0]
        if status_id == 1:
            student_status = "Dropout"
        elif status_id == 2:
            student_status = "Graduated"
        elif status_id == 3:
            student_status = "Graduating"
        else:
            student_status = "Unknown"
    else:
        student_status = "Unknown"

    # Determine completed credit hours
    courses_file = 'data/DashboardSemesterWiseCourseInfoCS.csv' if is_bcs else 'data/DashboardSemesterWiseCourseInfoSE.csv'
    courses_data = pd.read_csv(courses_file)

    completed_credit_hours = 0
    # Loop through semesters from 1 to the semester before the current semester
    for semester_num in range(1, int(current_semester.split()[-1])):
        semester_name = f'Semester{semester_num}'
        if semester_name in courses_data.columns:
            courses_in_semester = courses_data[semester_name].dropna().tolist()
            # Loop through each course and sum the credit hours
            for course_no in courses_in_semester:
                _, credit_hours = get_course_details(course_no)
                completed_credit_hours += credit_hours if credit_hours else 0

    # Generate random GPA for the current semester
    current_gpa = round(random.uniform(2.0, 4.0), 2)

    # Get the courses for the current semester
    courses = get_courses_by_semester(current_semester, is_bcs)
    course_details = []

    for course_no in courses:
        title, credit_hours = get_course_details(course_no)
        teacher = random.choice(teachers)
        attendance = random.randint(50, 100)  # Random attendance between 50-100%
        course_details.append({
            'course_no': course_no,
            'title': title,
            'credit_hours': credit_hours,
            'teacher': teacher,
            'attendance': attendance
        })

    # Render the dashboard template with the additional details
    return render_template(
        'dashboard.html', 
        course_details=course_details,
        reg_no=reg_no,
        student_name=student_name,
        department=department,
        batch=batch,
        student_status=student_status,
        completed_credit_hours=completed_credit_hours,
        current_gpa=current_gpa
    )

