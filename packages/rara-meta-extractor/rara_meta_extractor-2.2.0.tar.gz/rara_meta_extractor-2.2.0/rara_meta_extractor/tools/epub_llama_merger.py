from rara_meta_extractor.config import (
    LOGGER
)
from rara_meta_extractor.constants.data_classes import (
    MetaField, ExtractorType, MergeMethod
)
from rara_meta_extractor.tools.meta_formatter import MetaValidator
from rara_meta_extractor.regex_extractors import ISBNRegexExtractor
from collections import defaultdict
from typing import List, NoReturn

class EpubLlamaMerger:
    """ For merging meta detected with LlamaExtractor and/or EPUBMetaExtractor.
    """
    def __init__(self, epub_meta: dict, llama_meta: dict, text: str,
            field_method_map: dict, default_merge_method: str
    ) -> NoReturn:
        self.epub_meta: dict = epub_meta
        self.llama_meta: dict = llama_meta
        self.text: str = text
        self.llama_epub_field_map: dict = field_method_map
        self.default_merge_method: str = default_merge_method

        self.meta_validator = MetaValidator()
        self.isbn_regex_extractor = ISBNRegexExtractor()


    def _is_valid_key(self, field: str) -> bool:
        return self.meta_validator._is_valid_key(field)


    @property
    def epub_fields(self) -> List[str]:
        return list(self.epub_meta.keys())

    @property
    def llama_fields(self) -> List[str]:
        return list(self.llama_meta.keys())

    @property
    def common_fields(self) -> List[str]:
        return list(set(self.epub_fields).intersection(set(self.llama_fields)))

    @property
    def union_fields(self) -> List[str]:
        fields = list(set(self.epub_fields).union(set(self.llama_fields)))
        fields = [field for field in fields if self._is_valid_key(field)]
        return fields

    @property
    def epub_unique_fields(self) -> List[str]:
        return list(set(self.epub_fields) - set(self.llama_fields))

    @property
    def llama_unique_fields(self) -> List[str]:
        return list(set(self.llama_fields) - set(self.epub_fields))

    @property
    def epub_titles(self) -> List[dict]:
        return self.epub_meta.get(MetaField.TITLES, [])

    @property
    def llama_titles(self) -> List[dict]:
        return self.llama_meta.get(MetaField.TITLES, [])

    @property
    def epub_authors(self) -> List[dict]:
        return self.epub_meta.get(MetaField.AUTHORS, [])

    @property
    def llama_authors(self) -> List[dict]:
        return self.llama_meta.get(MetaField.AUTHORS, [])

    @property
    def epub_authors_str(self) -> List[dict]:
        return [author.get("name") for author in self.epub_authors]

    @property
    def llama_authors_str(self) -> List[dict]:
        return [author.get("name") for author in self.llama_authors]

    @property
    def unique_llama_authors(self) -> List[dict]:
        unique = set(self.llama_authors_str) - set(self.epub_authors_str)
        filtered = [author for author in self.llama_authors if author.get("name") in unique]
        return filtered

    @property
    def unique_epub_authors(self) -> List[dict]:
        unique = set(self.epub_authors_str) - set(self.llama_authors_str)
        filtered = [author for author in self.epub_authors if author.get("name") in unique]
        return filtered

    @property
    def common_authors(self) -> List[str]:
        common = list(set(self.epub_authors_str).intersection(set(self.llama_authors_str)))
        return common

    def _get_titles_map(self, meta: dict) -> dict:
        titles = meta.get(MetaField.TITLES, [])
        titles_map = defaultdict(list)

        for title in titles:
            key = title.get("title_type_int")
            titles_map[key].append(title)

        return titles_map

    def _is_capitalized(self, title: str) -> bool:
        title_words = [word.strip() for word in title.split() if word.strip()]
        for word in title_words:
            if len(word) > 3 and  word[0] != word[0].upper():
                return False
        return True


    def _select_title(self, key: str, llama_title: dict, epub_title: dict) -> dict:
        llama_title_str = llama_title.get("title", "")
        epub_title_str = epub_title.get("title", "")

        if llama_title_str and not epub_title_str:
            title = llama_title
        elif epub_title_str and not llama_title_str:
            title = epub_title
        elif llama_title_str.lower() == epub_title_str.lower():
            if self._is_capitalized(epub_title_str) or not self._is_capitalized(llama_title_str):
                title = epub_title
            else:
                title = llama_title
        elif llama_title_str.lower() in epub_title_str.lower():
            if ":" in epub_title_str and ":" not in llama_title_str:
                title = epub_title
            else:
                title = llama_title
        else:
            title = epub_title

        if title.get("title") == epub_title_str:
            LOGGER.debug(
                f"Title key = {key}. Using title extracted with EPUB-Extractor ({epub_title_str}). " \
                f"Ignoring title extracted with Llama-Extractor ({llama_title_str})."
            )
        else:
            LOGGER.debug(
                f"Title key = {key}. Using title extracted with Llama-Extractor ({llama_title_str}). " \
                f"Ignoring title extracted with EPUB-Extractor ({epub_title_str})."
            )
        return title

    def _get_unique_titles(self, titles_map: dict, common_keys: List[str], extractor_type: str) -> List[dict]:
        unique_titles = []
        for key, titles in titles_map.items():
            if key not in common_keys:
                LOGGER.debug(f"Adding titles unique to extraction method '{extractor_type}'into results: {titles}")
                unique_titles.extend(titles)
        return unique_titles


    def _merge_titles(self):
        LOGGER.info(f"Comparing titles extracted with LLama-Extractor and EPUB-Extractor...")
        llama_titles_map = self._get_titles_map(self.llama_meta)
        epub_titles_map = self._get_titles_map(self.epub_meta)

        common_keys = list(set(llama_titles_map.keys()).intersection(epub_titles_map.keys()))
        titles = []
        epub_title_added = False

        for key in common_keys:
            # Take just the first title  with that type,
            # not sure, if it is even possible to have more
            # than one title per title type
            epub_title = epub_titles_map.get(key)[0]
            llama_title = llama_titles_map.get(key)[0]
            final_title = self._select_title(key=key, llama_title=llama_title, epub_title=epub_title)
            titles.append(final_title)
            epub_title_added = True

        llama_unique_titles = self._get_unique_titles(llama_titles_map, common_keys, ExtractorType.LLAMA)
        epub_unique_titles = self._get_unique_titles(epub_titles_map, common_keys, ExtractorType.EPUB)

        if epub_unique_titles:
            epub_title_added = True
        titles.extend(epub_unique_titles)

        # Add titles unique to Llama ONLY IF no EPUB titles have been added
        # in order to avoid weird combinations
        if not epub_title_added:
            titles.extend(llama_unique_titles)
        return titles

    def _merge_authors(self):
        merged_authors = []
        merged_authors.extend(self.unique_llama_authors)
        merged_authors.extend(self.unique_epub_authors)

        for author in self.common_authors:
            roles = set()
            for llama_author in self.llama_authors:
                if llama_author.get("name") == author and llama_author.get("role") not in roles:
                    roles.add(llama_author.get("role"))
                    merged_authors.append(llama_author)

            for epub_author in self.epub_authors:
                if epub_author.get("name") == author and epub_author.get("role") not in roles:
                    roles.add(epub_author.get("role"))
                    merged_authors.append(epub_author)
        return merged_authors

    def _run_value_selection(self, field: str, merge_method: str) -> None | List[dict] | List[str] | str:
        value = None
        LOGGER.info(f"Running value selection for field '{field.upper()}' with merge method = {merge_method}.")
        if merge_method in [MergeMethod.EPUB_SOFT, MergeMethod.EPUB_HARD]:
            value = self.epub_meta.get(field)
        elif merge_method in [MergeMethod.LLAMA_SOFT, MergeMethod.LLAMA_HARD]:
            value = self.llama_meta.get(field)
        if merge_method == MergeMethod.EPUB_SOFT and not value:
            LOGGER.debug(
                f"Could not detect the value for field '{field.upper()}' from EPUB meta, " \
                f"trying to retrieve it from Llama meta."
            )
            value = self.llama_meta.get(field)
        if merge_method == MergeMethod.LLAMA_SOFT and not value:
            LOGGER.debug(
                f"Could not detect the value for field '{field.upper()}' from Llama meta, " \
                f"trying to retrieve it from EPUB meta."
            )
            value = self.epub_meta.get(field)
        return value

    @property
    def authors(self) -> List[dict]:
        LOGGER.debug(f"EPUB authors: {self.epub_authors}")
        LOGGER.debug(f"Llama authors: {self.llama_authors}")
        merge_method = self.llama_epub_field_map.get(MetaField.AUTHORS, MergeMethod.COMBO)
        LOGGER.info(f"Running AUTHORS selection with merge method = {merge_method}.")
        if merge_method == MergeMethod.COMBO:
            authors = self._merge_authors()

        else:
            authors = self._run_value_selection(field=MetaField.AUTHORS, merge_method=merge_method)

        roles = [author.get("role").lower() for author in authors]

        if "autor" in roles:
            authors = [author for author in authors if author.get("role").lower() != "unknown"]
        # If we could not detect an author, assume that the one with unknown role might be one
        elif "unknown" in roles:
            for author in authors:
                if author.get("role") == "unknown":
                    author["role"] = "Autor"
        return authors

    @property
    def titles(self) -> List[dict]:
        merge_method = self.llama_epub_field_map.get(MetaField.TITLES, MergeMethod.COMBO)
        LOGGER.info(f"Running TITLES selection with merge method = {merge_method}.")
        if merge_method == MergeMethod.COMBO:
            titles = self._merge_titles()
        else:
            titles = self._run_value_selection(field=MetaField.TITLES, merge_method=merge_method)
        return titles

    @property
    def isbn(self) -> List[str]:
        merge_method = self.llama_epub_field_map.get(MetaField.ISBN, MergeMethod.REGEX)
        LOGGER.info(f"Running ISBN selection with merge method = {merge_method}.")
        if merge_method == MergeMethod.REGEX:

            isbn = self.isbn_regex_extractor.extract(self.text)
            LOGGER.debug(f"ISBNs detected with REGEX: {isbn}")
        else:
            isbn = self._run_value_selection(field=MetaField.ISBN, merge_method=merge_method)
        return isbn


    def _get_merge_method(self, field: str) -> str:
        field_1 = "_".join(field.split())
        field_2 = " ".join(field.split("_"))
        merge_method = self.llama_epub_field_map.get(field_1, None)
        if not merge_method:
            merge_method = self.llama_epub_field_map.get(field_2, self.default_merge_method)
        return merge_method


    def merge(self) -> dict:
        LOGGER.info(f"EPUB meta to merge: {self.epub_meta}")
        LOGGER.info(f"Llama meta to merge: {self.llama_meta}")
        merged_meta = {}

        for field in self.union_fields:
            if field == MetaField.TITLES:
                merged_meta[field] = self.titles
            elif field == MetaField.AUTHORS:
                merged_meta[field] = self.authors
            elif field == MetaField.ISBN:
                merged_meta[field] = self.isbn
            else:
                merge_method = self._get_merge_method(field)
                LOGGER.info(f"Running {field.upper()} selection with merge method = {merge_method}.")
                merged_meta[field] = self._run_value_selection(field=field, merge_method=merge_method)

        return merged_meta
