import process_FAST
import term_model
import sys
import pandas as pd
import inspect
    

def main(fast_file, cohort):
    cohort_fast = process_FAST.excel2cohorts(fast_file)[cohort]
    cohort_sparc = term_model.get_scores_for(cohort, 2)
    records = {}
    for fast in cohort_fast:
        records[fast.id_num] = fast
    for sparc in cohort_sparc:
        if sparc.id_num in records:
            bonus = 1 if records[sparc.id_num].total_reports() >= 3 else 2
            records[sparc.id_num].sparc_score = sparc.score
            records[sparc.id_num].medium_bonus = bonus if 4 <= sparc.score <= 5 else 0
            records[sparc.id_num].high_bonus = bonus if sparc.score <= 3 else 0
    candidates = list(records.values())
    candidates = [c for c in candidates if c.medium + c.medium_bonus + c.high + c.high_bonus >= 2]
    candidates.sort(key=lambda candidate:
    (-(candidate.medium + candidate.medium_bonus + candidate.high + candidate.high_bonus),
     candidate.sparc_score,
     -(candidate.high + candidate.high_bonus),
     -(candidate.medium + candidate.medium_bonus),
     candidate.last_name,
     candidate.first_name,
     candidate.id_num))
    candidates = [tuple(record) + (record.sparc_score, record.medium_bonus, record.high_bonus) for record in candidates]
    output = pd.DataFrame(candidates, columns=list(inspect.getmembers(process_FAST.FastStudent)[0][1].keys()) +
                                              ['SPARC Score', 'Medium Bonus', 'High Bonus'])
    output.to_excel(f"..\\SPARC_Records\\FAST_SPARC_{cohort}_sophomore.xlsx")


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: sophomores fast_file cohort")
    else:
        main(f"..\\SPARC_Records\\{sys.argv[1]}", sys.argv[2])