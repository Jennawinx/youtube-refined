
## Developement

Scope: single user desktop app

STACK
- Server: Python FastAPI Sqlite (probably pywebview)
- Client: React Typescript (maybe DaisyUI)

### Server

```sh
cd ./v2/server/
```

#### Setup

##### Windows
```sh
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn main:app --reload
```

##### Mac
```sh
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
``` 

##### Add VSCODE Support
```
Go to extensions, install Python
Go to extensions, install FastAPI
Go to extensions, install Black Formatter
Ctrl + Shift + P > Python: Select Interpreter > Find python.exe under .venv
```

##### Add Package
```sh
# Start env first
pip install <package_name>
pip freeze > requirements.txt
```

##### How DB model was derived from V1
```sh
pip install sqlacodegen
sqlacodegen sqlite:///../db.sqlite3 > schema.py
```
