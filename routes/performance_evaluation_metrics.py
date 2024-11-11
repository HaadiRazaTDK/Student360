from flask import Blueprint, render_template, session, flash, redirect, url_for, request, abort
import pandas as pd
import os
from services.helpers import get_current_semester, plot_performance

performance_evaluation_metrics_bp = Blueprint('performance_evaluation_metrics_bp', __name__)

@performance_evaluation_metrics_bp.route('/performance_evaluation_metrics', methods=['GET', 'POST'])
def performance_evaluation_metrics():
    # Step 1: Get registration number and semester
    reg_no = session.get('Registration_number')
    if not reg_no:
        abort(400, description="Registration number is not logged in to session.")

    semester = get_current_semester(reg_no)
    if not semester:
        abort(400, description="Semester information is not available.")


    data_files = {
    'Semester 1CS': os.path.join('data', 'semester1CS.csv'),
    'Semester 2CS': os.path.join('data', 'semester2CS.csv'),
    'Semester 3CS': os.path.join('data', 'semester3CS.csv'),
    'Semester 4CS': os.path.join('data', 'semester4CS.csv'),
    'Semester 5CS': os.path.join('data', 'semester5CS.csv'),
    'Semester 6CS': os.path.join('data', 'semester6CS.csv'),
    'Semester 7CS': os.path.join('data', 'semester7CS.csv'),
    'Semester 8CS': os.path.join('data', 'semester8CS.csv'),
    'Semester 1SE': os.path.join('data', 'semester1SE.csv'),
    'Semester 2SE': os.path.join('data', 'semester2SE.csv'),
    'Semester 3SE': os.path.join('data', 'semester3SE.csv'),
    'Semester 4SE': os.path.join('data', 'semester4SE.csv'),
    'Semester 5SE': os.path.join('data', 'semester5SE.csv'),
    'Semester 6SE': os.path.join('data', 'semester6SE.csv'),
    'Semester 7SE': os.path.join('data', 'semester7SE.csv'),
    'Semester 8SE': os.path.join('data', 'semester8SE.csv')
    }


    semester_data_pem = {semester: pd.read_csv(file) for semester, file in data_files.items()}



    # Step 2: Determine the program and fetch relevant data
    is_bcs = 'BCS' in reg_no.upper()
    selected_semester_data = semester_data_pem.get(f'{semester}CS' if is_bcs else f'{semester}SE')

    if selected_semester_data is None:
        return "Error: No data available for the current semester", 400

    # Handle POST request for course performance evaluation
    if request.method == 'POST':
        selected_course = request.form.get('course')
        if not selected_course:
            abort(400, description="No course is selected to display information.")

        selected_course = selected_course.strip().lower()
        selected_semester_data['Course_no'] = selected_semester_data['Course_no']
        selected_semester_data['Registration_number'] = selected_semester_data['Registration_number'].str.strip().str.lower()

        selected_course_data = selected_semester_data[
            (selected_semester_data['Course_no'] == selected_course) &
            (selected_semester_data['Registration_number'] == reg_no)
        ]

        if selected_course_data.empty:
            abort(400, description="Data not available for the selected course.")

        semesters_to_include = [
            sem for sem in data_files.keys()
            if int(''.join(filter(str.isdigit, sem))) < int(''.join(filter(str.isdigit, semester)))
        ]
        combined_data = pd.concat([semester_data_pem[sem] for sem in semesters_to_include])

        numeric_columns = [
            'Quiz1', 'Quiz2', 'Quiz3', 'Quiz4',
            'Assignment1', 'Assignment2', 'Assignment3', 'Assignment4',
            'MidTerm', 'FinalTerm',
            'LabMidTerm', 'LabFinalTerm', 'LabAssignment1', 'LabAssignment2',
            'LabTask1', 'LabTask2'
        ]
        combined_data[numeric_columns] = combined_data[numeric_columns].apply(pd.to_numeric, errors='coerce')
        selected_course_data[numeric_columns] = selected_course_data[numeric_columns].apply(pd.to_numeric, errors='coerce')

        course_cat = selected_course[:3]
        avg_metrics_prev = combined_data[
            (combined_data['Course_cat'] == course_cat) &
            (combined_data['Registration_number'] == reg_no)
        ][numeric_columns].mean()

        current_metrics = selected_course_data[numeric_columns].mean()

        quiz_metrics = ['Quiz1', 'Quiz2', 'Quiz3', 'Quiz4']
        assignment_metrics = ['Assignment1', 'Assignment2', 'Assignment3', 'Assignment4']
        exam_metrics = ['MidTerm', 'FinalTerm']
        lab_midterm_final_metrics = ['LabMidTerm', 'LabFinalTerm']
        lab_assignments_tasks_metrics = ['LabAssignment1', 'LabAssignment2', 'LabTask1', 'LabTask2']

        warnings, suggestions = [], []

        def generate_feedback(current, avg, metric_name):
            difference = current - avg
            if difference < -15:
                warnings.append(f"Significant improvement needed in {metric_name}. Seek help or revise the concepts.")
            elif -15 <= difference < -5:
                warnings.append(f"You're slightly below average in {metric_name}. A little more focus will help.")
            elif -5 <= difference <= 5:
                suggestions.append(f"Your performance in {metric_name} is consistent with the average. Keep it up.")
            elif 5 < difference <= 15:
                suggestions.append(f"You're slightly above average in {metric_name}. Great job!")
            else:
                suggestions.append(f"Outstanding performance in {metric_name}. Keep excelling!")

        for metric in quiz_metrics:
            generate_feedback(current_metrics[metric], avg_metrics_prev[metric], metric)
        for metric in assignment_metrics:
            generate_feedback(current_metrics[metric], avg_metrics_prev[metric], metric)
        for metric in exam_metrics:
            generate_feedback(current_metrics[metric], avg_metrics_prev[metric], metric)

        plots = {
            "Quiz Performance": plot_performance(avg_metrics_prev[quiz_metrics], current_metrics[quiz_metrics], quiz_metrics, "Quiz Performance"),
            "Assignment Performance": plot_performance(avg_metrics_prev[assignment_metrics], current_metrics[assignment_metrics], assignment_metrics, "Assignment Performance"),
            "Exam Performance": plot_performance(avg_metrics_prev[exam_metrics], current_metrics[exam_metrics], exam_metrics, "Exam Performance")
        }

        if any(current_metrics[lab_midterm_final_metrics].notna()):
            plots["Lab Midterm and Final Performance"] = plot_performance(
                avg_metrics_prev[lab_midterm_final_metrics], current_metrics[lab_midterm_final_metrics],
                lab_midterm_final_metrics, "Lab Midterm and Final Performance"
            )

        if any(current_metrics[lab_assignments_tasks_metrics].notna()):
            plots["Lab Assignments and Tasks Performance"] = plot_performance(
                avg_metrics_prev[lab_assignments_tasks_metrics], current_metrics[lab_assignments_tasks_metrics],
                lab_assignments_tasks_metrics, "Lab Assignments and Tasks Performance"
            )

        return render_template(
            'performance_evaluation_metrics.html',
            plots=plots,
            courses=selected_semester_data['Course_no'].unique().tolist(),
            selected_course=selected_course,
            warnings=warnings,
            suggestions=suggestions,
            data_files=data_files
        )

    courses = selected_semester_data['Course_no'].unique().tolist()
    return render_template(
        'performance_evaluation_metrics.html',
        courses=courses,
        data_files=data_files
    )
