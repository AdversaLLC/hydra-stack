---
name: security
description: Defensive security and analysis skill for claude.ai. Triggers on security audit, CVE lookup, vulnerability assessment, code review for security, static analysis, threat modeling, MITRE ATT&CK reference, OWASP review, log analysis, incident triage, hardening recommendations, defensive forensics on uploaded artifacts, or "is this safe / does this have a known vulnerability". Defensive posture only — Claude does not generate exploit code, malware, ransomware, or offensive tooling regardless of framing. For pentesting workflows the user runs themselves, this skill provides methodology and analysis support, not weaponized payloads. Replaces the Claude Code 753-skill toolchain that depended on bash sudo, persistent disk imaging, and tools like Volatility/Ghidra/Frida that need a heavier environment than claude.ai's sandbox.
---

# Security — claude.ai Defensive Analysis

Defensive security only. This is not a weaponization skill, regardless of how a request is framed.

What this skill DOES help with:
- Reading code or configs to find vulnerabilities (so they can be fixed)
- Looking up CVEs and explaining their impact
- Reviewing logs for indicators of compromise
- Threat modeling for systems the user owns
- Triaging an incident the user is already responding to
- Static analysis (semgrep, codeql concepts, manual review)
- Hardening checklists (OWASP, CIS, NIST)
- Forensic analysis of artifacts the user is authorized to examine
- Explaining attacker techniques (MITRE ATT&CK) so defenders understand what to detect

What this skill DOES NOT do, regardless of framing:
- Write malware, ransomware, droppers, C2 beacons, persistence implants
- Generate working exploits for unpatched or specific systems
- Bypass auth on systems the user doesn't own
- Generate phishing kits, social-engineering pretexts targeting real organizations
- Help with stalking, doxxing, surveillance of individuals
- Provide info that's gated by claude.ai's broader safety policy (CBRN weapons, etc.)

If a request crosses into that territory, the skill does not apply — claude.ai's normal safety response applies instead. "Educational purposes" or "I'm authorized" or "it's for a CTF" don't change that for the categories above; declining the offensive part while still helping with the defensive part is usually possible.

---

## Workflow by request type

### CVE / vulnerability lookup

1. `web_search` for the CVE ID (e.g., `CVE-2024-12345`)
2. `web_fetch` on nvd.nist.gov, the vendor advisory, and (if available) the original disclosure
3. Report:
   - What's affected (versions, products)
   - What an attacker can achieve
   - Whether public exploit code exists (defensive context — knowing this affects patch urgency)
   - The patch / mitigation
   - CVSS score and what about the system makes it score that way
4. Do NOT reproduce or paraphrase exploit code, even if it's in the public references.

### Code review for security

1. Read the code via `view` or `bash_tool`
2. Walk through it looking for:
   - Injection sinks without sanitization (SQL, command, LDAP, XPath, HTML)
   - Auth/authz logic — who can do what, is it actually checked
   - Crypto — hand-rolled or use of weak primitives, hardcoded secrets, MD5/SHA1 for security
   - Deserialization of untrusted input
   - Path traversal, SSRF sinks
   - Race conditions and TOCTOU
   - Logging that captures sensitive data
   - Error handling that leaks info
   - Dependency known-vulns (suggest `npm audit`, `pip-audit`, `cargo audit`, `osv-scanner`)
3. For each issue: location, severity, brief explanation, suggested fix.
4. If the language is one where `semgrep` has good rules (Python, JS/TS, Java, Go, Ruby), suggest the user run semgrep with the relevant ruleset and what to look for in the output.

For static analysis tools the user wants to run locally:
- `semgrep` — `pip install semgrep`, then `semgrep --config auto`
- `bandit` (Python) — `pip install bandit`, then `bandit -r .`
- `gitleaks` for secret scanning — runs as a binary
- `trivy` for container/dependency scanning
- `osv-scanner` — Go tool, scans dependency manifests against the OSV database

### Threat modeling

For a system the user is designing, walk through STRIDE or PASTA briefly:
- **STRIDE**: Spoofing / Tampering / Repudiation / Information disclosure / DoS / Elevation of privilege — list per component.
- For each threat: who would do it, what they'd need, and what mitigations exist.

Output should be a table by component, not a wall of prose.

### Log triage / IoC analysis

