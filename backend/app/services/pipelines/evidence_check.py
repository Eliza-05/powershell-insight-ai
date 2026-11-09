"""Deterministic evidence check AFTER the LLM (taxonomy 0.2 operations, no semantics claimed).

For every behavior the model claimed and the literal validator admitted, the cited spans are
expanded to whole lines of their source, comments are blanked and string contents removed (text
that is only shown or stored does not count), and Base64 behind -EncodedCommand/FromBase64String
is decoded. The behavior is kept only if that region contains an operation the taxonomy
definition requires. If it fails but the region matches exactly one other behavior that is not
already kept, it is relabelled (e.g. a POST cited as B01 becomes B06); otherwise it is dropped.
It never adds a behavior the model did not claim, so it fixes false positives and wrong IDs,
never omissions. The model's risk label is never changed (attribution stays with the model).

Rules frozen from the lab prototype (runners/evidence_check.py, R7 exploratory analysis); they
were written after seeing those answers and still need an independent evaluation.
"""
from __future__ import annotations

import base64
import re

from app.schemas.llm_analysis import BehaviorId
from app.schemas.pipeline import ModelReport
from app.services.pipelines.sanitize import blank_comments

VERSION = "evidence-check-v1"
BEHAVIOR_IDS = ("B01", "B02", "B03", "B04", "B05", "B06", "B07")

I = re.IGNORECASE
DOWNLOAD = re.compile(r"\b(Invoke-WebRequest|Invoke-RestMethod|iwr|irm|curl|wget|Start-BitsTransfer)\b|"
                      r"\.Download(File|String|Data)\b|\.Get(String)?Async\b", I)
SENDING = re.compile(r"-Method\s+(Post|Put|Patch)\b|-Body\b|\.Upload(String|File|Data)\b", I)
OUTFILE = re.compile(r"-OutFile\b", I)
CMD = {
    "B02": re.compile(r"\b(Invoke-Expression|iex|Add-Type|Invoke-Command)\b|\[scriptblock\]::Create|"
                      r"\.InvokeScript\b|NewScriptBlock|Assembly\]::Load|\.Invoke\(\)|(^|[\s;(|])[&.]\s*\$", I),
    "B04": re.compile(r"\b(Set-MpPreference|Add-MpPreference|Set-NetFirewallProfile|auditpol|Clear-EventLog|"
                      r"Remove-EventLog|Disable-NetFirewallRule)\b|netsh\s+advfirewall|wevtutil\s+cl|AmsiUtils", I),
    "B05": re.compile(r"\b(Get-NetIPConfiguration|Get-NetAdapter|Get-NetIPAddress|ipconfig|Get-LocalUser|"
                      r"Get-LocalGroup(Member)?|whoami|systeminfo|hostname|Get-ComputerInfo|Get-CimInstance|"
                      r"Get-WmiObject|gwmi|Get-Process|Get-Service|Get-HotFix|Get-MpComputerStatus|Get-ItemProperty|"
                      r"Get-PSDrive|Get-Volume|Get-NetTCPConnection)\b|\$env:(COMPUTERNAME|USERNAME|USERDOMAIN)\b", I),
    "B06": re.compile(r"\b(Test-NetConnection|Test-Connection|Send-MailMessage|New-PSSession|Enter-PSSession|"
                      r"Resolve-DnsName)\b|Net\.Sockets|TcpClient|UdpClient|\.Upload(String|File|Data)\b", I),
}
REGISTRY_ENUM = re.compile(r"\bGet-ChildItem\b[^\n]*\bHK(LM|CU)\b", I)  # needs raw text (path is a string)
B03_WRITE = re.compile(r"\b(Set-ItemProperty|New-ItemProperty|Set-Content|Add-Content|Out-File|Copy-Item|New-Item)\b|"
                       r"\breg(\.exe)?\s+add\b", I)
B03_PLACE = re.compile(r"\\Run(Once)?\b|\\Startup\\|\\Winlogon\b", I)
B03_DIRECT = re.compile(r"\b(Register-ScheduledTask|New-Service|Register-WmiEvent)\b|schtasks(\.exe)?\s+/create|"
                        r"__EventFilter|\bsc(\.exe)?\s+create\b", I)
