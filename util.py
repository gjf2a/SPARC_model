from SPARC_lib import *
import pandas as pd

import process_details_FAST

default_dictionary = "..\\SPARC_Records\\Data_Dictionary.xlsx"
default_courses = "..\\SPARC_Records\\Course_History.xlsx"


class DataDictionary:
    def __init__(self, data_file=default_dictionary, course_file=default_courses):
        self.rows = pd.read_excel(data_file)
        self.indexed = {row['id_num']: row for index, row in self.rows.iterrows()}
        courses = pd.read_excel(course_file)
        self.student2courses = load_course_table(courses)


class AugmentedRecord:
    def __init__(self, fast: process_details_FAST.DetailFastStudent, other, med_bonus_criterion, high_bonus_criterion):
        self.fast = fast
        self.other = other
        bonus = 1 if fast.total_reports() >= 3 else 2
        self.medium_bonus = bonus if med_bonus_criterion(other) else 0
        self.high_bonus = bonus if high_bonus_criterion(other) else 0

    def total_high(self):
        return len(self.fast.high) + self.high_bonus

    def total_medium(self):
        return len(self.fast.moderate) + self.medium_bonus

    def total_fast(self):
        return self.total_high() + self.total_medium()

    def __iter__(self):
        all_items = [self.fast.id_num, self.fast.first_name, self.fast.last_name, self.fast.cohort,
                     self.fast.moderate, self.fast.high,
                     self.other, self.total_fast(), len(self.fast.low), len(self.fast.moderate), self.medium_bonus,
                     len(self.fast.high), self.high_bonus, len(self.fast.missing)]
        all_items.reverse()
        total = len(all_items)
        for i in range(total):
            yield all_items.pop()


def augment_fast(cohort_fast, cohort_other, other_selector, med_bonus_criterion, high_bonus_criterion,
                 other_column_name):
    fast_records = {}
    augmented_records = {}
    for fast in cohort_fast:
        fast_records[fast.id_num] = fast
    for other in cohort_other:
        if other.id_num in fast_records:
            augmented_records[other.id_num] = AugmentedRecord(fast_records[other.id_num], other_selector(other),
                                                              med_bonus_criterion, high_bonus_criterion)
    candidates = list(augmented_records.values())
    candidates = [c for c in candidates if c.total_fast() >= 2]
    candidates.sort(key=lambda c: (-c.total_fast(), -len(c.fast.high), -len(c.fast.moderate), c.other,
                                   c.fast.last_name, c.fast.first_name, c.fast.id_num))

    column_headers = ['ID Num', 'First Name', 'Last Name', 'Cohort', 'Moderate Concern Courses',
                      'High Concern Courses', other_column_name, 'Total Score',
                      'Low', 'Medium', 'Medium Bonus', 'High', 'High Bonus', 'Missing']
    candidates = [tuple(c) for c in candidates]
    return pd.DataFrame(candidates, columns=column_headers)