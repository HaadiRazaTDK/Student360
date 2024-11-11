
import matplotlib.patheffects as path_effects
import matplotlib.pyplot as plt
import os
import pandas as pd
import numpy as np
import os
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
import json 
import pickle
from flask import  flash
from sklearn.metrics import  r2_score
from sklearn.preprocessing import StandardScaler
import random
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg') 

# Load student registration data
students_data = pd.read_csv(r'data/DashboardCurrentSemesterStudents.csv')
courses_cs = pd.read_csv(r'data/DashboardSemesterWiseCourseInfoCS.csv')
courses_se = pd.read_csv(r'data/DashboardSemesterWiseCourseInfoSE.csv')
course_info = pd.read_csv(r'data/coursedifficulty.csv')  # Assuming this contains credit_hours




def plot_performance(avg_metrics, current_metrics, metrics, title):
    x = range(len(metrics))
    plt.figure(figsize=(8, 6))  # Slightly bigger figure for better visibility

    # Define colors that match the website's theme
    avg_color = '#34495e'  # Dark grey (for averages)
    current_color = '#1abc9c'  # Light green (for current marks)

    # Bar plots with reduced width and better spacing
    bars1 = plt.bar(x, avg_metrics, width=0.35, label='Previous Avg', color=avg_color, alpha=0.85, edgecolor='white')
    bars2 = plt.bar([i + 0.35 for i in x], current_metrics, width=0.35, label='Current Marks', color=current_color, alpha=0.85, edgecolor='white')

    # Add shadow effects to bars for depth
    shadow_effect = [path_effects.withSimplePatchShadow(offset=(2, -2), shadow_rgbFace='lightgrey')]
    for bar in bars1:
        bar.set_path_effects(shadow_effect)
    for bar in bars2:
        bar.set_path_effects(shadow_effect)

    # Aesthetic enhancements for axes
    plt.xticks([i + 0.35 / 2 for i in x], metrics, rotation=0, fontsize=11, color='#ecf0f1')  # Use clean white text for x-axis labels
    plt.ylabel('Marks', fontsize=11, color='#ecf0f1')  # Clean white text for y-axis label
    plt.title(title, fontsize=14, weight='bold', color='#1abc9c')  # Matching green title text

    # Custom legend with clean styling
    plt.legend(frameon=False, loc='upper left', fontsize=10, facecolor='white')

    # Minimal grid lines for a cleaner look
    plt.grid(axis='y', linestyle='--', linewidth=0.5, color='lightgrey', alpha=0.7)

    # Remove unnecessary borders and apply light grey to visible borders
    plt.gca().spines['top'].set_visible(False)
    plt.gca().spines['right'].set_visible(False)
    plt.gca().spines['left'].set_color('#95a5a6')
    plt.gca().spines['bottom'].set_color('#95a5a6')

    # Adjust layout for better compactness
    plt.tight_layout()

    # Save the plot
    plot_path = os.path.join('static/plots', f"{title.replace(' ', '_')}.png")
    plt.savefig(plot_path, bbox_inches='tight', pad_inches=0.1, transparent=True)  # Transparent background for cleaner integration
    plt.close()

    return plot_path


def calculate_mean_exclude_zero(values):
    # If values is None, assign it an empty list
    if values is None:
        values = []

    # Filter out zero values
    non_zero_values = [value for value in values if value != 0]
    
    # If there are no non-zero values, return 0 (or None if you want)
    if len(non_zero_values) == 0:
        return 0
    
    # Calculate and return the mean of non-zero values
    mean_value = np.mean(non_zero_values)
    return mean_value

def get_courses_and_credit_hours(df):
    course_credit_dict = {}
    
    # Iterate over each semester's course and credit hours
    for i in range(1, 13):  # We assume there can be up to Semester12
        semester_col = f"Semester{i}"
        credit_col = f"CreditHours{i}"
        
        # Iterate over the rows to extract course and credit hour data
        for index, row in df.iterrows():
            course = row[semester_col]
            credit_hours = row[credit_col]
            
            if course and credit_hours:  # Only add if course and credit hours are valid
                course_credit_dict[course] = credit_hours
                
    return course_credit_dict

