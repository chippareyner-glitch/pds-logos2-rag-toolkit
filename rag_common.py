"""Shared configuration and utilities for Pango PDS & Logos-2 RAG."""
from __future__ import annotations

import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DOCUMENTS = ROOT / 'documents'
DATABASE = ROOT / 'database'
MODEL_NAME = 'intfloat/multilingual-e5-small'
COLLECTION_NAME = os.getenv('RAG_COLLECTION', 'pds_logos2_pnr_sta_kb')
CHUNK_TOKENS = 320
OVERLAP_TOKENS = 40

TOKEN_RE = re.compile(r'[a-zA-Z_][a-zA-Z0-9_.-]*|\d+|[\u4e00-\u9fff]')

def keywords(text: str) -> list[str]:
    return TOKEN_RE.findall(text.lower())

def get_collection(coll_name: str | None = None):
    import chromadb
    DATABASE.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(DATABASE))
    name = coll_name or COLLECTION_NAME
    coll = client.get_or_create_collection(name=name)
    return client, coll

def get_model():
    os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(MODEL_NAME, device=os.getenv('RAG_DEVICE', 'cpu'))

def segment_text(text: str, tokenizer):
    text = text.replace('\x00', '').replace('\r\n', '\n').replace('\r', '\n')
    if len(text.strip()) < 30:
        return
    offsets = tokenizer(text, add_special_tokens=False, return_offsets_mapping=True, truncation=False)['offset_mapping']
    stride = CHUNK_TOKENS - OVERLAP_TOKENS
    for i in range(0, len(offsets), stride):
        batch = offsets[i:i + CHUNK_TOKENS]
        if not batch:
            break
        start, end = batch[0][0], batch[-1][1]
        snippet = text[start:end].strip()
        if len(snippet) >= 30:
            yield snippet
        if i + CHUNK_TOKENS >= len(offsets):
            break
