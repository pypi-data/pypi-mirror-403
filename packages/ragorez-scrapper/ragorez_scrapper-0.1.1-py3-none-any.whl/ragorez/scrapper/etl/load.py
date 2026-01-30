import chromadb


class Loader:
    def save(self, chunks: list):
        pass


class ChromaDBLoader(Loader):
    def __init__(self, collection: chromadb.Collection):
        self.collection = collection

    def save(self, chunks):
        return save_to_chroma(chunks, self.collection)


def save_to_chroma(chunks: list, collection: chromadb.Collection):
    documents = []
    ids = []
    for i, chunk in enumerate(chunks):
        documents.append(chunk)
        ids.append(f"chunk_{i}")
    collection.add(documents=documents, ids=ids)
    return collection
