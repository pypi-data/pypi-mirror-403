import sys
from websuper.config import load_token, save_token
from websuper.tunnel import start_tunnel

def main():
    if len(sys.argv) < 2:
        print("Usage: websuper <command>")
        return

    cmd = sys.argv[1]

    if cmd == "config" and sys.argv[2] == "add-authtoken":
        save_token(sys.argv[3])
        print("✓ Auth token saved")
        return

    if cmd == "http":
        port = sys.argv[2]
        token = load_token()
        start_tunnel(port, token)
        return

    print("Unknown command")
