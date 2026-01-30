from dataclasses import dataclass
from typing import Dict

import chromadb


@dataclass
class Chunk:
    text: str
    id: str
    metadata: Dict = None


class Loader:
    def save(self, chunks: list[Chunk]):
        pass


class ChromaDBLoader(Loader):
    def __init__(self, collection: chromadb.Collection):
        self.collection = collection

    def save(self, chunks: list[Chunk]):
        return save_to_chroma(chunks, self.collection)


def save_to_chroma(chunks: list[Chunk], collection: chromadb.Collection):
    documents = []
    ids = []
    for chunk in chunks:
        documents.append(chunk.text)
        ids.append(chunk.id)
    collection.add(documents=documents, ids=ids)
    return collection
