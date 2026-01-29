import pytest

import math
import petlja_api as petlja


def test_submit_ok(sess, comp_with_problems, src_ok):
    cid, _ = comp_with_problems
    pid = petlja.get_added_problem_ids(sess, cid)[0]
    score = petlja.submit_solution(sess, cid, pid, src_ok)
    assert int(score) == 100


def test_submit_wa(sess, comp_with_problems, src_wa):
    cid, _ = comp_with_problems
    pid = petlja.get_added_problem_ids(sess, cid)[0]
    score = petlja.submit_solution(sess, cid, pid, src_wa)
    assert score == "0"


def test_submit_ce(sess, comp_with_problems, src_ce):
    cid, _ = comp_with_problems
    pid = petlja.get_added_problem_ids(sess, cid)[0]
    score = petlja.submit_solution(sess, cid, pid, src_ce)
    assert score == "CE"


@pytest.mark.slow
def test_submit_tle(sess, comp_with_problems, src_tle):
    cid, _ = comp_with_problems
    pid = petlja.get_added_problem_ids(sess, cid)[0]
    score = petlja.submit_solution(sess, cid, pid, src_tle)
    assert score == "0"


def test_submit_detailed_ok(sess, comp_with_problems, src_ok):
    cid, _ = comp_with_problems
    pid = petlja.get_added_problem_ids(sess, cid)[0]
    res = petlja.submit_solution_detailed(sess, cid, pid, src_ok)
    assert res.score == 100
    assert not res.compile_error
    assert all(t.status == "OK" for t in res.testcase_results)
    assert all(t.time_ms is not None and t.time_ms < 1000 for t in res.testcase_results)
    assert all(
        t.memory_mb is not None and t.memory_mb < 256 for t in res.testcase_results
    )


def test_submit_detailed_wa(sess, comp_with_problems, src_wa):
    cid, _ = comp_with_problems
    pid = petlja.get_added_problem_ids(sess, cid)[0]
    res = petlja.submit_solution_detailed(sess, cid, pid, src_wa)
    assert res.score == 0
    assert not res.compile_error
    assert all(t.status == "WA" for t in res.testcase_results)
    assert all(t.time_ms is not None and t.time_ms < 1000 for t in res.testcase_results)
    assert all(
        t.memory_mb is not None and t.memory_mb < 256 for t in res.testcase_results
    )


def test_submit_detailed_ce(sess, comp_with_problems, src_ce):
    cid, _ = comp_with_problems
    pid = petlja.get_added_problem_ids(sess, cid)[0]
    res = petlja.submit_solution_detailed(sess, cid, pid, src_ce)
    assert res.compile_error
    assert not res.testcase_results
    assert res.score == 0


@pytest.mark.slow
def test_submit_detailed_tle(sess, comp_with_problems, src_tle):
    cid, _ = comp_with_problems
    pid = petlja.get_added_problem_ids(sess, cid)[0]
    res = petlja.submit_solution_detailed(sess, cid, pid, src_tle)
    assert res.score == 0
    assert not res.compile_error
    assert all(t.status == "TLE" for t in res.testcase_results)
    assert all(t.time_ms is not None and t.time_ms > 1000 for t in res.testcase_results)


def test_submit_detailed_rte(sess, comp_with_problems, src_rte):
    cid, _ = comp_with_problems
    pid = petlja.get_added_problem_ids(sess, cid)[0]
    res = petlja.submit_solution_detailed(sess, cid, pid, src_rte)
    assert res.score == 0
    assert not res.compile_error
    assert all(t.status == "RTE" for t in res.testcase_results)


def test_submit_detailed_status(sess, comp_with_problems, src_ok_wa):
    cid, _ = comp_with_problems
    pid = petlja.get_added_problem_ids(sess, cid)[0]
    res = petlja.submit_solution_detailed(sess, cid, pid, src_ok_wa)

    expected_statuses = [
        "WA",
        "WA",
        "OK",
        "WA",
        "OK",
        "OK",
        "WA",
        "WA",
        "WA",
        "WA",
        "WA",
    ]
    assert [t.status for t in res.testcase_results] == expected_statuses


def test_submit_detailed_time(sess, comp_with_problems, src_100ms_runtime):
    cid, _ = comp_with_problems
    petlja.add_language(sess, cid, ".py")
    pid = petlja.get_added_problem_ids(sess, cid)[0]
    res = petlja.submit_solution_detailed(sess, cid, pid, src_100ms_runtime)

    times = [t.time_ms for t in res.testcase_results]
    assert all(t is not None and t != math.inf for t in times)
    avg_time = sum(times) / len(times)
    expected_time = 100
    assert avg_time == pytest.approx(expected_time, abs=50)


def test_submit_detailed_memory(sess, comp_with_problems, src_10mb_memory):
    cid, _ = comp_with_problems
    pid = petlja.get_added_problem_ids(sess, cid)[0]
    res = petlja.submit_solution_detailed(sess, cid, pid, src_10mb_memory)

    mems = [t.memory_mb for t in res.testcase_results]
    assert all(m is not None and m != math.inf for m in mems)
    avg_mem = sum(mems) / len(mems)
    expected_mem = 10
    assert avg_mem == pytest.approx(expected_mem, abs=2)
