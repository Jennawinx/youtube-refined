### Get started

Use python3.14 or higher

```bash
# First time
python3.14 -m venv .venv            # Or whichever version you choose for venv

# Activate venv
    # MAC
    source .venv/bin/activate
    # Windows
    .\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Run for development
python manage.py runserver

# Run pywebviewer
python desktop.py
```

### modifying theming

Daisy only adds css to the output file if it's been used

```bash
# Install standalone exe
cd feed/static/css && curl -sL daisyui.com/fast | bash

# One time change
feed/static/css/tailwindcss -i feed/static/css/input.css -o feed/static/css/output.css

# Watching changes
feed/static/css/tailwindcss -i feed/static/css/input.css -o feed/static/css/output.css --watch
```

### Running as desktop app

#### MAC

**Run script as pywebview**
```
    1. under build/mac/YouTube Refined.app/Contents/MacOS/YouTube Refined
    2. update the paths
    3. copy the file to desktop
    4. update icon by right click get info
    5. drag build/mac/YouTube Refined.app/Contents/Resources/AppIcon.icns into the icon next to the file name
```

#### Windows

**Compile the exe**
```powershell
    # Create .spec file (first time) otherwise update hiddenimports= as needed
    # pyinstaller --name="youtube_refined" --noconsole desktop.py

    # Include env file
    pyinstaller --name="youtube_refined" --onefile --add-data ".env;." desktop.py

    # Build the .exe
    pyinstaller youtube_refined.spec

    # To run, double click dist/youtube_refined.exe
```