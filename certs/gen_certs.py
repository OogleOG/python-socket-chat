#!/usr/bin/env python3
"""Generate self-signed TLS certificates for development."""

import subprocess
import sys
import os


def generate():
    cert_dir = os.path.dirname(os.path.abspath(__file__))
    cert_file = os.path.join(cert_dir, "server.crt")
    key_file = os.path.join(cert_dir, "server.key")

    if os.path.exists(cert_file) and os.path.exists(key_file):
        print("Certificates already exist. Delete them to regenerate.")
        return

    try:
        subprocess.run([
            "openssl", "req", "-x509", "-newkey", "rsa:4096",
            "-keyout", key_file,
            "-out", cert_file,
            "-days", "365",
            "-nodes",
            "-subj", "/CN=localhost",
        ], check=True)
        print(f"Generated:\n  {cert_file}\n  {key_file}")
    except FileNotFoundError:
        print("Error: openssl not found. Install OpenSSL or generate certs manually.")
        print("On Windows, you can install OpenSSL via: winget install ShiningLight.OpenSSL")
        sys.exit(1)


if __name__ == "__main__":
    generate()