# Adjust Unmarked Marks
def adjust_unmarked_marks(unmarked, current_mean, total_needed, component_name):
    remarks = ""
    
    if component_name == "finalterm":
        unmarked = [total_needed] if total_needed <= 50 else [50]
        remarks = "Keep pushing, you're almost there!"
        return unmarked, remarks
    
    elif component_name == "midterm":
        unmarked = [total_needed] if total_needed <= 25 else [25]
        remarks = "You can be halfway there with the midterm performance."
        return unmarked, remarks

    else:  # Quizzes and Assignments
        if component_name == "assignments":
            totalmarks = 16
        else: 
            totalmarks = 11

        for i in np.arange(0, totalmarks, 0.5):
            for j in range(len(unmarked)):
                unmarked[j] = i
            if current_mean != 0:
                new_mean = (current_mean + np.mean(unmarked)) / 2
            else:
                new_mean = np.mean(unmarked)

            if total_needed <= new_mean:
                if component_name == 'quizzes':
                    remarks = f'If you put effort into {component_name}, GPA target would be achieved easily.'
                elif component_name == 'assignments':
                    for i in range(len(unmarked)):
                        unmarked[i] = round(unmarked[i] * 2 / 3)
                    remarks = f'Good going, you can reach your target easily with {component_name} performance.'
                return unmarked, remarks

        remarks = f"Target GPA cannot be achieved by {component_name}."
        if component_name == 'assignments':
            for i in range(len(unmarked)):
                unmarked[i] = float(f"{unmarked[i] * 2 / 3:.1f}")
        return unmarked, remarks

    


def gpa_to_percentage(target_gpa):
    if target_gpa >= 4.00:
        return 85
    elif target_gpa >= 3.66:
        return 80
    elif target_gpa >= 3.33:
        return 75
    elif target_gpa >= 3.00:
        return 71
    elif target_gpa >= 2.66:
        return 68
    elif target_gpa >= 2.33:
        return 64
    elif target_gpa >= 2.00:
        return 61
    elif target_gpa >= 1.66:
        return 58
    elif target_gpa >= 1.33:
        return 54
    elif target_gpa >= 1.00:
        return 50
    else:
        return 0 
    
# Fetch Current Marks
def fetch_current_marks(student_data, course):
    course_data = student_data.loc[student_data['Course_no'] == course]
    
    if course_data.empty:
        print(f"No data found for course {course}.")
        # Return empty lists and 0 for midterm/final if no data is available
        return [], [], 0, 0
    
    # Ensure that quiz and assignment marks are lists, if marks are 0, replace with None or zero for easier handling
    quiz_marks = course_data[['Quiz1', 'Quiz2', 'Quiz3', 'Quiz4']].fillna(0).values.flatten().tolist()
    assignment_marks = course_data[['Assignment1', 'Assignment2', 'Assignment3', 'Assignment4']].fillna(0).values.flatten().tolist()
    midterm_mark = course_data['MidTerm'].fillna(0).values[0]
    finalterm_mark = course_data['FinalTerm'].fillna(0).values[0]

    return quiz_marks, assignment_marks, midterm_mark, finalterm_mark




# Fetch Student Data Based on Program and Semester
def fetch_student_data(student_registration, student_semester, is_bcs):
    # Determine the correct file path based on the program (BCS or SE)
    semester_num = int(student_semester.split()[-1])
    
    if is_bcs:
        file_path = f'data/Semester{semester_num}CS.csv'
    else:
        file_path = f'data/Semester{semester_num}SE.csv'

    # Load the semester data from the file
    try:
        semester_data = pd.read_csv(file_path)
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return None

    # Filter the data for the specific student
    student_data = semester_data[semester_data['Registration_number'] == student_registration]
    
    if student_data.empty:
        print(f"No data found for registration number {student_registration} in semester {student_semester}")
        return None
    
    return student_data

