from pathlib import Path
import petlja_api as petlja
import re
import subprocess


def is_for_testing(source_path):
    is_code = source_path.suffix in petlja.submit.LANGUAGE_IDS
    is_tgen = source_path.stem.endswith("tgen")
    return is_code and not is_tgen


def remove_metadata(st_path):
    cleaned = Path(st_path.parent, st_path.stem + "-cleaned.md")
    is_metadata = False
    lines = open(st_path, encoding="utf-8").readlines()
    with open(cleaned, "w", encoding="utf-8") as cleaned_file:
        for line in lines:
            if line.startswith("---"):
                is_metadata = not is_metadata
                continue
            if not is_metadata:
                cleaned_file.write(line)
    return cleaned


def alias_from_name(name):
    alias = re.sub(r"[^a-zA-Z0-9]", "", name).lower()
    return alias


def open_comp(comp_name):
    comp_alias = alias_from_name(comp_name)
    try:
        comp_id = petlja.create_competition(session, comp_name, comp_alias)
        print(f"Created competition {comp_name}")
    except ValueError:
        comp_id = petlja.get_competition_id(session, comp_alias)
        print(f"Found competition {comp_name}")
    return comp_id


def open_prob(prob_name):
    prob_alias = alias_from_name(prob_name)
    try:
        prob_id = petlja.create_problem(session, prob_name, prob_alias)
        print(f"Created problem {prob_name}")
    except ValueError:
        prob_id = petlja.get_problem_id(session, prob_alias)
        print(f"Found problem {prob_name}")
    return prob_id


session = petlja.login()

comp_path = Path.cwd()
comp_name = comp_path.name
comp_id = open_comp(comp_name)

for problem_path in comp_path.iterdir():
    if problem_path.is_dir():
        problem_name = problem_path.name
        problem_id = open_prob(problem_name)

        subprocess.run(
            ["petljapub", "tests-zip"],
            cwd=problem_path,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        testcases_path = problem_path.joinpath("_build/testcases.zip")
        petlja.upload_testcases(session, problem_id, testcases_path)
        print(f"Uploaded testcases for problem {problem_name}")

        statement_path = next(problem_path.glob("*-st.md"))
        cleaned_statement_path = remove_metadata(statement_path)
        petlja.upload_statement(session, problem_id, cleaned_statement_path)
        cleaned_statement_path.unlink()
        print(f"Uploaded statement for problem {problem_name}")

        petlja.add_problem(session, comp_id, problem_id)
        print(f"Added problem {problem_name} to competition {comp_name}")

        for solution_path in problem_path.iterdir():
            if not is_for_testing(solution_path):
                continue

            solution_name = solution_path.name
            language = solution_path.suffix
            petlja.add_language(session, comp_id, language)
            score = petlja.submit_solution(
                session,
                comp_id,
                problem_id,
                solution_path,
            )
            print(f"Submitted solution {solution_name} for problem {problem_name}")
            print(f"Score: {score}")
