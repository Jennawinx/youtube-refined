### Get started
```bash
# First time
python3.14 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run
python manage.py runserver
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