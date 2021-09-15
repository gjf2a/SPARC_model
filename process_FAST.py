import sys
import inspect
from dataclasses import dataclass
from typing import List, Dict
import pandas as pd


@dataclass
class FastStudent:
    id_num: str
    first_name: str
    last_name: str
    cohort: str
    low: int
    medium: int
    high: int
    missing: int

    def total_reports(self):
        return self.low + self.medium + self.high

    def __iter__(self):
        for key in inspect.getmembers(self)[0][1].keys():
            yield self.__dict__[key]


def split_by_cohort(students: List[FastStudent]) -> Dict[str,List[FastStudent]]:
    result = {}
    for s in students:
        if s.cohort not in result:
            result[s.cohort] = []
        result[s.cohort].append(s)
    return result


def excel2cohorts(excel_file: str) -> Dict[str,List[FastStudent]]:
    fast_data = pd.read_excel(excel_file)
    students = [FastStudent(id_num=row['id num'],
                            first_name=row['first name'],
                            last_name=row['last name'],
                            cohort=row['cohort cde'],
                            low=int(row['low']),
                            medium=int(row['medium']),
                            high=int(row['high']),
                            missing=int(row['missing']))
                for index, row in fast_data.iterrows()]

    return split_by_cohort(students)


def main(excel_file):
    cohorts = excel2cohorts(excel_file)
    for (cohort, cohort_students) in cohorts.items():
        cohort_students.sort(key=lambda student: (-(student.high + student.moderate), -student.high, -student.moderate))
        output = pd.DataFrame(cohort_students, columns=inspect.getmembers(FastStudent)[0][1].keys())
        output.to_excel(f"..\\SPARC_Records\\FAST_report_{cohort}.xlsx")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: process_FAST FAST_file.xlsx")
    else:
        main(f"..\\SPARC_Records\\{sys.argv[1]}")