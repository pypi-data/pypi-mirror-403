import warnings

from tqdm import tqdm

from .etl.extraction import Extractor
from .etl.load import Loader, Chunk
from .etl.transformation import Cleaner, Transformator


def generate_chunk_id(source: str, number: int) -> str:
    return f"{source}-{number}"


class ScrapperPipeline:
    def __init__(
            self,
            extractors: list[Extractor],
            cleaners: list[Cleaner],
            transformator: Transformator,
            loaders: list[Loader],
            disable_logging=False,
    ):
        self.extractors = extractors
        self.cleaners = cleaners
        self.transformator = transformator
        self.loaders = loaders
        self.disable_logging = disable_logging

    def process(self, resources: str | list[str]):
        if isinstance(resources, str):
            resources = [resources]
        for resource in tqdm(
                resources, desc="Processing resources", disable=self.disable_logging
        ):
            extractor = [i for i in self.extractors if i.is_extractable(resource)]
            if len(extractor) == 0:
                raise Exception("extractor not found")
            if len(extractor) > 1:
                warnings.warn(
                    f"several extractors found for resource {resource}. Extractors: {extractor}"
                )
            extractor = extractor[0]
            text = extractor.extract(resource)
            for cleaner in self.cleaners:
                text = cleaner.clean(text)
            text_chunks = self.transformator.get_chunks(text)
            chunks = []
            for i, text_chunk in enumerate(text_chunks):
                chunks.append(Chunk(text=text_chunk, id=generate_chunk_id(resource, i)))
            for loader in self.loaders:
                loader.save(chunks)
