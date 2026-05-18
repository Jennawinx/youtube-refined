### Get started
```bash
source .venv/bin/activate
python manage.py runserver
```

### modifying theming

```bash
# Install standalone exe
cd feed/static/css && curl -sL daisyui.com/fast | bash

# One time change
feed/static/css/tailwindcss -i feed/static/css/input.css -o feed/static/css/output.css

# Watching changes
feed/static/css/tailwindcss -i feed/static/css/input.css -o feed/static/css/output.css --watch
```