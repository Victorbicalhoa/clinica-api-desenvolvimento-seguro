import json
from copy import deepcopy
from pathlib import Path
from uuid import uuid4
from xml.etree import ElementTree

import pytest
from cvss import CVSS3

from scripts.security_gate import evaluate


@pytest.fixture
def gate_reports():
    """Fixtures sinteticas do gate; nao sao evidencias de scans reais."""
    directory = Path(".cache") / ("gate-" + uuid4().hex)
    directory.mkdir(parents=True)
    trace = json.loads(Path("security/threat-tests.json").read_text(encoding="utf-8"))
    root = ElementTree.Element("testsuite")
    for item in trace["mandatory_tests"]:
        ElementTree.SubElement(root, "testcase", name=item["test"])
    (directory / "pytest.xml").write_text(ElementTree.tostring(root, encoding="unicode"))
    cases = {
        "health": 200,
        "docs": 200,
        "openapi": 200,
        "consulta-list": 200,
        "consulta-detail": 200,
        "agenda-prof": 200,
        "agenda-recepcao": 200,
        "admin-denied": 403,
        "unauth-denied": 401,
        "machine-availability": 200,
        "machine-human-denied": 401,
        "human-machine-denied": 401,
    }
    documents = {
        "execution.json": {"pytest": 0, "ruff": 0, "format": 0, "bandit": 0, "pip_audit": 0},
        "bandit.json": {"errors": [], "metrics": {"_totals": {"loc": 10}}, "results": []},
        "pip-audit.json": {"dependencies": [{"name": "fastapi", "version": "test", "vulns": []}]},
        "zap.json": {
            "schema_version": 1,
            "mode": "passive-authenticated-corpus",
            "zap_version": "2.17.0",
            "records_to_scan": 0,
            "coverage": [
                {"id": key, "status": value, "expected": value} for key, value in cases.items()
            ],
            "alerts": [],
        },
    }
    for name, content in documents.items():
        (directory / name).write_text(json.dumps(content), encoding="utf-8")
    try:
        yield directory, documents
    finally:
        for name in [*documents, "pytest.xml"]:
            (directory / name).unlink(missing_ok=True)
        directory.rmdir()


def gate(directory, policy=None):
    return evaluate(
        directory, policy or {"version": 1, "zap_medium_reviews": {}}, {"fastapi": "test"}
    )


def test_gate_evidencias_completas_passam(gate_reports):
    directory, _ = gate_reports
    assert gate(directory)["passed"]


@pytest.mark.parametrize(
    "filename", ["execution.json", "bandit.json", "pip-audit.json", "zap.json", "pytest.xml"]
)
@pytest.mark.parametrize("content", [None, "", "{}"])
def test_gate_relatorio_ausente_vazio_invalido_bloqueia(gate_reports, filename, content):
    directory, _ = gate_reports
    target = directory / filename
    if content is None:
        target.unlink()
    else:
        target.write_text(content)
    assert not gate(directory)["passed"]


@pytest.mark.parametrize(
    "scenario",
    [
        "pytest",
        "scanner-error",
        "bandit-high",
        "bandit-medium",
        "sca-vulnerability",
        "sca-skipped",
        "zap-high",
        "zap-medium",
        "zap-coverage",
        "zap-queue",
    ],
)
def test_gate_bloqueia_falhas_e_achados(gate_reports, scenario):
    directory, documents = gate_reports
    data = deepcopy(documents)
    if scenario == "pytest":
        data["execution.json"]["pytest"] = 1
    elif scenario == "scanner-error":
        data["execution.json"]["bandit"] = 99
    elif scenario.startswith("bandit-"):
        data["bandit.json"]["results"] = [
            {"test_id": "TEST", "issue_severity": scenario.split("-")[1].upper()}
        ]
    elif scenario == "sca-vulnerability":
        data["pip-audit.json"]["dependencies"][0]["vulns"] = [{"id": "CVE-FICTICIA"}]
    elif scenario == "sca-skipped":
        data["pip-audit.json"]["dependencies"][0]["skip_reason"] = "test"
    elif scenario in {"zap-high", "zap-medium"}:
        data["zap.json"]["alerts"] = [
            {"pluginId": "999", "risk": scenario.split("-")[1].title(), "path": "/consultas"}
        ]
    elif scenario == "zap-coverage":
        data["zap.json"]["coverage"][3]["status"] = 401
    else:
        data["zap.json"]["records_to_scan"] = 1
    for name, content in data.items():
        (directory / name).write_text(json.dumps(content), encoding="utf-8")
    assert not gate(directory)["passed"]


