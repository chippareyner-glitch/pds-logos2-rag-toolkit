"""Search Pango PDS, Logos-2, and Academic LLM Papers RAG Knowledge Base.

Usage: python search.py "FlightLLM DSP" --top-k 3 --max-chars 800 --json
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

from rag_common import COLLECTION_NAME, get_collection, get_model, keywords


def main() -> int:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description='Search PDS Logos-2 & LLM Accelerator KB.')
    parser.add_argument('question', help='Your search query; Chinese and English both work.')
    parser.add_argument('--top-k', type=int, default=4, help='Max cited passages (default: 4).')
    parser.add_argument('--max-chars', type=int, default=900, help='Characters per passage (default: 900).')
    parser.add_argument('--mode', choices=['hybrid', 'semantic', 'keyword'], default='hybrid')
    parser.add_argument('--collection', default=COLLECTION_NAME, help=f'Target collection (default: {COLLECTION_NAME}).')
    parser.add_argument('--json', action='store_true', help='Machine-readable result for Claude Code / Codex.')
    args = parser.parse_args()
    top_k = max(1, min(args.top_k, 15))
    max_chars = max(200, min(args.max_chars, 5000))

    coll_name = args.collection
    _, collection = get_collection(coll_name)
    count = collection.count()
    if count == 0:
        print(f"Index empty for collection '{coll_name}'. Please run: python build_index.py --collection {coll_name}", file=sys.stderr)
        return 2

    pool = min(count, max(24, top_k * 6))
    scores = defaultdict(float)
    details = {}

    # Dense Semantic Search (Weight 0.6)
    if args.mode in ('hybrid', 'semantic'):
        model = get_model()
        query_vector = model.encode(['query: ' + args.question], normalize_embeddings=True)[0]
        result = collection.query(
            query_embeddings=[query_vector.tolist()],
            n_results=pool,
            include=['documents', 'metadatas', 'distances']
        )
        if result['ids'] and result['ids'][0]:
            for rank, (id_, doc, meta) in enumerate(zip(result['ids'][0], result['documents'][0], result['metadatas'][0]), start=1):
                scores[id_] += 0.6 * (1.0 / (60 + rank))
                details[id_] = (doc, meta)

    # Sparse BM25 Search (Weight 0.4)
    if args.mode in ('hybrid', 'keyword'):
        from rank_bm25 import BM25Okapi
        all_docs = collection.get(include=['documents', 'metadatas'])
        if all_docs['documents']:
            tokenized = [keywords(x + " " + (m.get('entities', '') if m else '') + " " + (m.get('tags', '') if m else '')) for x, m in zip(all_docs['documents'], all_docs['metadatas'])]
            query_tokens = keywords(args.question)
            if query_tokens:
                bm25 = BM25Okapi(tokenized)
                raw_scores = bm25.get_scores(query_tokens)
                positions = sorted(range(len(raw_scores)), key=lambda i: raw_scores[i], reverse=True)
                rank = 0
                for i in positions:
                    if raw_scores[i] <= 0 or rank >= pool:
                        break
                    rank += 1
                    id_ = all_docs['ids'][i]
                    scores[id_] += 0.4 * (1.0 / (60 + rank))
                    details[id_] = (all_docs['documents'][i], all_docs['metadatas'][i])

    ranked = sorted(scores, key=lambda x: scores[x], reverse=True)[:top_k]
    hits = []
    for rank, id_ in enumerate(ranked, start=1):
        doc, meta = details[id_]
        hits.append({
            'rank': rank,
            'source': meta.get('source', ''),
            'title': meta.get('title', ''),
            'item_id': meta.get('item_id', ''),
            'tags': meta.get('tags', ''),
            'pdf_page': meta.get('page', 1),
            'error_code': meta.get('error_code', ''),
            'entities': meta.get('entities', ''),
            'text': doc[:max_chars] + (' ... [truncated]' if len(doc) > max_chars else ''),
        })

    if args.json:
        print(json.dumps({
            'question': args.question,
            'collection': coll_name,
            'mode': args.mode,
            'total_hits': len(hits),
            'hits': hits
        }, ensure_ascii=False, indent=2))
    else:
        if not hits:
            print('No matches found. Try refining your query.')
        for h in hits:
            title_part = f" - {h['title']}" if h['title'] else ""
            err_part = f" [{h['error_code']}]" if h['error_code'] else ""
            tag_part = f" | Tags: {h['tags']}" if h['tags'] else ""
            print(f"\n[{h['rank']}] {h['source']} | Page {h['pdf_page']}{title_part}{err_part}{tag_part}")
            print(h['text'])
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
