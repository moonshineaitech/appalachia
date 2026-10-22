"""Bootstrap and verify Python trust after the October 2026 eMudhra incident.

Run --bootstrap before installing dependencies, then run without arguments at
startup. Downloads are hash-verified before pip gets to execute any wheel.
"""
import hashlib
import importlib.metadata
import json
from pathlib import Path
import re
import shutil
import ssl
import subprocess
import sys
import tempfile
import urllib.request

WHEELS = {
    "pip": (
        "26.2.2",
        "https://files.pythonhosted.org/packages/3f/06/3e4420302363fbb71be3c7f35ce042f54bfca330e3e66b3a2e3c4cca579f/pip-26.2.2-py3-none-any.whl",
        "fd7f4dfa8190e014013b9f08f3e973f4e4c26ffd179a204895533a7254813a70",
    ),
    "certifi": (
        "2026.10.19",
        "https://files.pythonhosted.org/packages/c4/51/29046e48f693c54e5b7412216d447a1d8362c9653148d98c02cdf65fa733/certifi-2026.10.19-py3-none-any.whl",
        "42d35340cc5b9ba78e818ddbff0c5b1c2b779de448a340fd1b989f5fa8670e1b",
    ),
}


def bootstrap():
    with tempfile.TemporaryDirectory() as temporary:
        wheels = {}
        for name, (_, url, digest) in WHEELS.items():
            wheel = Path(temporary) / url.rsplit("/", 1)[1]
            with urllib.request.urlopen(url, timeout=60) as response:
                data = response.read()
            if hashlib.sha256(data).hexdigest() != digest:
                raise RuntimeError(f"Untrusted {name} wheel: SHA256 mismatch")
            wheel.write_bytes(data)
            wheels[name] = wheel
        subprocess.run(
            [sys.executable, "-I", "-c",
             "import runpy,sys;sys.path.insert(0,sys.argv.pop(1));"
             "sys.argv[0]='-m';runpy.run_module('pip',run_name='__main__')",
             str(wheels["pip"]), "--isolated", "--disable-pip-version-check",
             "install", "--no-index", "--no-deps", "--upgrade",
             str(wheels["pip"]), str(wheels["certifi"])],
            check=True,
        )
        # Updating installed pip alone leaves new virtualenvs seeded with old pip.
        import ensurepip
        module = Path(ensurepip.__file__)
        source = module.read_text(encoding="utf-8")
        if not re.search(r"_PIP_VERSION\s*=", source):
            raise RuntimeError("Unsupported ensurepip layout; cannot secure venv seeds")
        bundled = module.parent / "_bundled"
        bundled.mkdir(exist_ok=True)
        shutil.copy2(wheels["pip"], bundled / wheels["pip"].name)
        module.write_text(re.sub(r'(_PIP_VERSION\s*=\s*)[\"\'][^\"\']+[\"\']',
                                 r'\g<1>"26.2.2"', source), encoding="utf-8")
        for old in bundled.glob("pip-*.whl"):
            if old.name != wheels["pip"].name:
                old.unlink()


def verify():
    import certifi
    from pip._vendor import certifi as pip_certifi
    from pip._vendor.packaging.version import Version
    actual = {name: importlib.metadata.version(name) for name in WHEELS}
    for name, (minimum, _, _) in WHEELS.items():
        if Version(actual[name]) < Version(minimum):
            raise RuntimeError(f"Unsafe Python trust: upgrade {name} to {minimum}")
    if Version(pip_certifi.__version__) < Version("2026.10.19"):
        raise RuntimeError("pip still bundles a compromised certificate store")
    seed = subprocess.check_output(
        [sys.executable, "-I", "-m", "ensurepip", "--version"], text=True
    ).strip()
    if Version(seed.removeprefix("pip ")) < Version("26.2.2"):
        raise RuntimeError("ensurepip would seed a vulnerable pip")
    blocked = {"emSign ECC Root CA - G3", "AAA Certificate Services"}
    bundles = {"system": None, "certifi": certifi.where(),
               "pip-certifi": pip_certifi.where()}
    for name, bundle in bundles.items():
        context = ssl.create_default_context(cafile=bundle)
        subjects = {value for cert in context.get_ca_certs()
                    for item in cert["subject"] for key, value in item
                    if key == "commonName"}
        if blocked & subjects:
            raise RuntimeError(f"Compromised root remains in {name} trust")
    receipt = {"python": sys.version.split()[0], **actual,
               "pipVendoredCertifi": pip_certifi.__version__,
               "ensurepip": seed, "affectedRootsPresent": False}
    print("Verified patched Python trust " + json.dumps(receipt, sort_keys=True), flush=True)
    return receipt


if __name__ == "__main__":
    if "--bootstrap" in sys.argv:
        bootstrap()
    verify()
