"""Index Pango PDS, Logos-2 documentation, academic papers, and engineering project corpora.

Usage: python build_index.py [--reset] [--force] [--collection <name>]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
from pathlib import Path

from rag_common import (
    COLLECTION_NAME, DATABASE, DOCUMENTS, get_collection, get_model,
    segment_text,
)

ENTITY_RE = re.compile(
    r'\b(?:Place-\d+|Route-\d+|Flow-\d+|Map-\d+|DRC-\d+|'
    r'PAP_[A-Z0-9_]+|syn_[a-z0-9_]+|'
    r'GTP_[A-Z0-9_]+|CLMA|CLMS|DRM36K?|APM(?:_E2)?|GPLL|PPLL|USCM|HMIC_[HS]|'
    r'create_clock|create_generated_clock|set_clock_groups|set_false_path|'
    r'set_multicycle_path|set_input_delay|set_output_delay|define_attribute|'
    r'pds_shell|dev_map|report_timing|gen_bit_stream|'
    r'FlightLLM|AutoBridge|RapidStream|SpeedLLM|LATCH|SSR|Systolic|'
    r'Floorplanning|Pblock|Anchor_Registers|DSP_Cascade|PingPong_Buffer|Tinyriscv)\b',
    re.IGNORECASE
)

def extract_entities(text: str) -> list[str]:
    raw = ENTITY_RE.findall(text)
    seen = set()
    res = []
    for x in raw:
        norm = x.upper() if x.startswith(('pap_', 'gtp_')) else x
        if norm.lower() not in seen:
            seen.add(norm.lower())
            res.append(norm)
    return res[:25]

def main() -> int:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description='Build PDS Logos-2 & LLM Papers RAG index.')
    parser.add_argument('--reset', action='store_true', help='Delete existing index.')
    parser.add_argument('--force', action='store_true', help='Re-index unchanged files.')
    parser.add_argument('--collection', default=COLLECTION_NAME, help='Collection name (default: pds_logos2_pnr_sta_kb).')
    args = parser.parse_args()

    coll_name = args.collection
    client, collection = get_collection(coll_name)
    manifest_path = DATABASE / f'manifest_{coll_name}.json'
    if manifest_path.exists() and not args.reset:
        try:
            manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
        except Exception:
            manifest = {}
    else:
        manifest = {}

    if args.reset:
        print(f"Resetting collection '{coll_name}'...", flush=True)
        try:
            client.delete_collection(coll_name)
        except Exception:
            pass
        _, collection = get_collection(coll_name)

    model = None

    # 1. Index practical & academic project corpora (.jsonl)
    corpus_files = sorted(DOCUMENTS.rglob('*.jsonl'))
    for cfile in corpus_files:
        source_name = cfile.relative_to(DOCUMENTS).as_posix()
        sha = hashlib.sha256(cfile.read_bytes()).hexdigest()
        if not args.force and manifest.get(source_name, {}).get('sha256') == sha:
            print(f"SKIP unchanged corpus: {source_name}", flush=True)
            continue
        print(f"Indexing corpus: {source_name}...", flush=True)
        records = []
        with open(cfile, 'r', encoding='utf-8') as f:
            for line_no, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue
                item = json.loads(line)
                rec_id = hashlib.sha256(f"{source_name}|{line_no}|{item['id']}".encode('utf-8')).hexdigest()
                tags_str = " ".join(item.get('tags', []))
                text = (
                    f"【{item.get('title', '')}】\n"
                    f"ID: {item.get('id', '')}\n"
                    f"类别: {item.get('category', '')}\n"
                    f"标签: {tags_str}\n"
                    f"核心关注: {item.get('extract_focus', '')}\n"
                    f"{item.get('text', '')}"
                )
                entities = extract_entities(text)
                meta = {
                    'source': source_name,
                    'title': item.get('title', ''),
                    'item_id': item.get('id', ''),
                    'category': item.get('category', ''),
                    'tags': tags_str,
                    'extract_focus': item.get('extract_focus', ''),
                    'page': 1,
                    'error_code': item.get('error_code', ''),
                    'entities': " ".join(entities),
                    'sha256': sha
                }
                records.append((rec_id, text, meta))
        
        if records:
            if model is None:
                print("Loading embedding model (SentenceTransformer)...", flush=True)
                model = get_model()
            texts = [r[1] for r in records]
            print(f"Embedding {len(texts)} corpus chunks from {source_name}...", flush=True)
            vectors = model.encode(['passage: ' + t for t in texts], batch_size=32, normalize_embeddings=True)
            collection.upsert(
                ids=[r[0] for r in records],
                documents=texts,
                embeddings=vectors.tolist(),
                metadatas=[r[2] for r in records]
            )
            manifest[source_name] = {'sha256': sha, 'chunks': len(records)}
            print(f"Indexed {len(records)} chunks from {source_name}.", flush=True)

    # 2. Index PDF files (manuals + academic papers)
    import pymupdf
    pdf_files = sorted(DOCUMENTS.rglob('*.pdf'))
    for pfile in pdf_files:
        source_name = pfile.relative_to(DOCUMENTS).as_posix()
        sha = hashlib.sha256(pfile.read_bytes()).hexdigest()
        if not args.force and manifest.get(source_name, {}).get('sha256') == sha:
            print(f"SKIP unchanged PDF: {source_name}", flush=True)
            continue
        print(f"\nProcessing PDF: {source_name}...", flush=True)
        try:
            with pymupdf.open(pfile) as pdf:
                if model is None:
                    print("Loading embedding model (SentenceTransformer)...", flush=True)
                    model = get_model()
                records = []
                for page_no, page in enumerate(pdf, start=1):
                    raw = page.get_text('text', sort=True)
                    chunks = list(segment_text(raw, model.tokenizer))
                    for chunk_no, chunk in enumerate(chunks, start=1):
                        rec_id = hashlib.sha256(f"{source_name}|{sha}|{page_no}|{chunk_no}".encode('utf-8')).hexdigest()
                        entities = extract_entities(chunk)
                        meta = {
                            'source': source_name,
                            'title': pfile.stem,
                            'page': page_no,
                            'chunk': chunk_no,
                            'entities': " ".join(entities),
                            'sha256': sha
                        }
                        records.append((rec_id, chunk, meta))
        except Exception as e:
            print(f"ERROR reading {source_name}: {e}", file=sys.stderr)
            continue

        if not records:
            print(f"WARNING: No extractable text in {source_name}.", flush=True)
            continue

        print(f"Embedding and inserting {len(records)} chunks for {source_name}...", flush=True)
        t0 = time.time()
        batch_size = 48
        for i in range(0, len(records), batch_size):
            batch = records[i:i+batch_size]
            b_docs = [r[1] for r in batch]
            b_vectors = model.encode(['passage: ' + d for d in b_docs], batch_size=len(batch), normalize_embeddings=True)
            collection.upsert(
                ids=[r[0] for r in batch],
                documents=b_docs,
                embeddings=b_vectors.tolist(),
                metadatas=[r[2] for r in batch]
            )
            print(f"  Inserted {min(i+batch_size, len(records))}/{len(records)} chunks...", end='\r', flush=True)
        elapsed = time.time() - t0
        print(f"\nCompleted {source_name} ({len(records)} chunks) in {elapsed:.1f}s.", flush=True)
        manifest[source_name] = {'sha256': sha, 'chunks': len(records)}

    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding='utf-8')
    total_count = collection.count()
    print(f"\n==========================================")
    print(f"Ingestion done! Collection '{coll_name}' total chunks: {total_count}")
    print(f"Database saved to: {DATABASE}")
    print(f"==========================================")
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
