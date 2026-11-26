import os, hashlib, shutil, zipfile

def pb_sha256(path):
    """SHA-256 of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()

def pb_collect(files_by_folder, root):
    """files_by_folder: {"paper": [paths], "analysis": [...], ...}. Copies into root/<folder>/."""
    if os.path.exists(root):
        shutil.rmtree(root)
    n = 0
    for folder, paths in files_by_folder.items():
        os.makedirs(os.path.join(root, folder), exist_ok=True)
        for p in paths:
            shutil.copy2(p, os.path.join(root, folder, os.path.basename(p))); n += 1
    return n

def pb_manifest(root, name="MANIFEST.sha256"):
    """Write SHA-256 manifest of every file under root (excluding the manifest itself). Run LAST."""
    rows = []
    for dp, _, fs in os.walk(root):
        for f in sorted(fs):
            if f.startswith(name):
                continue
            fp = os.path.join(dp, f)
            rows.append((pb_sha256(fp), os.path.relpath(fp, root)))
    rows.sort(key=lambda x: x[1])
    with open(os.path.join(root, name), "w") as fh:
        for h, rel in rows:
            fh.write("%s  %s\n" % (h, rel))
    return len(rows)

def pb_zip(root, out=None):
    """Zip root; returns (zip_path, sha256)."""
    out = out or (root.rstrip("/") + ".zip")
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for dp, _, fs in os.walk(root):
            for f in fs:
                fp = os.path.join(dp, f)
                z.write(fp, os.path.relpath(fp, os.path.dirname(root)))
    return out, pb_sha256(out)

def pb_signing_md(root_name):
    """SIGNING.md text: manifest-last, GPG detach-sign, RFC-3161 from two TSAs, zip, deposit."""
    return """# Signing, timestamping and deposit

1. Regenerate the manifest LAST (after any edit):
   cd %s && find . -type f ! -name 'MANIFEST.sha256*' -print0 | sort -z | xargs -0 sha256sum > MANIFEST.sha256
   sha256sum -c MANIFEST.sha256
2. Sign the manifest (not each file):
   gpg --armor --detach-sign MANIFEST.sha256 && gpg --verify MANIFEST.sha256.asc MANIFEST.sha256
   Include your public key: gpg --armor --export KEYID > pubkey.asc
3. Trusted timestamp (cannot be backdated) — use two free TSAs:
   openssl ts -query -data MANIFEST.sha256 -sha256 -cert -out MANIFEST.sha256.tsq
   curl -s -H 'Content-Type: application/timestamp-query' --data-binary @MANIFEST.sha256.tsq https://freetsa.org/tsr > MANIFEST.sha256.tsr
   (repeat against https://zeitstempel.dfn.de)
4. Zip and record the zip hash somewhere outside the archive.
5. Deposit: Zenodo (DOI, free) first; arXiv when endorsed; public git repo with signed commits.
""" % root_name