def get_total_credit_hours(df, semester_col, credit_col):
    """Calculate the total credit hours for a given semester."""
    return df[credit_col].dropna().sum()

def get_courses_by_semester(semester, is_bcs):
    semester_column = semester.replace(" ", "")  # Removes any spaces from the semester name
    if is_bcs:
        if semester_column in courses_cs.columns:
            course_list = courses_cs[semester_column].dropna().tolist()
            # print("courses found", course_list)
        else:
            flash(f"Semester {semester} data not found in BCS courses.")
            return []
    else:
        if semester_column in courses_se.columns:
            course_list = courses_se[semester_column].dropna().tolist()
        else:
            flash(f"Semester {semester} data not found in SE courses.")
            return []
    
    return course_list

def get_course_details(course_no):
    course_row = course_info[course_info['Course_no'] == course_no]
    if not course_row.empty:
        return course_row[['Title', 'credit_hours']].values[0]
    return None, None

# Identify Unmarked Components
def identify_unmarked_components(quiz_marks, assignment_marks, midterm_mark, finalterm_mark):
    # If quiz_marks or assignment_marks are None, replace them with an empty list
    if quiz_marks is None:
        quiz_marks = []
    if assignment_marks is None:
        assignment_marks = []

    # Cast quiz marks as 0 if they are None or 0
    unmarked_quizzes = [f"Quiz{i+1}" for i, mark in enumerate(quiz_marks) if mark == 0 or mark is None]
    # print('unmarked_quizzes :', unmarked_quizzes)
    quiz_marks = [mark if mark is not None else 0 for mark in quiz_marks]  # Replace None with 0 for quizzes

    # Cast assignment marks as 0 if they are None or 0
    unmarked_assignments = [f"Assignment{i+1}" for i, mark in enumerate(assignment_marks) if mark == 0 or mark is None]
    # print('unmarked_assignments :', unmarked_assignments)
    assignment_marks = [mark if mark is not None else 0 for mark in assignment_marks]  # Replace None with 0 for assignments

    # Cast midterm and final term as 0 if they are None or 0
    unmarked_midterm = 0 if midterm_mark == 0 or midterm_mark is None else midterm_mark
    # print('unmarked_midterm :', unmarked_midterm)
    
    unmarked_finalterm = 0 if finalterm_mark == 0 or finalterm_mark is None else finalterm_mark
    # print('unmarked_finalterm :', unmarked_finalterm)
    
    return unmarked_quizzes, unmarked_assignments, unmarked_midterm, unmarked_finalterm



def find_courses_with_prereq(input_course, course_df, course_list=None):
    if course_list is None:
        course_list = []

    # Find all courses that have the input course as a prerequisite
    courses_with_prereq = course_df[course_df['prerequisite'].str.contains(input_course, na=False)]['Course_no'].values

    # If any courses were found, iterate through them
    for course in courses_with_prereq:
        if course not in course_list:
            course_list.append(course)
            # Recursively check if this course is a prerequisite for others
            find_courses_with_prereq(course, course_df, course_list)

    # Remove duplicates from the list
    course_list = list(set(course_list))
    return course_list

