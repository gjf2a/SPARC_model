from SPARC_lib import *
import sys
import pandas as pd
import inspect

default_dictionary = "..\\SPARC_Records\\Data_Dictionary.xlsx"
default_courses = "..\\SPARC_Records\\Course_History.xlsx"


# Organizational functions
def sum_scores(score_fn_list):
    return lambda row, term: sum_none([score_fn(row, term) for score_fn in score_fn_list])


def sum_none(score_list):
    if None in score_list:
        return None
    else:
        return sum(score_list)


@dataclass
class ScoredStudent:
    id_num: str
    last_name: str
    first_name: str
    cohort: str
    baseline_term: int
    last_term_enrolled: int
    score: int

    def persisted(self):
        return self.last_term_enrolled > self.baseline_term


def row2scored(row, term, cohort, score_func, student2courses):
    if row['cohort'] == cohort:
        score = score_func(row, term)
        if score is not None:
            id_num = row['id_num']
            return ScoredStudent(id_num=id_num,
                                 last_name=row['last_name'],
                                 first_name=row['first_name'],
                                 cohort=cohort,
                                 baseline_term=term,
                                 last_term_enrolled=latest_enrolled_term(cohort, student2courses[id_num]),
                                 score=score)


def score_cohort(data_dictionary, student2courses, score_func, cohort, term):
    result = []
    for index, row in data_dictionary.iterrows():
        record = row2scored(row, term, cohort, score_func, student2courses)
        if record:
            result.append(record)
    result.sort(key=lambda k: (k.score, k.last_name, k.first_name))
    return result


def latest_enrolled_term(cohort, course_records):
    return max(course_record.semester_number('20' + cohort[2:4]) for course_record in course_records)


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


def get_scores_for(cohort: str, term: int, exclusion=True, excel_filename=default_dictionary,
                   course_history_filename=default_courses) -> List[ScoredStudent]:
    data_dictionary = pd.read_excel(excel_filename)
    courses = pd.read_excel(course_history_filename)
    student2courses = load_course_table(courses)
    score_func_list = [summer_checklist, gpa_score, explorations, tec, lambda row, term: chem(student2courses, row, term), local_trajectory, global_trajectory, sports_one_year_penalty, sports_score, art_score]
    student_scores = score_cohort(data_dictionary, student2courses, sum_scores(score_func_list), cohort, term)
    if exclusion:
        student_scores = [entry for entry in student_scores if entry.persisted()]
    return student_scores


# Putting it all together
def main(excel_filename: str, course_history_filename: str, term: int, cohort: str, exclusion: bool):
    student_scores = get_scores_for(cohort, term, exclusion, excel_filename, course_history_filename)
    output = pd.DataFrame(student_scores, columns=inspect.getmembers(ScoredStudent)[0][1].keys())
    output.to_excel(f"..\\SPARC_Records\\Score_Report_{cohort}_{term}.xlsx")


if __name__ == '__main__':
    print(sys.argv)
    if len(sys.argv) < 3:
        print("Usage: term_model term cohort [data_dictionary_file.xlsx] [course_history_file.xlsx] [-x]")
        print(" -x: Exclude students whose last term enrolled is <= analysis term")
    else:
        if len(sys.argv) >= 5:
            dfile = sys.argv[3]
            cfile = sys.argv[4]
        else:
            dfile = default_dictionary
            cfile = default_courses
        main(dfile, cfile, int(sys.argv[1]), sys.argv[2], '-x' in sys.argv)
