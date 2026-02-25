# team404NotFound

# Requirements
- Python 3.13.0 or later (check using python / python3 --version),
- Django 6.0.2,
- Daphne 4.2.1.

# Installation & startup guide
This part will thoroughly explain how to install the needed packages (if not installed yet), how to run and what often issues may occur.

The required python / pip version and packages are already preinstalled in .venv, **however** they might be incompatible with your OS. (at the time of 25.02.2026) the .venv packages were downloaded on a machine using Windows 11 operating system, so python and most packages are in .exe format.

To know if the preinstalled .venv is compatible with your os, locate to the project's root directory and type:

On Windows 10 / 11:
```pwsh
.venv\Scripts\Activate.ps1 # or if using cmd instead of pwsh, type: .\venv\Scripts\activate.bat
cd ContestKeeper # or whatever the main application is called
python manage.py runserver # should raise no errors, **especially no ImportErrors**
```

On Linux / MacOS:
```bash
source .venv/bin/activate # use sudo prefix if needed
cd ContestKeeper # or whatever the main application is called
python manage.py runserver # should raise no errors, **especially no ImportErrors**
```

## If no errors are raised, proceed to the usage guide. Otherwise, continue this guide.

Here will be shown exactly how to manually reinstall .venv step by step.

### First of all, head to the project root, and delete .venv:

Using powershell:
```pwsh
del /s /q .venv # or whatever it is named as
```

Using bash:
```bash
rm -rf .venv # use sudo if needed
```

### Second of all, lets create a new .venv (requires Python installed, and pip logged in Path):

**You can install python by visiting [Python's official page](https://www.python.org/downloads/ "Download Python") or via your package manager**

Pwsh:
```pwsh
python -m venv .venv # change .venv to whatever name you want, but recommended to leave it as it is
```

Bash:
```bash
python3 -m venv .venv # alternatively, try python instead of python3
```

### Next, lets install the needed packages:

**(Before proceeding, make sure there is a "(venv)" prefix before your command line)**

Pwsh:
```pwsh
pip install django daphne # will also install all the required packages those two rely on
```

Bash
```bash
sudo apt install python-pip # EXAMPLE python pip installation, your OS might use another package manager 
pip install django daphne # will also install all the required packages those two rely on
```

## Now, once everything's set up, go back to the start of the guides and try running the app. If it does not run, try finding your issue here or in the internet:

### Common issues:
1. You might have installed python via python installer, and forgot to check "Add to PATH" flag or something similar. Can be resolved by either manually adding it to PATH (complex, wont be explained there) or by reinstalling the python and checking the flag, mentioned earlier.
2. Your Python might be outdated. Django and daphne support a variety of versions, but there may be certain compatability issues. In that case, please proceed to reinstall the needed python / package version.