def process_courses_for_warnings_suggestions(semesters, course_data, course_difficulty_df):
    warnings = []
    suggestions = []
    factors = []
    
    for semester in semesters:
        # Extract course list for the current semester
        course_list = course_data[f'Semester{semester}'].dropna().tolist()
        
        for course in course_list:
            # Find dependent courses (prerequisites) for the current course
            dependent_courses = find_courses_with_prereq(course, course_difficulty_df)
            
            # Filter dependent courses to include only those present in course_data
            filtered_dependent_courses = [dep_course for dep_course in dependent_courses 
                                          if any(course_data.isin([dep_course]).any())]
            
            
            course_details = course_difficulty_df[course_difficulty_df['Course_no'] == course]
            
            # Ensure course_details is not empty
            if not course_details.empty:
                difficulty = course_details['difficulty_level_encoded'].values[0]
                is_prerequisite = course_details['prerequisite'].values[0] != 'none'
                factors.append(f"{course_details['Title'].values[0]} (Difficulty: {course_details['difficulty_level'].values[0]})")
                
                # If the course has prerequisites and difficulty is high
                if is_prerequisite or difficulty > 3:
                    # Prepare a table-like warning message for filtered dependent courses
                    dependent_courses_table = f"Current course: {course} (Semester {semester})\n"
                    dependent_courses_table += "Dependent courses:\n"
                    dependent_courses_table += "{:<15} {:<15}\n".format("Course", "Semester")
                    
                    for dep_course in filtered_dependent_courses:
                        # Find the semester of the dependent course
                        dep_course_semester = course_data.columns[course_data.isin([dep_course]).any()].str.replace('Semester', '').values
                        if len(dep_course_semester) > 0:
                            dependent_courses_table += "{:<15} {:<15}\n".format(dep_course, dep_course_semester[0])
                        else:
                            dependent_courses_table += "{:<15} {:<15}\n".format(dep_course, "Unknown")

                    warnings.append(f"{course_details['Title'].values[0]} has a chain of prerequisites. "
                                    f"This is a critical course and can lead to late graduation if failed.\n\n"
                                    f"{dependent_courses_table}")
                
                # If the course does not have difficult prerequisites and the difficulty is moderate or less
                if not is_prerequisite and difficulty <= 3:
                    suggestions.append(f"{course_details['Title'].values[0]} is a relatively easy course and can help in increasing your GPA.")

    return factors, warnings, suggestions


def get_course_details(course_no):
    course_row = course_info[course_info['Course_no'] == course_no]
    if not course_row.empty:
        return course_row[['Title', 'credit_hours']].values[0]
    return None, None

# Function to process failed courses and update the course registration
def process_failed_courses(data, current_semester, failed_courses):
    # Convert the data to a pandas DataFrame
    df = data.copy()

    # Initialize variables
    unregistered_courses = []
    max_credit_hours = 21
    already_assigned = set()  # Keep track of already assigned courses
    failed_course_semesters = {}  # Track semesters with failed courses

    # Track failed courses and their semesters
    for sem in range(1, 13):  # Loop from Semester 1 to 12
        semester_col = f'Semester{sem}'
        for failed_course in failed_courses:
            if failed_course in df[semester_col].values:
                # Add an asterisk to the failed course in the semester
                df.loc[df[semester_col] == failed_course, semester_col] = failed_course + '*'
                # Track the semester where the course was failed
                failed_course_semesters[failed_course] = sem

    # Loop through each semester starting from the current one
    for sem in range(current_semester, 13):  # Loop from current to 12th semester
        semester_col = f'Semester{sem}'
        prereq_col = f'Prerequisite{sem}'
        credit_col = f'CreditHours{sem}'

        # Initialize credit hour counter for this semester
        total_credit_hours = get_total_credit_hours(df, semester_col, credit_col)
        
        # Check if any course in this semester has the failed course as a prerequisite
        for failed_course in failed_courses[:]:  # Iterate over a copy to modify failed_courses
            if failed_course in df[prereq_col].values:
                # Find the courses that require the failed course
                failed_course_indices = df[df[prereq_col].str.contains(failed_course, na=False)].index
                for idx in failed_course_indices:
                    course = df.loc[idx, semester_col]
                    credit_hours = df.loc[idx, credit_col]
                    
                    # Add the identified course to the unregistered courses list
                    if course not in already_assigned:
                        unregistered_courses.append(course)
                        already_assigned.add(course)
                    
                    # Remove the course from the current semester and update credit hours
                    df.loc[idx, semester_col] = failed_course  # Re-register the failed course
                    total_credit_hours -= credit_hours
                    df.loc[idx, credit_col] = df.loc[df[semester_col] == failed_course, credit_col].values[0]
                    
                    # Add the dependent course to failed courses so it can be rescheduled
                    if course not in failed_courses:
                        failed_courses.append(course)

                # Remove the current failed course after re-registering
                failed_courses.remove(failed_course)
            else:
                unregistered_courses.append(failed_course)
                failed_courses.remove(failed_course)
                
        # Redistribute courses to future semesters if credit hours exceed the maximum allowed
        if total_credit_hours < max_credit_hours:
            remaining_credit_space = max_credit_hours - total_credit_hours
            for idx in df.index:
                course_credit = df.loc[idx, credit_col]
                if pd.notna(course_credit) and course_credit <= remaining_credit_space:
                    # Add course back if it fits in the available credit hours
                    total_credit_hours += course_credit
                    remaining_credit_space -= course_credit

        # Now move to the next semester and check if unregistered courses are prerequisites
        if sem < 12:  # Stop before the last semester
            next_sem_col = f'Semester{sem + 1}'
            next_prereq_col = f'Prerequisite{sem + 1}'
            next_credit_col = f'CreditHours{sem + 1}'
            
            # For each unregistered course, check if it's a prerequisite for any course in the next semester
            for unregistered_course in unregistered_courses[:]:
                if unregistered_course in df[next_prereq_col].values:
                    unreg_course_indices = df[df[next_prereq_col].str.contains(unregistered_course, na=False)].index
                    for idx in unreg_course_indices:
                        next_course = df.loc[idx, next_sem_col]
                        credit_hours = df.loc[idx, next_credit_col]
                        
                        # Add this course to the unregistered courses list if not already assigned
                        if next_course not in already_assigned:
                            unregistered_courses.append(next_course)
                            already_assigned.add(next_course)
                        
                        # Remove the course from the next semester and re-register the unregistered course
                        df.loc[idx, next_sem_col] = unregistered_course
                        total_credit_hours -= credit_hours
                        
                        # Check and adjust the total credit hours
                        if total_credit_hours + credit_hours <= max_credit_hours or (sem == 8 and total_credit_hours + credit_hours <= 25):
                            df.loc[idx, next_sem_col] = unregistered_course
                            if unregistered_course in unregistered_courses:
                                unregistered_courses.remove(unregistered_course)
                                total_credit_hours += credit_hours

        # If it's the 8th semester, increase the credit hour limit to 25
        if sem == 8:
            max_credit_hours = 25
    
    return df, unregistered_courses

