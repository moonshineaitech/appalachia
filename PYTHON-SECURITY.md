The October 2026 Python certificate advisory requires pip 26.2.2 and certifi
2026.10.19 or newer. Update uv to 0.13.4 or newer if used. Updating the operating
system certificate package alone does not update pip's vendored certificate store.

Before installing dependencies, update the Linux system CA package (Debian 12:
ca-certificates 20250419~deb12u2 or newer), then run
`python scripts/python-security.py --bootstrap` with the deployment interpreter.
This downloads hash-verified wheels, updates pip and certifi, and updates the
ensurepip seed used by new virtual environments. Run the same script without
`--bootstrap` to verify trust before startup. requirements.txt is hash-pinned.

The recovered 2024 application is missing its home page template. Its old managed
Vercel Python deployment remains paused, with authentication required for every
deployment. These source fixes do not patch that stored deployment. Do not resume
it before restoring its missing source and rebuilding in a verified environment.

Advisory: https://discuss.python.org/t/information-for-python-users-regarding-emudhra-emsign-ca-certificate-security-incident/109576
