from flask import Blueprint, render_template, session, flash, redirect, url_for, jsonify
import pandas as pd


get_courses_bp = Blueprint('get_courses', __name__)

# Existing routes ...

@get_courses_bp.route('/get_courses/<selected_semester>', methods=['GET'])
def get_courses(selected_semester):
    reg_no = session.get('Registration_number')

    if not reg_no:
        return jsonify({"error": "Not logged in"}), 403

    is_bcs = 'BCS' in reg_no.upper()
    course_data_file = 'data/SemesterWiseCourseInformationCS.csv' if is_bcs else 'data/SemesterWiseCourseInformationSE.csv'
    
    # Ensure the file exists and is loaded correctly
    try:
        course_data = pd.read_csv(course_data_file)
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return jsonify({"error": "Failed to read course data"}), 500

    # Convert the semester number from "Semester X" to integer
    try:
        semester_number = int(selected_semester.split()[-1])
    except ValueError:
        print(f"Invalid semester format: {selected_semester}")
        return jsonify({"error": "Invalid semester format"}), 400

    semester_key = f'Semester{semester_number}'
    
    # Check if the semester column exists
    if semester_key not in course_data.columns:
        print(f"Semester column not found: {semester_key}")
        return jsonify({"error": "Semester not found"}), 404

    # Get the courses for the selected semester
    courses = course_data[semester_key].dropna().tolist()  # Drop any NaN values and convert to list

    return jsonify(courses)

# Other routes ...
