# petlja_api

A python library for interacting with the [petlja.org](https://petlja.org/) API.

## Installation

```
pip install petlja-api
```

## Basic usage

```py
import petlja_api as petlja

session = petlja.login()

# Create problem
prob_id = petlja.create_problem(session, name="My Problem", alias="my-prob")
petlja.upload_testcases(session, prob_id, "my-prob/testcases.zip")
petlja.upload_statement(session, prob_id, "my-prob/statement.md")

# Create competition
comp_id = petlja.create_competition(session, name="My Competition", alias="my-comp")
petlja.add_problem(session, comp_id, prob_id)

# Upload solution
score = petlja.submit(session, prob_id, "my-prob/sol.cpp", comp_id)
```