def get_courses_by_semester(semester, is_bcs):
    semester_column = semester.replace(" ", "")  # Removes any spaces from the semester name
    if is_bcs:
        if semester_column in courses_cs.columns:
            course_list = courses_cs[semester_column].dropna().tolist()
        else:
            flash(f"Semester {semester} data not found in BCS courses.")
            return []
    else:
        if semester_column in courses_se.columns:
            course_list = courses_se[semester_column].dropna().tolist()
        else:
            flash(f"Semester {semester} data not found in SE courses.")
            return []
    
    return course_list

def fetch_student_data(student_registration, student_semester, is_bcs):
    # Determine the correct file path based on the program (BCS or SE)
    semester_num = int(student_semester.split()[-1])
    
    if is_bcs:
        file_path = f'data/Semester{semester_num}CS.csv'
    else:
        file_path = f'data/Semester{semester_num}SE.csv'

    # Load the semester data from the file
    try:
        semester_data = pd.read_csv(file_path)
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return None

    # Filter the data for the specific student
    student_data = semester_data[semester_data['Registration_number'] == student_registration]
    
    if student_data.empty:
        print(f"No data found for registration number {student_registration} in semester {student_semester}")
        return None
    
    return student_data




def get_low_gpa_semesters(student_data, current_semester):
    low_gpa_semesters = []
    current_semester_num = int(current_semester.split()[-1])  # Extract semester number from the string
    
    # Loop through all semesters from the current semester to the 8th semester
    for semester in range(current_semester_num, 9):
        gpa_column = f'GPA_Semester_{semester}'
        if gpa_column in student_data.columns:
            gpa_value = student_data[gpa_column].iloc[0]  # Get the first row value for the GPA column
            if gpa_value < 2:
                low_gpa_semesters.append(semester)
    
    # Ensure the current semester is included in the list
    if current_semester_num not in low_gpa_semesters:
        low_gpa_semesters.append(current_semester_num)
    
    return low_gpa_semesters

