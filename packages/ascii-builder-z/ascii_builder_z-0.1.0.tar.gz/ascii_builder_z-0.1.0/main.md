Author: 3xboiz 2026 to 3026
All rights reserved by 3xboiz.

You are a senior Python package developer.
I want you to create a full Python package named ascii-builder-z by author Pawan.
Package requirements:
The package module name must be az.
It must generate thick ASCII art using characters █ ▓ ▒.
It must support all letters A–Z and numbers 0–9.
Output must be in the SAME ROW (horizontal ASCII text, not vertical).
API must work like this:
Copy code
Python
import az
az.set.name.pawan = "PAWAN123"
az.print("pawan")
It must also support:
Copy code
Python
az.print("HELLO")
It must support:
spacing control: az.set.space = 3
color control: az.set.color = "red" | "green" | "blue" | "yellow"
Must avoid shadowing built-in print (use builtins.print).
Provide FULL package code:
az/__init__.py
az/core.py
az/ascii_map.py
pyproject.toml
Must give step-by-step Ubuntu/Termux terminal commands using ONLY:
mkdir
cat
pip install . --upgrade
No nano, no vim, no editors.
Must include test file example test.py.
Must explain errors and fixes.
Output must be: ✔ Step-by-step
✔ Copy-paste ready
✔ Fully working
✔ Beginner friendly
✔ Production style
Do NOT skip any file.
Do NOT summarize.
Generate full code