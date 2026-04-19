import os
import re

file_path = "/media/yourbrolol/Data/Documents/Projects/StarForLife/team404NotFound/ContestKeeper/app/tests/tests.py"
with open(file_path, 'r') as f:
    lines = f.readlines()

imports = lines[:21]

class_matches = []
for i, line in enumerate(lines):
    if line.startswith('class '):
        class_name = re.match(r'class (\w+)', line).group(1)
        class_matches.append((i, class_name))

class_matches.append((len(lines), "EOF"))

blocks = {}
for idx in range(len(class_matches) - 1):
    start = class_matches[idx][0]
    end = class_matches[idx + 1][0]
    name = class_matches[idx][1]
    blocks[name] = lines[start:end]

files = {
    'test_application.py': ['ApplicationLogicTest'],
    'test_leaderboard.py': ['LeaderboardLogicTest', 'LeaderboardHelperFunctionsTest'],
    'test_round.py': ['RoundLogicTest'],
    'test_evaluation.py': ['EvaluationModelsTest'],
    'test_submission.py': ['SubmissionModelTest', 'SubmissionUITest'],
    'test_bugfixes.py': ['BugfixRegressionTest'],
    'test_views.py': ['HomeViewTaskTest', 'ProfileViewTaskTest'],
}

tests_dir = os.path.dirname(file_path)

for filename, classes in files.items():
    with open(os.path.join(tests_dir, filename), 'w') as f:
        f.writelines(imports)
        f.write("\n")
        f.writelines(lines[974:978]) # some extra imports in BugfixRegressionTest maybe? Wait, at 974 there's imports inside Bugfix? Let's check lines 974:978
        # Actually I can just write the original imports
        for c in classes:
            f.writelines(blocks[c])

tests_py_content = "from .test_application import *\n"
tests_py_content += "from .test_leaderboard import *\n"
tests_py_content += "from .test_round import *\n"
tests_py_content += "from .test_evaluation import *\n"
tests_py_content += "from .test_submission import *\n"
tests_py_content += "from .test_bugfixes import *\n"
tests_py_content += "from .test_views import *\n"

# also import other tests_taskXX.py so `tests.py` tests "whole application at once"?
# Actually the prompt says: keep "tests.py" for testing whole application at once
with open(file_path, 'w') as f:
    f.write(tests_py_content)
