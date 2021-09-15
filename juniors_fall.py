import process_details_FAST
import term_model
import sys

from util import DataDictionary, augment_fast


def main(fast_file, cohort):
    cohort_fast = process_details_FAST.excel2cohorts(fast_file)[cohort]
    cohort_sparc = term_model.get_scores_for(cohort, 4, DataDictionary())
    output = augment_fast(cohort_fast, cohort_sparc,
                          lambda sparc: sparc.score,
                          lambda score: score == 3,
                          lambda score: score <= 2,
                          "SPARC Score")
    output.to_excel(f"..\\SPARC_Records\\FAST_SPARC_{cohort}_junior.xlsx")


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: juniors_fall fast_file cohort")
    else:
        main(f"..\\SPARC_Records\\{sys.argv[1]}", sys.argv[2])