B07_API = re.compile(r"RetrievePassword|PasswordVault|GetNetworkCredential|ConvertFrom-SecureString|\bcmdkey\b|"
                     r"\bvaultcmd\b|Get-StoredCredential|\blsass\b|\\SAM\b", I)
B07_READ = re.compile(r"\b(Get-Content|Import-Clixml|Copy-Item|Import-Csv)\b|\breg(\.exe)?\s+save\b", I)
B07_PLACE = re.compile(r"credential|password|vault", I)
STRINGS = re.compile(r"'(?:[^']|'')*'|\"(?:[^\"`]|`.)*\"")


def decoded_payloads(text):
    out = []
    for m in re.finditer(r"-(?:EncodedCommand|enc|e|ec)\s+([A-Za-z0-9+/=]{16,})", text, I):
        try:
            out.append(base64.b64decode(m.group(1)).decode("utf-16-le"))
        except Exception:
            pass
    for m in re.finditer(r"FromBase64String\(\s*'([A-Za-z0-9+/=]{8,})'", text, I):
        try:
            out.append(base64.b64decode(m.group(1)).decode("utf-8"))
        except Exception:
            pass
    return out


def matches(raw):
    """Behaviors whose required operation appears in this code region (comments already blanked)."""
    texts = [raw] + decoded_payloads(raw)
    found = set()
    for t in texts:
        code = STRINGS.sub("''", t)
        for line_raw, line_code in zip(t.splitlines() or [t], code.splitlines() or [code]):
            if DOWNLOAD.search(line_code):
                found.add("B06" if SENDING.search(line_code) and not OUTFILE.search(line_code) else "B01")
        for b, rx in CMD.items():
            if rx.search(code):
                found.add(b)
        if REGISTRY_ENUM.search(t):
            found.add("B05")
        if (B03_WRITE.search(code) and B03_PLACE.search(t)) or B03_DIRECT.search(code):
            found.add("B03")
        cred_text = re.sub(r"Get-Credential", "", t, flags=I)
        if B07_API.search(code) or (B07_READ.search(code) and B07_PLACE.search(cred_text)):
            found.add("B07")
    return found


def line_region(text, start, end):
    a = text.rfind("\n", 0, start) + 1
    b = text.find("\n", end)
    return text[a:] if b == -1 else text[a:b]


def _id(value) -> str:
    return getattr(value, "value", value)


def verify(report: ModelReport, evidence, sources: dict[str, str]):
    """Return (checked_report, changes). `evidence` must be the validated evidence of `report`."""
    blanked = {k: blank_comments(v)[0] for k, v in sources.items()}
    regions: dict[str, list[str]] = {}
    for e in evidence:
        src = blanked.get(e.source_id)
        if src is not None:
            regions.setdefault(_id(e.behavior_id), []).append(line_region(src, e.start, e.end))
    findings = {_id(f.behavior_id): f for f in report.behaviors}
    kept, failing = [], {}
    for b in findings:
        m = matches("\n".join(regions.get(b, [])))
        if b in m:
            kept.append(b)
        else:
            failing[b] = m
    changes, behaviors = [], [findings[b] for b in kept]
    taken = set(kept)
    for b, m in failing.items():
        others = sorted(set(m) - taken - {b})
        if len(others) == 1:
            target = others[0]
            taken.add(target)
            f = findings[b]
            note = f"[Verificador determinista: reetiquetado de {b} a {target}; la cita contiene esa operación.] "
            behaviors.append(f.model_copy(update={"behavior_id": BehaviorId(target),
                                                  "explanation": (note + f.explanation)[:2000]}))
            changes.append({"from": b, "to": target, "action": "relabelled"})
        else:
            changes.append({"from": b, "to": None, "action": "dropped"})
    behaviors.sort(key=lambda f: BEHAVIOR_IDS.index(_id(f.behavior_id)))
    if not changes:
        return report, []
    data = report.model_dump(mode="json")
    data["behaviors"] = [f.model_dump(mode="json") for f in behaviors]
    return ModelReport.model_validate(data), changes
