1→The code must be simple, clean. You can follow the "KISS" method.
2→After generate a .md file for a new features/activities, you must gather in into a folder specifically, for example: "docs". In order to create a consistency and organized folder structure for next claude session.
3→When you try to recommend me for any approach to complete a task, you must make a comparition between the approaches and recommend me the best one.
4→I want you to keep tracking progress of everything is in progress/completed. All completed tasks must be documented in a single progress log at "docs/PROGRESS.md". Each task entry must be no longer than 10 lines and include: task name, status, files modified (with line numbers), what changed, approach used, and testing notes.
5→For python files, you must organize them in a folder specifically, for example: "python", "testpython".
6→Use TodoWrite tool for live progress tracking during task execution. Update docs/PROGRESS.md only after task completion.
7→A task is defined as done just when I say it is done. If I did not say it is done, it is not done.
8→All code changes must include basic testing/validation before marking complete.
9→Implement error handling only at system boundaries (user input, external APIs, file I/O). Trust internal code.
10→Document external dependencies and their purpose in docs/DEPENDENCIES.md when adding new packages.
11→Before marking complex tasks complete, provide brief code explanation with key decisions for user review.
12→Always use absolute paths in documentation. Use project-relative paths in code.
13→At session start, read docs/PROGRESS.md to understand project context before beginning new work.
