from dataclasses import dataclass

import process_details_FAST
import sys

from util import augment_fast, DataDictionary


@dataclass
class Freshman:
    id_num: str
    hs_gpa: float


def main(fast_file, cohort):
    cohort_fast = process_details_FAST.excel2cohorts(fast_file)[cohort]
    data = DataDictionary()
    id_gpa = [Freshman(row['id_num'], float(row['HS GPA Unweighted']))
              for index, row in data.rows.iterrows()]

    output = augment_fast(cohort_fast, id_gpa,
                          lambda iag: iag.hs_gpa,
                          lambda gpa: 3.0 <= gpa < 3.5,
                          lambda gpa: gpa < 3.0,
                          "Unweighted High School GPA")
    output.to_excel(f"..\\SPARC_Records\\FAST_SPARC_{cohort}_freshmen.xlsx")


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: freshmen_fall fast_file cohort")
    else:
        main(f"..\\SPARC_Records\\{sys.argv[1]}", sys.argv[2])