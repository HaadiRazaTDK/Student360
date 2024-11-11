from flask import Blueprint, render_template, session, flash, redirect, url_for, request
import pandas as pd
from services.helpers import (
    get_current_semester, fetch_student_data, get_courses_by_semester, gpa_to_percentage,
    fetch_current_marks, identify_unmarked_components, adjust_unmarked_marks, calculate_mean_exclude_zero,
    get_courses_and_credit_hours, process_failed_courses, create_prerequisite_chains_for_unregistered,
    register_unregistered_courses
)

prerequisite_courses_impact_bp = Blueprint('prerequisite_courses_impact_bp', __name__)

@prerequisite_courses_impact_bp.route('/prerequisite_courses_impact', methods=['GET', 'POST'])
def prerequisite_courses_impact():
    if 'Registration_number' not in session:
        flash('You are not logged in!')
        return redirect(url_for('home'))

    reg_no = session.get('Registration_number')
    is_bcs = 'BCS' in reg_no.upper()
    current_semester = get_current_semester(reg_no)

    if not current_semester:
        flash('Could not determine current semester.')
        return redirect(url_for('dashboard'))

    course_data_file = 'data/SemesterWiseCourseInformationCS.csv' if is_bcs else 'data/SemesterWiseCourseInformationSE.csv'
    course_data = pd.read_csv(course_data_file)
    
    prereq_dict = {}
    for semester in range(1, 13):
        courses = course_data[f'Semester{semester}']
        prereqs = course_data[f'Prerequisite{semester}']
        for course, prereq in zip(courses, prereqs):
            if pd.notna(course) and pd.notna(prereq):
                prereq_dict[course] = [p.strip() for p in prereq.split(',')] if prereq != 'none' else []

    courses_and_credit_hours = get_courses_and_credit_hours(course_data)
    semesters = [f"Semester {i}" for i in range(1, 9)]
    full_timetable = {f'Semester{i}': [] for i in range(1, 9)}

    for index, row in course_data.iterrows():
        for i in range(1, 9):
            semester_key = f'Semester{i}'
            course_key = row[semester_key]
            if pd.notna(course_key) and course_key != "NULL":
                full_timetable[semester_key].append({
                    "Course": course_key,
                })

    impacted_timetable = None
    unregistered_courses = None

    if request.method == 'POST':
        selected_semester = request.form.get('selected_semester')
        selected_course = request.form.get('selected_course')

        if selected_course and selected_semester:
            failed_courses = [selected_course]
            updated_df, unregistered_courses = process_failed_courses(course_data, int(selected_semester.split()[-1]), failed_courses)
            
            semester_columns = [f'Semester{i}' for i in range(1, 13)]
            updated_df_semesters_only = updated_df[semester_columns].drop_duplicates()

            prerequisite_chains = create_prerequisite_chains_for_unregistered(unregistered_courses, prereq_dict, courses_and_credit_hours)

            updated_schedule, remaining_unregistered_courses = register_unregistered_courses(
                unregistered_courses,
                updated_df_semesters_only,
                courses_and_credit_hours,
                prereq_dict,
                selected_semester
            )

            updated_schedule = updated_schedule.dropna(axis=1, how='all').drop_duplicates()

            impacted_timetable = {f'Semester{i}': [] for i in range(1, len(updated_schedule.columns) + 1)}
            for index, row in updated_schedule.iterrows():
                for i in range(1, len(updated_schedule.columns) + 1):
                    semester_key = f'Semester{i}'
                    course_key = row[semester_key]
                    if pd.notna(course_key) and course_key != "NULL":
                        if course_key.rstrip('*') in failed_courses:
                            course_key = course_key.rstrip('*') + '*'
                        impacted_timetable[semester_key].append({
                            "Course": course_key
                        })

            return render_template(
                'prerequisite_courses_impact.html',
                semester_courses=course_data[[f'Semester{i}' for i in range(1, 13)]].stack().unique(),
                full_timetable=full_timetable,
                impacted_timetable=impacted_timetable,
                unregistered_courses=unregistered_courses,
                semesters=semesters
            )

    return render_template(
        'prerequisite_courses_impact.html',
        semesters=semesters,
        semester_courses=[],
        full_timetable=full_timetable,
        impacted_timetable=None,
        unregistered_courses=None
    )
