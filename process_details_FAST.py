from typing import Dict, List
import pandas as pd

from process_FAST import split_by_cohort


class DetailFastStudent:
    def __init__(self, id_num, first_name, last_name, cohort):
        self.id_num = id_num
        self.first_name = first_name
        self.last_name = last_name
        self.cohort = cohort
        self.low = []
        self.moderate = []
        self.high = []
        self.missing = []

    def total_reports(self):
        return len(self.low) + len(self.moderate) + len(self.high)


def excel2cohorts(excel_file: str) -> Dict[str,List[DetailFastStudent]]:
    student2record = {}
    fast_data = pd.read_excel(excel_file)
    for index, row in fast_data.iterrows():
        id_num = row['id num']
        if id_num not in student2record:
            student2record[id_num] = DetailFastStudent(row['id num'], row['first name'], row['last name'],
                                                       row['cohort cde'])
        student2record[id_num].__dict__[row['concern label'].lower()].append(row['crs cde'])
    return split_by_cohort(student2record.values())