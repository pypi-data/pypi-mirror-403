from ragorez.common.text_transformations import delete_spaces_and_new_lines, transform_to_chunks


class Cleaner:
    def clean(self, text: str) -> str:
        pass


class DefaultRegexpCleaner(Cleaner):
    def clean(self, text: str) -> str:
        return delete_spaces_and_new_lines(text)


class Transformator:
    def get_chunks(self, text: str) -> list[str]:
        pass


class DefaultTransformator(Transformator):
    def __init__(self, chunk_size, overlap):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def get_chunks(self, text: str) -> list[str]:
        return transform_to_chunks(text, self.chunk_size, self.overlap)
