from flask import Blueprint, render_template, session, flash, redirect, url_for
import pandas as pd
from services.helpers import get_current_semester, get_courses_by_semester, predict_gpa, models

# Create a blueprint for academic routes
academic_performance_forcast_bp = Blueprint('academic_performance_forcast_bp', __name__)

@academic_performance_forcast_bp.route('/academic_performance_forecast', methods=['POST', 'GET'])
def academic_performance_forecast():
    # Ensure the student is logged in
    if 'Registration_number' not in session:
        flash('You are not logged in!')
        return redirect(url_for('home'))

    reg_no = session['Registration_number']
    current_semester = get_current_semester(reg_no)  # Assuming you have this function
    is_bcs = 'BCS' in reg_no.upper()
    
    
    factors = {
    "GPA_Semester_2": [
        "Average_CourseCode_CSC_Gpa",
        "Average_CourseCode_HUM_Gpa",
        "Average_CourseCode_MTH_Gpa",
        "Average_CGPA",
        "GPA_Semester_1",
        "Academic_Standing_University",
        "Academic_Standing_Department",
        "Academic_Standing_Batch"
    ],
    "GPA_Semester_3": [
        "Academic_Standing_University",
        "Academic_Standing_Department",
        "Average_CourseCode_CSC_Gpa",
        "Academic_Standing_Batch",
        "Average_CourseCode_HUM_Gpa",
        "Average_CGPA",
        "GPA_Semester_2",
        "Average_CourseCode_MTH_Gpa",
        "GPA_Semester_1"
    ],
    "GPA_Semester_4": [
        "Academic_Standing_Batch",
        "Academic_Standing_University",
        "Academic_Standing_Department",
        "Average_CourseCode_CSC_Gpa",
        "Average_CGPA",
        "GPA_Semester_3",
        "Average_CourseCode_HUM_Gpa",
        "Average_CourseCode_MTH_Gpa",
        "GPA_Semester_2",
        "GPA_Semester_1"
    ],
    "GPA_Semester_5": [
        "Average_CourseCode_CSC_Gpa",
        "Academic_Standing_Batch",
        "Academic_Standing_University",
        "Academic_Standing_Department",
        "GPA_Semester_4",
        "Average_CGPA",
        "Average_CourseCode_MTH_Gpa",
        "Average_CourseCode_HUM_Gpa",
        "GPA_Semester_2",
        "GPA_Semester_1",
        "GPA_Semester_3"
    ],
    "GPA_Semester_6": [
        "Academic_Standing_Department",
        "Academic_Standing_University",
        "Average_CourseCode_CSC_Gpa",
        "Academic_Standing_Batch",
        "GPA_Semester_5",
        "GPA_Semester_1",
        "Average_CourseCode_HUM_Gpa",
        "GPA_Semester_2",
        "GPA_Semester_4",
        "GPA_Semester_3",
        "Average_CourseCode_MTH_Gpa"
    ],
    "GPA_Semester_7": [
        "Academic_Standing_University",
        "Academic_Standing_Department",
        "Average_CourseCode_CSC_Gpa",
        "Academic_Standing_Batch",
        "GPA_Semester_6",
        "Average_CGPA",
        "Average_CourseCode_HUM_Gpa",
        "GPA_Semester_2",
        "GPA_Semester_5",
        "GPA_Semester_1",
        "GPA_Semester_4",
        "GPA_Semester_3",
        "Average_CourseCode_MTH_Gpa"
    ],
    "GPA_Semester_8": [
        "Academic_Standing_Department",
        "Academic_Standing_University",
        "Academic_Standing_Batch",
        "GPA_Semester_7",
        "Average_CourseCode_CSC_Gpa",
        "Average_CourseCode_HUM_Gpa",
        "Average_CGPA"
        "GPA_Semester_4",
        "GPA_Semester_3",
        "GPA_Semester_1",
        "GPA_Semester_2",
        "GPA_Semester_5"
    ]
}

    # Load the student data from the CSV file
    data = pd.read_csv("data/databasextracted.csv")
    
    CategoricalVariables = []
    ContinousVariables = []
    
    for column in data.columns:
        if data[column].isnull().sum() > 200: 
            continue
        else:
            if data[column].dtype == "object":
                CategoricalVariables.append(column)
            else:
                if data[column].nunique() < 50:
                    CategoricalVariables.append(column)
                else:
                    ContinousVariables.append(column)
    
    
    for col in data.columns:
        if col in CategoricalVariables:
           data[col].fillna(data[col].mode()[0], inplace=True)
        elif col in ContinousVariables:
            data[col].fillna(data[col].mean(), inplace=True)
            
    student_data = data[data['Registration_number']==reg_no]
    
    # Drop unnecessary columns based on the current semester
    columns_to_drop = ['GPA_Semester_9', 'GPA_Semester_10', 'GPA_Semester_11', 'GPA_Semester_12', 
                       'PreAdmission_Score', 'Max_PreAdmission_score', 'Average_CourseCode_PHY_Gpa', 
                       'Average_CourseCode_EEE_Gpa', 'Average_CourseCode_BIO_Gpa', 'Average_CourseCode_CSE_Gpa', 
                       'Average_CourseCode_MGT_Gpa', 'Average_CourseCode_ENV_Gpa', 'Average_CourseCode_CSD_Gpa']
    student_data = student_data.drop(columns=columns_to_drop)
    
    # Extract the current semester number as an integer
    current_semester_num = int(current_semester.split()[-1])


    # Find all columns that are GPA columns (e.g., GPA_Semester_#)
    gpa_columns = [col for col in student_data.columns if col.startswith('GPA_Semester_')]

    # Identify and drop the GPA columns that correspond to semesters after the current semester
    for col in gpa_columns:
        semester_num = int(col.split('_')[-1])  # Extract the semester number from the column name
        if semester_num > current_semester_num:
            student_data = student_data.drop(columns=[col])

        
    # Remove redundant columns
    RedundantVariables = ['Registration_number','Domicile_id', 'Year_id', 'Matric_inter_Improvement_index', 'Matric_Degree_id', 
                          'Matric_Board_id', 'Matric_Board_Performance_Avg_Standpoint', 
                          'Matric_Degree_Performance_Avg_Standpoint', 'Matric_Domicile_Performance_Avg_Standpoint', 
                          'Matric_Performance_Avg_Standpoint', 'Inter_Board_id', 'Inter_Degree_id', 
                          'Inter_Subject_id', 'Inter_Board_Performance_Avg_Standpoint', 
                          'Inter_Degree_Performance_Avg_Standpoint', 'Inter_Domicile_Performance_Avg_Standpoint', 
                          'Inter_Subject_Performance_Avg_Standpoint', 'inter_performance_Avg_Standpoint']
    student_data = student_data.drop(columns=RedundantVariables)
    
    print('student_data : ', student_data.columns)
    
    # Flag to indicate which GPAs are predicted
    predicted_gpas = {}
    
    # Perform predictions starting from the current semester up to the 8th semester
    for semester in range(int(current_semester.split()[-1]), 9):
        model_key = f"GPA_Semester_{semester}"
        if model_key in models:
            model = models[model_key]
            student_data = predict_gpa(student_data, model, semester)
            predicted_gpas[model_key] = True  # Mark GPA as predicted
    
    # Keep only columns that start with 'GPA_Semester_'
    # Prepare data for graduation prediction
    student_data_for_graduation_prediction = student_data[['GPA_Semester_1', 'GPA_Semester_2', 'GPA_Semester_3',
                                                           'GPA_Semester_4', 'GPA_Semester_5', 'GPA_Semester_6',
                                                           'GPA_Semester_7', 'GPA_Semester_8', 'Average_CourseCode_HUM_Gpa',
                                                           'Average_CourseCode_CSC_Gpa', 'Academic_Standing_University',
                                                           'Academic_Standing_Department', 'Academic_Standing_Batch']].copy()

    # Convert DataFrame to JSON string and store it in the session
    session['student_data_graduation'] = student_data_for_graduation_prediction.to_json(orient='split')

    
    gpa_columns = [col for col in student_data.columns if col.startswith('GPA_Semester_')]
    student_data = student_data[gpa_columns]

    
    

   # Determine current semester and initialize factors, warnings, and suggestions
    current_semester_num = int(current_semester.split()[-1])

    current_factors = factors.get(f'GPA_Semester_{current_semester_num}', [])
    current_suggestions = []
    current_warnings = []

    # Get student's GPA data
    gpa_data = student_data.iloc[0].to_dict()

    # Check for warnings based on conditions
    for factor in current_factors:
        if factor in ["Average_CourseCode_CSC_Gpa", "Average_CourseCode_HUM_Gpa", "Average_CourseCode_MTH_Gpa"]:
            if gpa_data.get(factor, 0) <= 2:
                current_warnings.append(factor)

        if factor in ["Average_CGPA", "GPA_Semester_1"]:
            if gpa_data.get(factor, 0) <= 2:
                current_warnings.append(factor)

        if factor in ["Academic_Standing_University", "Academic_Standing_Department", "Academic_Standing_Batch"]:
            if gpa_data.get(factor, 100) < 50:  # Assuming 100 is the max for academic standing
                current_warnings.append(factor)

    
    # Modified portion for suggestions generation
    for warning in current_warnings:
        if warning in ["Average_CourseCode_CSC_Gpa", "Average_CourseCode_HUM_Gpa", "Average_CourseCode_MTH_Gpa"]:
            # Find courses that start with CSC, HUM, or MTH in the current semester
            for course in get_courses_by_semester(current_semester, is_bcs):
                if course.startswith("csc") and warning == "Average_CourseCode_CSC_Gpa":
                    current_suggestions.append(f"Focus on improving in {course} (CSC-related course).")
                elif course.startswith("hum") and warning == "Average_CourseCode_HUM_Gpa":
                    current_suggestions.append(f"Focus on improving in {course} (HUM-related course).")
                elif course.startswith("mth") and warning == "Average_CourseCode_MTH_Gpa":
                    current_suggestions.append(f"Focus on improving in {course} (MTH-related course).")

         # This section should be outside the previous loop, as it handles different warnings
    if any(warning in ["Average_CGPA", "GPA_Semester_1"] for warning in current_warnings):
        current_suggestions.append("Improve your attendance.")
        current_suggestions.append("Study CLO (Course Learning Outcomes) more effectively.")
        current_suggestions.append("Practice coding regularly to enhance your skills.")   
            
    # Render the template with student data, factors, suggestions, and warnings
    return render_template(
        'academic_performance_forecast.html',
        student_data=gpa_data,
        factors=current_factors,
        suggestions=current_suggestions,
        warnings=current_warnings,
        predicted_gpas=predicted_gpas
    )