# PythonAnywhere Deployment Checklist

Use this checklist to make sure your GitHub repo contains everything needed before cloning on PythonAnywhere.

## Required files in the repository root

You should see these files at the top level of the repo:

- `app.py`
- `models.py`
- `requirements.txt`
- `pythonanywhere_wsgi.py`
- `README.md`
- `templates/`

## Deploy steps

### 1. Clone the repository

```bash
cd ~
git clone <your-repo-url>
cd Personal-Finance-Manager-V.1
```

### 2. Confirm the required files exist

```bash
pwd
ls
```

### 3. Create and activate a virtualenv

```bash
mkvirtualenv --python=/usr/bin/python3.13 pfms-env
workon pfms-env
```

### 4. Install requirements

```bash
pip install -r requirements.txt
```

### 5. Initialize the database

```bash
python -c "from app import init_db; init_db()"
```

### 6. Configure the WSGI file

Use the example in `pythonanywhere_wsgi.py` and update the path to your username.

### 7. Reload the web app

After saving the WSGI file, reload the app from the PythonAnywhere **Web** tab.
