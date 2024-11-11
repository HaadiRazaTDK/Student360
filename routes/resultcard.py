from flask import Blueprint, render_template, session, flash, redirect, url_for
from services.helpers import get_current_semester, get_courses_by_semester, get_course_details, generate_gpa

result_card_bp = Blueprint('result_card_bp', __name__)

@result_card_bp.route('/result_card')
def result_card():
    if 'Registration_number' not in session:
        flash('You are not logged in!')
        return redirect(url_for('home'))

    reg_no = session['Registration_number']
    is_bcs = 'BCS' in reg_no.upper()
    current_semester = get_current_semester(reg_no)

    if not current_semester:
        flash('Could not determine current semester.')
        return redirect(url_for('home'))

    student_results = []
    total_semesters = int(current_semester.split()[-1])

    for semester_num in range(1, total_semesters + 1):
        semester_name = f"Semester {semester_num}"
        courses = get_courses_by_semester(semester_name, is_bcs)
        semester_courses = []

        for course_no in courses:
            title, credit_hours = get_course_details(course_no)
            gpa = generate_gpa() if semester_num < total_semesters else None

            semester_courses.append({
                'course_no': course_no,
                'title': title,
                'credit_hours': credit_hours,
                'gpa': gpa  # GPA is None for the current semester
            })

        semester_data = {
            'semester': semester_name,
            'courses': semester_courses,
        }

        if semester_num < total_semesters:
            semester_data['gpa'] = generate_gpa()

        student_results.append(semester_data)

    return render_template('result_card.html', student_results=student_results)
