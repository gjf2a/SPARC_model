from SPARC_lib import *
import sys
import pandas as pd


# Organizational functions
def sum_scores(score_fn_list):
    return lambda row, term: sum_none([score_fn(row, term) for score_fn in score_fn_list])


def sum_none(score_list):
    if None in score_list:
        return None
    else:
        return sum(score_list)


def score_cohort(data_dictionary, score_func, cohort, term):
    result = []
    for index, row in data_dictionary.iterrows():
        if row['cohort'] == cohort:
            score = score_func(row, term)
            if score is not None:
                result.append((row['id_num'], row['last_name'], row['first_name'], row['cohort'], term, score))
    return result


# Scoring functions

# Foundational.
def gpa_score(row, term):
    career_gpa = row[f'Term {term} Career GPA']
    if career_gpa is None:
        return None
    if career_gpa < 2.0:
        return 0
    elif career_gpa < 2.5:
        return 1
    elif career_gpa < 3.0:
        return 2
    elif career_gpa < 3.5:
        return 3
    else:
        return 4


# Maybe slightly helpful.
def gpa_diff_penalty(row, term):
    hendrix = float_filter_nan(row[f'Term {term} Career GPA'])
    high_school = float_filter_nan(row['HS GPA Unweighted'])
    if hendrix is None or high_school is None:
        return None
    else:
        return -1 if hendrix - high_school < -0.5 else 0


# Helpful.
def explorations(row, term):
    if row['Explorations grade'] == 'A' and term < 3:
        return 1
    else:
        return 0


# Helpful.
def tec(row, term):
    grade = str_filter_nan(row['TEC grade'])
    if len(grade) > 0 and grade in 'AB':
        return 1
    return 0


# Very helpful
def chem(student2courses, row, term):
    id_num = row['id_num']
    if id_num in student2courses:
        course_list = student2courses[row['id_num']]
        if has_taken(course_list, 'CHEM', '110'):
            if term == 1:
                return 1
            elif has_taken(course_list, 'CHEM', '120'):
                return 2
            else:
                return 0
        else:
            return 1
    else:
        return 0


# Slightly helpful.
def summer_checklist(row, term):
    value = row['% Summer Tasks Completed On Time']
    if type(value) == str and '%' in value:
        value = value[0:value.find('%')]
    checklist = float_filter_nan(value)
    if term <= 2 and checklist is not None and checklist > 68:
        return 1
    else:
        return 0


def trajectory(row, start, end):
    then = float_filter_nan(row[f'Term {start} Career GPA'])
    now = float_filter_nan(row[f'Term {end} Career GPA'])
    return now - then if now is not None and then is not None else 0.0


def trajectory_score(row, start, end):
    traj = trajectory(row, start, end)
    if traj > 0.5:
        return 1
    elif traj < -0.5:
        return -1
    else:
        return 0


# Helpful.
def global_trajectory(row, term):
    return trajectory_score(row, 1, term) if term > 2 else 0


# Helpful.
def local_trajectory(row, term):
    return trajectory_score(row, term - 1, term) if term > 1 else 0


sport_years = 5


def activity_participated(row, activity, columns_per_year):
    year_activities = {i:[] for i in range(1, sport_years + 1)}
    for i in range(1, sport_years + 1):
        for j in range(columns_per_year):
            key = f"{activity}_{i}_{chr(ord('A') + j)}"
            value = str_filter_nan(row[key])
            if len(value) > 0:
                year_activities[i].append(value)
    return year_activities


def sports_played(row):
    return activity_participated(row, 'sport', 3)


def arts_performed(row):
    return activity_participated(row, 'perform_art', 4)


# Helpful.

def played_any_sport_twice(row):
    sports = set()
    for played in sports_played(row).values():
        for sport in played:
            if sport in sports:
                return True
            else:
                sports.add(sport)
    return False


def sports_score(row, term):
    if term >= 3 and played_any_sport_twice(row):
        return 1
    else:
        return 0


# Helpful.
def sports_one_year_penalty(row, term):
    if term >= 3:
        played = sports_played(row)
        if len(played[1]) == 0:
            return 0
        for sport in played[1]:
            if sport in played[2]:
                return 0
        return -1
    else:
        return 0


# Slightly hurts. But intuitively it should be helpful. Keep.

def performing_arts_2_year(row):
    arts = set()
    for played in arts_performed(row).values():
        for art in played:
            if art in arts:
                return True
            else:
                arts.add(art)
    return False


def art_score(row, term):
    if term >= 3 and performing_arts_2_year(row):
        return 1
    else:
        return 0


# Putting it all together
def main(excel_filename: str, course_history_filename: str, term: int, cohort: str):
    data_dictionary = pd.read_excel(excel_filename)
    courses = pd.read_excel(course_history_filename)
    student2courses = load_course_table(courses)
    score_func_list = [summer_checklist, gpa_score, explorations, tec, lambda row, term: chem(student2courses, row, term), local_trajectory, global_trajectory, sports_one_year_penalty, sports_score, art_score]
    student_scores = score_cohort(data_dictionary, sum_scores(score_func_list), cohort, term)
    student_scores.sort(key=lambda k: (k[5], k[1], k[2]))
    output = pd.DataFrame([entry for entry in student_scores],
                          columns=['id_num', 'last_name', 'first_name', 'cohort', 'term', 'score'])
    output.to_excel(f"..\\SPARC_Records\\Score_Report_{cohort}_{term}.xlsx")


if __name__ == '__main__':
    print(sys.argv)
    if len(sys.argv) < 3:
        print("Usage: term_model term cohort [data_dictionary_file.xlsx] [course_history_file.xlsx]")
    else:
        if len(sys.argv) == 5:
            dfile = sys.argv[3]
            cfile = sys.argv[4]
        else:
            dfile = "..\\SPARC_Records\\Data_Dictionary.xlsx"
            cfile = "..\\SPARC_Records\\Course_History.xlsx"
        main(dfile, cfile, int(sys.argv[1]), sys.argv[2])