@pytest.mark.parametrize("tag", ["failure", "error", "skipped", "missing"])
def test_gate_junit_falha_skip_ou_controle_ausente_bloqueia(gate_reports, tag):
    directory, _ = gate_reports
    tree = ElementTree.parse(directory / "pytest.xml")
    root = tree.getroot()
    if tag == "missing":
        root.remove(root[0])
    else:
        ElementTree.SubElement(root[0], tag)
    tree.write(directory / "pytest.xml", encoding="unicode")
    assert not gate(directory)["passed"]


@pytest.mark.parametrize(
    "impact,path,expiry,passes",
    [
        ("moderate", "/docs", "2099-01-01", True),
        ("high", "/docs", "2099-01-01", False),
        ("moderate", "/consultas", "2099-01-01", False),
        ("moderate", "/docs", "2000-01-01", False),
    ],
)
def test_gate_triagem_limitada_por_impacto_rota_e_prazo(gate_reports, impact, path, expiry, passes):
    directory, documents = gate_reports
    documents["zap.json"]["alerts"] = [{"pluginId": "10038", "risk": "Medium", "path": path}]
    (directory / "zap.json").write_text(json.dumps(documents["zap.json"]))
    policy = {
        "version": 1,
        "zap_medium_reviews": {
            "10038": {
                "business_impact": impact,
                "paths": ["/docs"],
                "expires": expiry,
                "reason": "Somente fixture sintetica",
                "owner": "teste",
            }
        },
    }
    assert gate(directory, policy)["passed"] is passes


def test_scores_cvss_recalculados_do_vetor():
    register = json.loads(Path("security/risk-register.json").read_text(encoding="utf-8"))
    for finding in register["findings"]:
        assert CVSS3(finding["vector"]).scores()[0] == finding["score"]


def test_gate_status_autenticado_nao_pode_ser_redefinido_pelo_relatorio(gate_reports):
    directory, documents = gate_reports
    entry = documents["zap.json"]["coverage"][3]
    entry["status"] = entry["expected"] = 401
    (directory / "zap.json").write_text(json.dumps(documents["zap.json"]))
    assert not gate(directory)["passed"]


def test_gate_rejeita_versao_diferente_do_inventario(gate_reports):
    directory, documents = gate_reports
    documents["pip-audit.json"]["dependencies"][0]["version"] = "old"
    (directory / "pip-audit.json").write_text(json.dumps(documents["pip-audit.json"]))
    assert not gate(directory)["passed"]


def test_runner_remove_reports_antigos_antes_de_erro_operacional(gate_reports, monkeypatch):
    import subprocess

    from scripts import run_checks

    directory, _ = gate_reports
    reports = directory / "reports"
    reports.mkdir()
    (reports / "pip-audit.json").write_text('{"dependencies": []}')
    (reports / "bandit.json").write_text('{"results": []}')
    (reports / "zap.json").write_text('{"alerts": []}')
    try:
        with monkeypatch.context() as scoped:
            scoped.chdir(directory)
            scoped.setattr(
                run_checks.subprocess,
                "run",
                lambda *a, **kw: subprocess.CompletedProcess(a, 99, b"", b"falha simulada"),
            )
            run_checks.main()
        assert not (reports / "pip-audit.json").exists()
        assert not (reports / "bandit.json").exists()
        assert not (reports / "zap.json").exists()
        assert set(json.loads((reports / "execution.json").read_text()).values()) == {99}
    finally:
        for name in [
            "execution.json",
            "ruff.txt",
            "format.txt",
            "pytest.txt",
            "bandit.txt",
            "pip_audit.txt",
        ]:
            (reports / name).unlink(missing_ok=True)
        reports.rmdir()


def test_ambiente_respeita_versoes_pinadas():
    from importlib.metadata import version

    for line in Path("requirements.txt").read_text().splitlines():
        if line and not line.startswith("#"):
            package, expected = line.split("==")
            assert version(package) == expected, package
