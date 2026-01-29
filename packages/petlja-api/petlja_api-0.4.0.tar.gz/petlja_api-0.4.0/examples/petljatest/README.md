# petljatest

Automatically create a competition, add its problems and test all of their solutions on [arena.petlja.org](https://arena.petlja.org/)

## Usage

Directory structure should be [petljapub](https://pypi.org/project/petljapub/) compatible

```
00_competition/
├── 01_problem1
│   ├── problem1.cpp
│   ├── problem1.py
│   ├── problem1-sol.md
│   ├── problem1-st.md
│   ├── problem1-tgen.cpp
│   └── scoring.yaml
├── 02_problem2
│   ├── problem2.cpp
│   ├── problem2.cs
│   ├── problem2.py
│   ├── problem2-scoring.yaml
│   ├── problem2-sol.md
│   ├── problem2-st.md
│   └── problem2-tgen.cpp
├── ...
```

Run script from top-level competition directory

```
$ cd 00_competition/
$ python3 petljatest.py
Petlja username: testacc
Petlja password: 
```

Example output:

```
Created competition 00_example_competition
Found problem 01_problem1
Uploaded testcases for problem 01_problem1
Uploaded statement for problem 01_problem1
Added problem 01_problem1 to competition 00_example_competition
Submitted solution problem1.py for problem 01_problem1
Score: 10
Submitted solution problem1.cs for problem 01_problem1
Score: 0
Submitted solution problem1.cpp for problem 01_problem1
Score: 0
Found problem 02_problem2
...
```