prereq_dict = {}
credit_hours_dict = {}



def register_unregistered_courses(unregistered_courses, updated_df_semesters_only, course_and_credit_hours, prereq_dict, current_semester):
    # Helper function to calculate total credit hours for a semester
    def get_total_credit_hours(semester_courses, course_credit_dict):
        credit_hours = 0
        for course in semester_courses:
            if pd.notna(course) and course in course_credit_dict:
                credit_hours += course_credit_dict[course]
        return credit_hours

    # Helper function to check if prerequisites for a course are registered
    def prerequisites_met(prereqs, registered_courses):
        return all(prereq in registered_courses for prereq in prereqs)

    # Helper function to find the semester up until which all prerequisites are met
    def get_semester_up_to_prereqs_met(course, prereq_dict, updated_df):
        prereqs = prereq_dict.get(course, [])
        print('prereqs', prereqs)
        max_semester = 0
        for semester in range(1, 13):
            semester_courses = updated_df[f'Semester{semester}'].dropna().values
            if prerequisites_met(prereqs, semester_courses):
                print("semester ipto which prereqs are met", semester)
                max_semester = semester
            else:
                continue
        return max_semester

    # Filter unregistered courses that are not in course_and_credit_hours
    valid_courses = [course for course in unregistered_courses if course in course_and_credit_hours]
    invalid_courses = [course for course in unregistered_courses if course not in course_and_credit_hours]

    if invalid_courses:
        print(f"These courses are not in course_and_credit_hours: {invalid_courses}")

    # Sort valid unregistered courses by credit hours (descending order)
    valid_courses = sorted(
        valid_courses, 
        key=lambda course: course_and_credit_hours.get(course, 0),
        reverse=True
    )
    print('valid_courses : ',valid_courses)
    current_semester = int(current_semester.split()[-1])
    print(current_semester)

    # Loop over each valid unregistered course and check if it can be registered in a future semester
    for course in valid_courses[:]:  # Copy the list to safely remove elements
        prereq_chain = prereq_dict.get(course, [])
        if len(prereq_chain) == 0:
            prereq_met_semester = current_semester
        else:
            prereq_met_semester = get_semester_up_to_prereqs_met(course, prereq_dict, updated_df_semesters_only)
        print('course : ',course, 'prereq_met_semester : ',prereq_met_semester)

        # Try to register the course in semesters after prerequisites are met
        semester_to_continue_from = (prereq_met_semester if prereq_met_semester > current_semester else current_semester) + 1
        for semester in range(semester_to_continue_from, 13):
            semester_courses = updated_df_semesters_only[f'Semester{semester}'].dropna().values
            print('sem :', semester,' sem courses',semester_courses)
            total_credit_hours = get_total_credit_hours(semester_courses, course_and_credit_hours)
            print('sem :', semester,'sem credit hours', total_credit_hours)
            course_credit_hours = course_and_credit_hours.get(course, 0)
            print('course : ',course_credit_hours)

            max_credit_hours = 25 if semester == 8 else 21
            if total_credit_hours + course_credit_hours <= max_credit_hours:
                available_spots = updated_df_semesters_only[f'Semester{semester}'].isna()
                print('available spots:', available_spots)
                if available_spots.any():
                    first_empty_spot = available_spots.idxmax()
                    updated_df_semesters_only.at[first_empty_spot, f'Semester{semester}'] = course
                    valid_courses.remove(course)
                break

    return updated_df_semesters_only, valid_courses







# Recursive function to get full prerequisite chain based on credit hours
def get_prereq_chain(course, prereq_dict, credit_hours_dict, min_credit_hours=0, chain=None):
    if chain is None:
        chain = []
    if course not in prereq_dict or not prereq_dict[course]:
        return chain
    
    # Only consider courses that have more credit hours than the minimum required
    if credit_hours_dict.get(course, 0) >= min_credit_hours:
        for prereq in prereq_dict[course]:
            if prereq not in chain:  # Avoid circular dependencies
                chain.append(prereq)
                get_prereq_chain(prereq, prereq_dict, credit_hours_dict, min_credit_hours, chain)
    return chain

