from flask import Blueprint, render_template, session, flash, redirect, url_for, request
from services.helpers import (
    get_current_semester, fetch_student_data, get_courses_by_semester, gpa_to_percentage,
    fetch_current_marks, identify_unmarked_components, adjust_unmarked_marks, calculate_mean_exclude_zero
)

tracking_GPA_target_bp = Blueprint('tracking_GPA_target_bp', __name__)

@tracking_GPA_target_bp.route('/tracking_GPA_target', methods=['GET', 'POST'])
def tracking_GPA_target():
    if request.method == 'POST':
        reg_no = session.get('Registration_number')
        current_semester = get_current_semester(reg_no)
        is_bcs = 'BCS' in reg_no.upper()

        student_data = fetch_student_data(reg_no, current_semester, is_bcs)
        if student_data is None:
            flash('No data found for the current semester.')
            return redirect(url_for('dashboard'))

        semester_courses = get_courses_by_semester(current_semester, is_bcs)
        gpa_targets = {}
        required_marks_per_course = {}
        achieved_marks_per_course = {}
        remarks_per_course = {}

        for course in semester_courses:
            target_gpa = request.form.get(f'gpa_{course}', 0)
            try:
                target_gpa = float(target_gpa)
            except ValueError:
                target_gpa = 0
            gpa_targets[course] = target_gpa

            required_percentage = gpa_to_percentage(target_gpa)

            quiz_marks, assignment_marks, midterm_mark, finalterm_mark = fetch_current_marks(student_data, course)

            quiz_marks = [int(x) if isinstance(x, (int, float, str)) and str(x).isdigit() else 0 for x in quiz_marks]
            assignment_marks = [int(x) if isinstance(x, (int, float, str)) and str(x).isdigit() else 0 for x in assignment_marks]
            midterm_mark = int(midterm_mark) if isinstance(midterm_mark, (int, str)) and str(midterm_mark).isdigit() else 0
            finalterm_mark = int(finalterm_mark) if isinstance(finalterm_mark, (int, str)) and str(finalterm_mark).isdigit() else 0

            achieved_marks_per_course[course] = {
                "quizzes": quiz_marks,
                "assignments": assignment_marks,
                "midterm": midterm_mark,
                "finalterm": finalterm_mark
            }

            unmarked_quizzes, unmarked_assignments, unmarked_midterm, unmarked_finalterm = identify_unmarked_components(
                quiz_marks, assignment_marks, midterm_mark, finalterm_mark
            )

            required_quizzes, quiz_remarks = adjust_unmarked_marks(unmarked_quizzes, calculate_mean_exclude_zero(quiz_marks), required_percentage * 0.1, "quizzes")
            required_assignments, assignment_remarks = adjust_unmarked_marks(unmarked_assignments, calculate_mean_exclude_zero(assignment_marks), required_percentage * 0.15, "assignments")
            required_midterm, midterm_remarks = adjust_unmarked_marks([midterm_mark], midterm_mark, required_percentage * 0.25, "midterm")
            required_finalterm, finalterm_remarks = adjust_unmarked_marks([finalterm_mark], finalterm_mark, required_percentage * 0.5, "finalterm")

            required_marks_per_course[course] = {
                "quizzes": required_quizzes,
                "assignments": required_assignments,
                "midterm": required_midterm,
                "finalterm": required_finalterm
            }

            remarks_per_course[course] = {
                "quizzes": quiz_remarks,
                "assignments": assignment_remarks,
                "midterm": midterm_remarks,
                "finalterm": finalterm_remarks
            }

        return render_template(
            'tracking_GPA_target.html',
            semester_courses=semester_courses,
            required_marks_per_course=required_marks_per_course,
            achieved_marks_per_course=achieved_marks_per_course,
            gpa_targets=gpa_targets,
            remarks_per_course=remarks_per_course
        )

    else:
        reg_no = session.get('Registration_number')
        current_semester = get_current_semester(reg_no)
        is_bcs = 'BCS' in reg_no.upper()
        semester_courses = get_courses_by_semester(current_semester, is_bcs)
        gpa_targets = {}

        return render_template(
            'tracking_GPA_target.html',
            semester_courses=semester_courses,
            gpa_targets=gpa_targets
        )
