# Selected source documents and memory promotion

Hydra keeps canonical Markdown files unchanged. Set `vault_readonly_sources`
in the local Hydra config to an explicit list of Markdown paths, and optionally
`vault_source_project` (default `arch`). Normal `promote` calls import these
through `vault_import` before embedding. Files over 256 KiB and symlink paths
are rejected. No recursive vault or transcript ingestion is enabled here.

Source chunks retain paths and approximate starting lines. Explicit wikilinks
between selected files become graph links; derived file chunks are excluded
from wisdom-note export. Updates supersede active source-owned old chunks.
Reverted versions are reactivated only when the importer itself superseded
them. Operator quarantine, rejection, rollback and protected nodes remain held.

Common credential assignments (including quoted JSON/YAML keys), bearer values,
known token formats, private blocks and private keys are redacted before new
chunks are stored. This is heuristic redaction, not a guarantee of detecting
every secret. The whole redacted document is screened before chunking; all
screening reasons except document size quarantine its derived chunks. Existing
HTML comments or instruction-like text can therefore quarantine a whole source.
The importer does not approve quarantined material automatically.

Importer version 2 rescans earlier source records even if their content hash
is unchanged. It does **not** purge historical graph bodies, vector storage,
logs or backups. Treat existing stores as private; review any earlier exposure
separately, rotate exposed credentials, and plan an explicitly authorized purge
if required. Do not describe re-importing as sanitizing the entire existing store.

Promotion cursors are scoped by resolved memory database path and project.
The old aggregate checkpoint remains compatibility metadata. A wisdom-row hash
anchor detects many database replacements/restores; this is not a complete
database identity check when the replacement preserves that anchor. Source
observations are never deleted by promotion.

For explicit saves from a different working directory, Hydra-mem supplies
`HYDRA_BRIDGE_PROJECT` to its detached bridge process. The `promote` command
honors it unless `--project` is given, and scopes embedding/vault export to the
saved project. Context and root-keyed caches retain working-root scope. Planning
files from an unrelated working root are not imported by that scoped promotion.

Run the portable temporary-store tests with:

```bash
python -m unittest discover -s memory -p 'test_*.py'
```
