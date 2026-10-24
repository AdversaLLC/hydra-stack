#!/usr/bin/env python3
"""rag_worker: the optional vector tier for hydra-graph, run in its own interpreter.

Protocol: one JSON object on stdin, one JSON object on stdout. Never imported by
hydra_graph.py; if anything here fails, hydra-graph falls back to FTS and says so.

Requests:
  {"op":"probe",  "path":..., "backend":"auto|ollama|onnx", "model":...}
  {"op":"upsert", "path":..., "backend":..., "model":..., "project":..., "docs":[{"id","text","meta"}]}
  {"op":"query",  "path":..., "backend":..., "model":..., "project":..., "query":..., "limit":8}
  {"op":"delete", "path":..., "project":..., "ids":[...]}

Backends, tried in order under "auto":
  ollama  - local Ollama at OLLAMA_HOST (default http://127.0.0.1:11434), model default nomic-embed-text.
            No network beyond loopback.
  onnx    - Chroma's DefaultEmbeddingFunction (all-MiniLM-L6-v2). One-time model download on first use,
            then offline. Chosen only if Ollama is not reachable.
Chroma itself: PersistentClient only. Nothing listens on a port.
"""
import json
import os
import sys
import urllib.request


def ollama_ok(host: str) -> bool:
    try:
        with urllib.request.urlopen(host.rstrip("/") + "/api/tags", timeout=1.5) as r:
            return r.status == 200
    except Exception:
        return False


def make_ef(backend: str, model: str):
    import chromadb.utils.embedding_functions as ef  # type: ignore
    host = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")
    if backend in ("auto", "ollama") and ollama_ok(host):
        return ef.OllamaEmbeddingFunction(url=host.rstrip("/") + "/api/embeddings", model_name=model or "nomic-embed-text"), "ollama"
    if backend == "ollama":
        raise RuntimeError(f"ollama not reachable at {host}")
    return ef.DefaultEmbeddingFunction(), "onnx"


def main() -> int:
    raw = sys.stdin.buffer.read().decode("utf-8", "replace").strip().splitlines()
    try:
        req = json.loads(raw[-1]) if raw else {}
    except Exception:
        print(json.dumps({"error": "bad request json"}))
        return 0
    op = req.get("op")
    os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")   # local patch: chroma's anonymous usage pings are on by default; this stack is private
    try:
        import chromadb  # type: ignore
    except Exception as e:
        print(json.dumps({"error": f"chromadb not importable: {e}"}))
        return 0
    try:
        backend_want = req.get("backend", "auto")
        if op == "probe" and backend_want == "onnx" and os.environ.get("HYDRA_RAG_NO_DOWNLOAD"):
            print(json.dumps({"ok": False, "error": "onnx backend would download a model; unset HYDRA_RAG_NO_DOWNLOAD to allow"}))
            return 0
        ef, backend = make_ef(backend_want, req.get("model", ""))
        # local patch 2026-10-22: expand "~" (config stores "~/.hydra/chroma"; chromadb does not expand it, so vectors
        # were written to a literal folder named "~" under the cwd) and mirror every project vector into hg_global so a
        # project-less (cross-project) recall has the full corpus, not only nodes that have no project.
        client = chromadb.PersistentClient(path=os.path.expanduser(req.get("path") or ".chroma"), settings=chromadb.Settings(anonymized_telemetry=False))
        name = "hg_" + "".join(c if c.isalnum() else "_" for c in (req.get("project") or "global"))[:50]
        col = client.get_or_create_collection(name, embedding_function=ef, metadata={"hnsw:space": "cosine"})
        gcol = None
        if name != "hg_global":
            gcol = client.get_or_create_collection("hg_global", embedding_function=ef, metadata={"hnsw:space": "cosine"})
        if op == "probe":
            ef(["probe"])
            print(json.dumps({"ok": True, "backend": backend, "collections": len(client.list_collections())}))
        elif op == "upsert":
            docs = [d for d in req.get("docs", []) if isinstance(d, dict) and d.get("id") and d.get("text")]
            if docs:
                for target in (col, gcol):
                    if target is not None:
                        target.upsert(ids=[d["id"] for d in docs], documents=[d["text"] for d in docs],
                                      metadatas=[d.get("meta") or {"_": 1} for d in docs])
            print(json.dumps({"ok": True, "backend": backend, "upserted": len(docs)}))
        elif op == "query":
            n = max(1, min(int(req.get("limit", 8) or 8), 50))
            if col.count() == 0:
                print(json.dumps({"ok": True, "backend": backend, "hits": []}))
                return 0
            res = col.query(query_texts=[str(req.get("query", ""))], n_results=min(n, col.count()))
            ids = res.get("ids", [[]])[0]
            dists = res.get("distances", [[]])[0] if res.get("distances") else [0.0] * len(ids)
            print(json.dumps({"ok": True, "backend": backend, "hits": [{"id": i, "score": 1 - float(d)} for i, d in zip(ids, dists)]}))
        elif op == "delete":
            ids = [i for i in req.get("ids", []) if isinstance(i, str)]
            if ids:
                for target in (col, gcol):
                    if target is not None:
                        target.delete(ids=ids)
            print(json.dumps({"ok": True, "deleted": len(ids)}))
        else:
            print(json.dumps({"error": f"unknown op {op}"}))
    except Exception as e:
        print(json.dumps({"error": f"{type(e).__name__}: {e}"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
