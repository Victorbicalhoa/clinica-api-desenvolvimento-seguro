"""Distribuicao oficial fixa e validada por SHA256, sem instalar servico."""

import hashlib
import urllib.request
import zipfile
from pathlib import Path

URL = "https://github.com/zaproxy/zaproxy/releases/download/v2.17.0/ZAP_2.17.0_Crossplatform.zip"
SHA256 = "94c8f767b1c2e94f0db66b3ae56514d5e3f5a728ee1b6c798e0c8fe2d61fbff0"


def main():
    root = Path(".cache/security-tools")
    root.mkdir(parents=True, exist_ok=True)
    archive = root / "zap.zip"
    with urllib.request.urlopen(URL, timeout=180) as response:
        data = response.read()
    if hashlib.sha256(data).hexdigest() != SHA256:
        raise RuntimeError("SHA256 ZAP divergente")
    archive.write_bytes(data)
    with zipfile.ZipFile(archive) as zipped:
        for member in zipped.namelist():
            if not (root / member).resolve().is_relative_to(root.resolve()):
                raise RuntimeError("Caminho invalido no ZIP oficial")
        zipped.extractall(root)
    print("ZAP 2.17.0 baixado e SHA256 validado.")


if __name__ == "__main__":
    main()