def create_prerequisite_chains_for_unregistered(unregistered_courses, prereq_dict, credit_hours_dict):
    prerequisite_chains = {}
    for course in unregistered_courses:
        if course in prereq_dict:  # Only process courses that have prerequisites
            prereq_chain = get_prereq_chain(course, prereq_dict, credit_hours_dict, min_credit_hours=3)  # Example: min_credit_hours of 3
            prerequisite_chains[course] = prereq_chain
    return prerequisite_chains

def get_current_semester(registration_number):
    student_row = students_data[students_data['Registration_number'] == registration_number]
    if not student_row.empty:
        return student_row['Current_Semester'].values[0]
    return None

# New function to generate GPA for each semester
def generate_gpa():
    return round(random.uniform(2.0, 4.0), 2)  # Random GPA above 2.0

# Preprocessing function
def preprocess_data(data):
    data = data[['GPA_Semester_1','GPA_Semester_2','GPA_Semester_3','GPA_Semester_4','GPA_Semester_5','GPA_Semester_6','GPA_Semester_7','GPA_Semester_8','Average_CourseCode_HUM_Gpa','Average_CourseCode_CSC_Gpa','Academic_Standing_University','Academic_Standing_Department','Academic_Standing_Batch']].copy()
    data = data.dropna(subset=["GPA_Semester_8"])
    threshold = 0.2
    high_missing_cols = [col for col in data.columns if data[col].isnull().sum() / len(data) > threshold]
    data = data.drop(columns=high_missing_cols)
    columns_to_impute = data.columns[data.isnull().any()]
    for col in columns_to_impute:
        if data[col].dtype == 'object':
            data[col].fillna(data[col].mode()[0], inplace=True)
        else:
            data[col].fillna(data[col].mean(), inplace=True)
    return data

# Function to predict graduation status
def predict_graduation(data, model):
    X = preprocess_data(data)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    predictions = model.predict(X_scaled)
    try:
        probabilities = model.predict_proba(X_scaled)
    except AttributeError:
        probabilities = None
    return X, predictions, probabilities


model_files = {
    "GPA_Semester_2": r"Model_Files/Catboost_2ndSemester0.8071.pkl",
    "GPA_Semester_3": r"Model_Files/Catboost_3rdSemester0.8072.pkl",
    "GPA_Semester_4": r"Model_Files/ExtraTrees_4thSemester0.8052.pkl",
    "GPA_Semester_5": r"Model_Files/LightGBM_5thSemester0.7878.pkl",
    "GPA_Semester_6": r"Model_Files/Catboost_6thSemester0.7976.pkl",
    "GPA_Semester_7": r"Model_Files/Catboost_7thSemester0.8154.pkl",
    "GPA_Semester_8": r"Model_Files/Catboost_8thSemester0.0.8041.pkl"
}

# Load models into memory
models = {}
for semester, file_path in model_files.items():
    with open(file_path, 'rb') as f:
        models[semester] = pickle.load(f)
    
# Helper function to load models
def custom_load_model(model_path):
    try:
        with open(model_path, 'rb') as file:
            model = pickle.load(file)
        return model
    except Exception as e:
        print(f"Error loading model from {model_path}: {e}")
        return None

# Function to predict GPA

def predict_gpa(data, model, semester):
    # Convert the data to a numpy array
    X = data.to_numpy()

    # Predict GPA using the model
    gpa_pred = model.predict(X)
    print('prediction for semester done: ',semester)

    # If the prediction is an array, round each prediction
    if isinstance(gpa_pred, np.ndarray):
        gpa_pred = np.round(gpa_pred, 2)  # Use np.round for arrays
    else:
        gpa_pred = round(gpa_pred, 2)  # Use round for a single prediction

    # Add the GPA predictions to the dataframe
    data[f'GPA_Semester_{semester}'] = gpa_pred


    return data

