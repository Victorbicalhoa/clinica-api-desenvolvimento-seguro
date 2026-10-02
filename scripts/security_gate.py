"""Gate fail-closed; severidade de scanner nao e CVSS."""

import argparse
import json
from datetime import date
from pathlib import Path
from xml.etree import ElementTree


def evaluate(directory: Path, policy: dict, required_packages: dict[str, str]) -> dict:
    blocked, warnings = [], []

    def read(name):
        return json.loads((directory / name).read_text(encoding="utf-8"))

    try:
        status = read("execution.json")
        for name in ("pytest", "ruff", "format"):
            if type(status[name]) is not int or status[name] != 0:
                blocked.append(f"{name}: controle obrigatorio falhou")
        for name in ("bandit", "pip_audit"):
            if type(status[name]) is not int or status[name] not in (0, 1):
                blocked.append(f"{name}: erro operacional")
        suites = ElementTree.parse(directory / "pytest.xml").getroot()
        cases = list(suites.iter("testcase"))
        if not cases or any(
            list(case)
            for case in cases
            if any(case.find(tag) is not None for tag in ("failure", "error", "skipped"))
        ):
            blocked.append("pytest: vazio, falha, erro ou teste ignorado")
        trace = json.loads(Path("security/threat-tests.json").read_text(encoding="utf-8"))
        for item in trace["mandatory_tests"]:
            if not any(case.attrib.get("name", "").split("[")[0] == item["test"] for case in cases):
                blocked.append(f"pytest: regressao obrigatoria ausente {item['test']}")
        bandit = read("bandit.json")
        if bandit["errors"] or bandit["metrics"]["_totals"]["loc"] <= 0:
            blocked.append("Bandit: analise incompleta")
        if not isinstance(bandit["results"], list):
            raise ValueError("results Bandit invalidos")
        for finding in bandit["results"]:
            level = finding["issue_severity"]
            if level not in {"LOW", "MEDIUM", "HIGH"}:
                raise ValueError("severidade Bandit desconhecida")
            target = blocked if level in {"MEDIUM", "HIGH"} else warnings
            target.append(f"Bandit {finding['test_id']}: {level}")
        if status["bandit"] == 1 and not bandit["results"]:
            blocked.append("Bandit: exit 1 sem findings")
        audit = read("pip-audit.json")
        dependencies = audit["dependencies"]
        if not isinstance(dependencies, list) or not dependencies:
            raise ValueError("inventario SCA vazio")
        seen = {}
        for dependency in dependencies:
            seen[dependency["name"].lower().replace("_", "-")] = dependency["version"]
            if "skip_reason" in dependency or not isinstance(dependency["vulns"], list):
                raise ValueError("dependencia nao auditada")
            for finding in dependency["vulns"]:
                blocked.append(
                    f"SCA {dependency['name']} {finding['id']}: corrigir/triagem necessaria"
                )
        if any(seen.get(name) != version for name, version in required_packages.items()):
            blocked.append("SCA: inventario/versoes nao correspondem a requirements.txt")
        if status["pip_audit"] == 1 and not any(x["vulns"] for x in dependencies):
            blocked.append("SCA: exit 1 sem findings")
        zap = read("zap.json")
        if zap["schema_version"] != 1 or zap["mode"] != "passive-authenticated-corpus":
            raise ValueError("schema ZAP invalido")
        if zap["records_to_scan"] != 0 or not zap["zap_version"]:
            blocked.append("ZAP: scan incompleto")
        expected = {
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
        coverage = zap["coverage"]
        if (
            {item["id"] for item in coverage} != set(expected)
            or len(coverage) != len(expected)
            or any(
                item["status"] != expected[item["id"]] or item["expected"] != expected[item["id"]]
                for item in coverage
            )
        ):
            blocked.append("ZAP: corpus autenticado incompleto")
        if not isinstance(zap["alerts"], list):
            raise ValueError("alerts ZAP invalidos")
        if policy["version"] != 1:
            raise ValueError("politica desconhecida")
        for alert in zap["alerts"]:
            risk = alert["risk"]
            if risk not in {"Informational", "Low", "Medium", "High"}:
                raise ValueError("risco ZAP desconhecido")
            if risk == "High":
                blocked.append(f"ZAP {alert['pluginId']}: High")
            elif risk == "Medium":
                review = policy["zap_medium_reviews"].get(alert["pluginId"])
                if (
                    not review
                    or review["business_impact"] != "moderate"
                    or alert["path"] not in review["paths"]
                    or date.fromisoformat(review["expires"]) < date.today()
                    or not review["reason"]
                    or not review["owner"]
                ):
                    blocked.append(f"ZAP {alert['pluginId']}: Medium sem triagem valida")
                else:
                    warnings.append(f"ZAP {alert['pluginId']}: Medium, impacto moderado revisado")
            else:
                warnings.append(f"ZAP {alert['pluginId']}: {risk}")
    except (
        OSError,
        ValueError,
        KeyError,
        TypeError,
        AttributeError,
        ElementTree.ParseError,
    ) as exc:
        blocked.append(f"Evidencia ausente/invalida: {type(exc).__name__}")
    return {"passed": not blocked, "blocked": blocked, "warnings": warnings}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--reports", type=Path, default=Path("reports"))
    args = parser.parse_args()
    try:
        policy = json.loads(Path("security/policy.json").read_text(encoding="utf-8"))
        packages = {
            line.split("==")[0].lower().replace("_", "-"): line.split("==")[1]
            for line in Path("requirements.txt").read_text().splitlines()
            if line and not line.startswith("#")
        }
        result = evaluate(args.reports, policy, packages)
    except (OSError, ValueError, IndexError):
        result = {
            "passed": False,
            "blocked": ["Politica/inventario ausente ou invalido"],
            "warnings": [],
        }
    args.reports.mkdir(exist_ok=True)
    (args.reports / "gate.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
