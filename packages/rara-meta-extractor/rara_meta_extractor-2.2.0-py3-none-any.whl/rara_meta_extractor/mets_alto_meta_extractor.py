from rara_tools.parsers.mets_alto_parsers.mets_alto_parser import DocumentMeta
from rara_meta_extractor.constants.data_classes import  TitleType, AuthorNameOrder
from rara_meta_extractor.tools.meta_formatter import Author, Title
from copy import deepcopy
from typing import List


class MetsAltoOutputEnricher:
    """ Enriches parsed METS/ALTO with necessary
    title and author fields.
    """
    def __init__(self, doc: dict):
        self.original_doc: dict = doc

    @staticmethod
    def enrich_titles(titles: List[dict], simple: bool = False) -> List[dict]:
        """ Add information expected by Kratt CORE to each title.
        """
        enriched_titles =  []

        # The current Title formatter is a bit illogical
        # as it takes in a list of titles instead of a single one.
        # However, we would like to add language separately for each title,
        # so we just call the formatter multiple times
        for title in titles:
            new_titles = Title(
                titles = [title.get("title")],
                lang = title.get("language"),
                part_number = title.get("part_number"),
                title_type=TitleType.METS_TITLE
            ).to_dicts(simple=simple)
            enriched_titles.extend(new_titles)
        return enriched_titles

    @staticmethod
    def enrich_authors(authors: List[dict]) -> List[dict]:
        """ Add information expected by Kratt CORE to each author.
        """
        enriched_authors = []

        for i, author in enumerate(authors):
            name = f"{author.get('first_name')} {author.get('last_name')}"
            author_name_order = AuthorNameOrder.FIRST_NAME_FIRST
            #is_primary = True if i == 0 else False

            new_author = Author(
                name=name,
                role=author.get("role"),
                author_type=author.get("type"),
                author_name_order=author_name_order,
                is_primary=True,
                map_role=False
            ).to_dict()
            enriched_authors.append(new_author)
        return enriched_authors

    def enrich(self, simple: bool = False) -> dict:
        """ Add information expected by Kratt CORE to titles & authors
        (the whole document + sections).
        """
        extracted_meta: dict = deepcopy(self.original_doc)

        # Main titles & authors
        titles = extracted_meta.pop("title", [])
        authors = extracted_meta.pop("authors", [])

        enriched_titles = MetsAltoOutputEnricher.enrich_titles(titles=[titles], simple=simple)
        enriched_authors = MetsAltoOutputEnricher.enrich_authors(authors=authors)
        if titles:
            extracted_meta["titles"] = enriched_titles
        if authors:
            extracted_meta["authors"] = enriched_authors

        # Section titles & authors
        sections = extracted_meta.pop("sections", [])
        enriched_sections = []
        for section in sections:
            titles = section.pop("titles", [])
            merged_titles = section.pop("merged_titles", [])
            merged_titles = [title for title in merged_titles if title.get("title")]
            authors = section.pop("authors", [])

            authors = [author for author in authors if author.get("first_name") or author.get("")]

            if not authors and not merged_titles:
                continue

            enriched_authors = MetsAltoOutputEnricher.enrich_authors(authors=authors)
            enriched_titles = MetsAltoOutputEnricher.enrich_titles(titles=merged_titles, simple=simple)

            section["titles"] = enriched_titles
            section["authors"] = enriched_authors

            enriched_sections.append(section)
        extracted_meta["sections"] = enriched_sections
        return extracted_meta


class MetsAltoMetaExtractor:
    def __init__(self, mets_alto_metadata: List[dict], language: str, texts: List[dict]):
        self.digitizer_output: dict = self.reconstruct_digitizer_output(
            mets_alto_metadata=mets_alto_metadata,
            language=language,
            texts=texts
        )
        self.document_meta: dict = DocumentMeta(self.digitizer_output).to_dict()
        self.output_enricher = MetsAltoOutputEnricher(self.document_meta)

    def reconstruct_digitizer_output(
            self, mets_alto_metadata: List[str] = [], language: str = "", texts: List[dict] = []
        ) -> dict:
        """ Partially reconstructs digitizer output as the new Mets/Alto meta extractor
        expects this format.
        """
        digitizer_output = {
            "doc_meta": {
                "mets_alto_metadata": mets_alto_metadata,
                "languages": [{"language": language}]
            },
            "texts": texts
        }
        return digitizer_output

    def remove_empty(self, meta: dict) -> dict:
        """ Removes empty meta fields.
        """
        sections = meta.pop("sections", [])
        cleaned_sections = []
        for section in sections:
            new_section = {}
            for key, value in section.items():
                if value:
                    new_section[key] = value
            cleaned_sections.append(new_section)

        new_meta = {}
        for key, value in meta.items():
            if value:
                new_meta[key] = value
        new_meta["sections"] = cleaned_sections
        return new_meta

    def reformat_fields(self, meta: dict) -> dict:
        """ Rename fields & reformat data structures.
        """
        isbn = meta.pop("isbn", "")
        issn = meta.pop("issn", "")
        content_type = meta.pop("resource_type", "")
        if isbn:
            meta["isbn"] = [isbn]
        if issn:
            meta["issn"] = [issn]
        if content_type:
            meta["content_type"] = content_type
        return meta

    def extract_meta(self, simple: bool = False) -> dict:
        """ Extract metadata. Use mainly DocumentMeta class,
        but reformat / enrich content of some fields like titles and authors.
        """
        extracted_meta = self.output_enricher.enrich(simple=simple)
        extracted_meta = self.remove_empty(extracted_meta)
        extracted_meta = self.reformat_fields(extracted_meta)
        return extracted_meta
