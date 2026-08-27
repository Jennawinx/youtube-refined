import os
import sys
import threading
import time
import socket

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'youtube_refined.settings')


def find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]


def start_django(port):
    from django.core.management import call_command
    call_command('runserver', f'127.0.0.1:{port}', '--noreload', '--skip-checks')


def wait_for_server(port, timeout=10):
    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.create_connection(('127.0.0.1', port), timeout=0.5):
                return True
        except OSError:
            time.sleep(0.1)
    return False


if __name__ == '__main__':
    import django
    django.setup()

    port = find_free_port()

    thread = threading.Thread(target=start_django, args=(port,), daemon=True)
    thread.start()

    if not wait_for_server(port):
        print('Django server failed to start', file=sys.stderr)
        sys.exit(1)

    import webview
    webview.create_window(
        'YouTube Refined',
        f'http://127.0.0.1:{port}',
        width=1280,
        height=800,
        min_size=(800, 600),
    )
    webview.start()
