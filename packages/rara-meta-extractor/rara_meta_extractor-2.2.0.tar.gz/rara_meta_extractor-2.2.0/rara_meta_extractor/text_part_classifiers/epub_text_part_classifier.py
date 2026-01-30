import json
import regex as re
from typing import List, Tuple, Dict
from rara_meta_extractor.config import LOGGER
from rara_meta_extractor.constants.data_classes import TextPartLabel, MetaField
from rara_meta_extractor.text_part_classifiers.base_text_part_classifier import BaseTextPartClassifier

class EPUBTextPartClassifier(BaseTextPartClassifier):
    def __init__(self):
        super().__init__()
        self.used_sections: list = []
        self.section_title_filter: List[str] = [
            "peatükk", "stseen", "vaatus", "osa", "jagu",
            "üks", "kaks", "kolm", "esimene", "teine", "kolmas"
        ]
        self.section_title_filter_roman: List[str] = [
            "II", "IV", "IX", "ii", "iv",
            "ix", "Ii", "Iv", "Ix", "XII"
        ]
        self.section_title_filter_numbers: List[str] = [
            "1", "2", "3", "4", "5"
        ]
        self.conclusion_upper_keywords: list = []


    def _clean_text(self, text_dict: dict) -> dict:
        """ EPUB texts sometimes contain multiple different whitespace
        characters in a row, e.g. "\n ". Remove newline characters for
        these cases.
        """
        text = text_dict.get("text_value")
        if text and isinstance(text, list):
            text = text[0]
        if not isinstance(text, str):
            LOGGER.error(f"Invalid text type in EPUB meta. Expected str, got: {type(text)}")
            text = ""
        else:
            text = re.sub(r"\n ", " ", text)
        text_dict["text_value"] = text
        return text

    def _toc_from_section_titles(self, digitized_texts: List[dict])-> List[dict]:
        """ Trying to put together a table of contents
        for ebooks through section titles.
        """
        # Filter for getting rid of nondescript chapter names
        # we don't want in out table of contents
        toc = []
        title_not_none = [
            txt for txt in digitized_texts
            if txt.get("section_title", None)
        ]

        if len(set([section["section_title"] for section in title_not_none])) > 1:
            for section in title_not_none:
                stripped_title = section["section_title"].strip().strip(",.")
                if stripped_title in self.section_title_filter_roman:
                    return toc
                if stripped_title in self.section_title_filter_numbers:
                    return toc
                for filter_item in self.section_title_filter:
                    if filter_item in stripped_title.lower():
                        return toc
            for section in title_not_none:
                section_title = section.get("section_title")
                text = section.get("text")
                if section_title == text:
                    continue
                if section_title not in toc:
                    toc.append(section_title)
        return toc

    def _ebooks_get_conclusion_from_meta(self, parsed_meta: dict )-> list:
        """ Using different methods to find conclusions.
        """
        if MetaField.INCLUDED_TEXT in parsed_meta:
            if parsed_meta[MetaField.INCLUDED_TEXT] != None:
                return [parsed_meta[MetaField.INCLUDED_TEXT]]
        return []

    def get_conclusions(self, digitized_texts: List[dict], epub_meta: dict = {}):
        """ Using different methods to find conclusions.
        """
        LOGGER.debug(f"Searching for conclusions.")
        concl = self._look_through_section_titles(
            digitized_texts=digitized_texts,
            search_type=TextPartLabel.CONCLUSION
        )
        if not concl:
            concl = self._look_through_texts(
                digitized_texts=digitized_texts,
                search_type=TextPartLabel.CONCLUSION
            )

        # Second option: get conclusion info
        # from parsed_meta (if exists)
        if not concl:
            # ... or whatever key parsed meta is saved as
            if epub_meta:
                # No language data in parsed metadata, so used as second option
                concl = self._ebooks_get_conclusion_from_meta(
                    parsed_meta=epub_meta
                )
        cleaned_concl = []
        for c in concl:
            cl_c = self._clean_text(c)
            cleaned_concl.append(cl_c)
        return cleaned_concl

    def get_tables_of_content(self, digitized_texts: List[dict]):
        """ Using different methods to find tables of content
        for ebook files.
        """
        LOGGER.debug(f"Searching for tables_of_content.")
        # Since ebooks don't have authors names associated with chapters,
        # we first try to fetch section titles by themselves
        toc = self._toc_from_section_titles(digitized_texts=digitized_texts)
        LOGGER.debug(f"Detected Table of Content from EPUB Meta: {toc}")
        if not toc:
            # After this we look at where the toc should be
            # according to section titles and extract the text
            toc = self._look_through_section_titles(
                digitized_texts=digitized_texts,
                search_type=TextPartLabel.TABLE_OF_CONTENTS
            )
        if not toc:
            # After this we look at the text itself using keywords
            toc = self._look_through_texts(
                digitized_texts=digitized_texts,
                search_type=TextPartLabel.TABLE_OF_CONTENTS
            )
        return toc

    def get_abstracts(self, digitized_texts: List[dict]):
        """ Using different methods to find abstracts.
        """
        LOGGER.debug(f"Searching for abstracts.")
        abstracts = self._look_through_section_titles(
            digitized_texts=digitized_texts,
            search_type=TextPartLabel.ABSTRACT
        )
        if not abstracts:
            abstracts = self._look_through_texts(
            digitized_texts=digitized_texts,
            search_type=TextPartLabel.ABSTRACT
        )
        return abstracts

    def get_parts_of_text(self, digitized_texts: List[dict], epub_meta: dict) -> dict:
        """ Getting results for ebooks.

        Parameters
        -----------
        digitized_texts: List[dict]
            `texts` from Digitizer output.
        epub_meta: dict
            Output of `EPUBMetaExtractor.extract_meta()`.

        Returns
        -----------
        dict
            TODO
        """
        LOGGER.info(f"Classifying EPUB text sections.")
        tables_of_content = self.get_tables_of_content(
            digitized_texts=digitized_texts
        )
        conclusions = self.get_conclusions(
            digitized_texts=digitized_texts,
            epub_meta=epub_meta
        )
        abstracts = self.get_abstracts(
            digitized_texts=digitized_texts
        )
        results = self._results_correct_fields(
            {
                "table_of_contents": tables_of_content,
                "conclusions": conclusions,
                "abstracts": abstracts
            }
        )
        return results
