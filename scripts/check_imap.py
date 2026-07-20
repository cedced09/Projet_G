from __future__ import annotations

import imaplib
import socket
import ssl

from app.settings import Settings


def main() -> None:
    settings = Settings()
    host = settings.email_imap_host
    port = settings.email_imap_port
    username = settings.email_imap_username
    password = settings.email_imap_password

    if not host or not username or not password:
        print("Configuration incomplete: EMAIL_IMAP_HOST, USERNAME et PASSWORD sont requis.")
        raise SystemExit(1)

    print(f"Host: {host}")
    print(f"Port: {port}")
    print(f"Username: {username}")
    print("Password: present, non affiche")

    try:
        addresses = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        print(f"DNS: ECHEC - {exc}")
        raise SystemExit(1) from exc
    print(f"DNS: OK - {len(addresses)} adresse(s) trouvee(s)")

    try:
        with (
            socket.create_connection((host, port), timeout=10) as raw_socket,
            ssl.create_default_context().wrap_socket(
                raw_socket,
                server_hostname=host,
            ),
        ):
            print("TLS socket: OK")
    except OSError as exc:
        print(f"TLS socket: ECHEC - {exc}")
        raise SystemExit(1) from exc

    try:
        with imaplib.IMAP4_SSL(host, port, timeout=10) as client:
            print("IMAP SSL: OK")
            client.login(username, password)
            print("LOGIN: OK")
            status, folders = client.list()
            print(f"LIST folders: {status}")
            if status == "OK" and folders:
                print("Quelques dossiers:")
                for folder in folders[:5]:
                    print(f"  {folder.decode(errors='replace')}")
            client.logout()
    except imaplib.IMAP4.error as exc:
        print(f"LOGIN/IMAP: ECHEC - {exc}")
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