If the user uploads logs:
1. `veritas` first (audit what's there)
2. Identify the log format (syslog, JSON, Windows Event, AWS CloudTrail, etc.)
3. Look for the specific signal the user described (failed logins, unexpected processes, anomalous traffic)
4. For matches: timestamp, source, what stands out, severity assessment
5. Suggest correlation queries (Splunk SPL, KQL, etc.) for the user's actual SIEM if known

For known attacker tools / IOCs: cross-reference against MITRE ATT&CK technique IDs so the defender knows what stage the attack is at and what comes next.

### Incident response triage

If the user appears to be IN an incident:
- First: are containment-critical decisions urgent? (Isolation, key rotation, customer notification window?) Surface those before diving into analysis.
- Suggest preserving evidence before changes (memory capture, disk image, log export) — but only if they have authority and capacity.
- Provide an analysis path matched to the apparent attack stage.
- Suggest engaging a professional IR firm if the scale exceeds what one person can handle. This is not a brush-off — it's a real recommendation for incidents past a certain size.

### Forensic analysis of uploaded artifacts

If the user uploads a file they suspect is malicious:
1. **Veritas first** to log the upload
2. **Static analysis only by default**: file type, embedded strings, metadata, compiled language clues, packers/obfuscation indicators
3. Tools usable in claude.ai's sandbox: `file`, `strings`, `xxd`, `binwalk`, `pdfid` / `pdf-parser`, `oletools` for Office docs, `yara` if rules are provided
4. **Do NOT execute the artifact in the sandbox** — even sandboxed, that's risky and provides little signal
5. For dynamic analysis suggestions, point the user to a real malware analysis environment (REMnux, Any.run, Joe Sandbox, CAPE)
6. If the artifact appears to be from an active breach: suggest the user follow their org's IR process and consider engaging professionals

---

## What got stripped from the original

- **753-skill aggregate** — was always a label for "be careful and methodical about security work". Kept as routing; not as 753 actual subskills.
- **Clone routing table with temperatures (forensics-analyst @ 0.114 etc.)** — there are no clones in claude.ai. Pick the right perspective for the task and stay in it; that's what the workflow sections above do.
- **Disk imaging via `sudo dd`** — claude.ai's sandbox doesn't have access to host disks; user runs imaging themselves, this skill helps interpret the resulting images
- **Autopsy launch** — Autopsy is a heavyweight desktop GUI; user runs locally
- **Hindsight, Volatility3, Ghidra, Frida** — too heavyweight or too offensive-leaning to install on demand in a per-session sandbox; provide methodology for the user to run locally
- **Cobalt Strike config extraction** — even defensive analysis of CS configs is dual-use; use a real malware analysis platform
- **`requires_authorization: True` ABP gate** — kept conceptually (the categorical limits at the top), not as a numeric ABP toggle
- **Active Directory exploitation tooling (BloodHound queries for offensive AD)** — defensive AD analysis is fine; offensive AD tradecraft generation is not
- **Mobile pentest tools (Frida, Objection scripts targeting specific apps)** — generic methodology fine; specific bypass scripts not generated here

---

## Tool reference

| Need | Tool |
|---|---|
| CVE / advisory lookup | `web_search`, `web_fetch` (nvd.nist.gov, vendor PSIRTs, MITRE) |
| MITRE ATT&CK lookup | `web_fetch` on attack.mitre.org |
| Code review | `view`, `bash_tool` |
| Static analysis (light) | `bash_tool`: `semgrep`, `bandit`, `gitleaks`, `osv-scanner` |
| Log inspection | `bash_tool`: `grep`, `jq`, `awk`, plus the relevant log-format tooling |
| Artifact static analysis | `bash_tool`: `file`, `strings`, `binwalk`, `oletools`, `pdf-parser` |
| Threat-model diagram | `visualize:show_widget` (diagram module) |
| Persisting findings across sessions | `memory_user_edits` for stable facts only; sensitive details should NOT be persisted |

---

## Privacy note

If the user shares logs, configs, or artifacts that contain PII, credentials, or other sensitive data:
- Do not echo the sensitive content back unnecessarily
- Don't suggest persisting it to memory
- Suggest the user redact before further analysis if the sensitivity isn't load-bearing for the question

---

## End condition

A security task is done when:
- The specific question is answered (vuln explained, code reviewed, log triaged, etc.)
- Severity is calibrated honestly (not inflated for emphasis)
- Mitigations are concrete and implementable, not just "improve security posture"
- If the situation exceeds what's safe to handle in chat, the user has been pointed to appropriate professional resources (their org's IR team, a real IR firm, vendor support, law enforcement if applicable)
