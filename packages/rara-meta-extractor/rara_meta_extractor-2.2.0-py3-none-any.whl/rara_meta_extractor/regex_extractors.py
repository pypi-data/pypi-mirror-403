import regex as re
from typing import List
from rara_meta_extractor.config import LOGGER

class ISBNRegexExtractor:
    """ Regex-based ISBN extractor.
    """
    def __init__(self):
        self.pattern = re.compile(r"(?<=\D|^)(\d\s*-?\s*){13}(?=\D|[^-]|$)")

    def _clean(self, isbn: str) -> str:
        """ Cleans extracted ISBNs from "-" and from whitespaces.

        Parameters
        -----------
        isbn: str
            Extracted raw ISBN number which might contain additional
            punctuation characters.

        Returns
        -----------
        str:
            Cleaned ISBN number.
        """
        isbn = re.sub(r"-", "", isbn)
        isbn = re.sub(r"\s+", "", isbn)
        isbn = isbn.strip()
        return isbn

    def _clean_isbns(self, isbns: List[str]) -> List[str]:
        """ Clean ISBN matches

        Parameters
        -----------
        isbns: List[str]
            ISBN matches to clean.

        Returns
        ----------
        List[str]:
            Cleaned ISBN numbers.
        """
        cleaned = [self._clean(isbn) for isbn in isbns]
        return cleaned


    def _filter_isbns(self, isbns: List[str]) -> List[str]:
        """ Filter out matches that contain "\n" as they
        are very probable false positives. ISBN numbers do not usually
        span over multiple lines.

        Parameters
        -----------
        isbns: List[str]
            ISBN matches to filter.

        Returns
        ----------
        List[str]:
            Filtered ISBN numbers.
        """
        filtered = []
        for isbn in isbns:
            if "\n" not in isbn.strip():
                filtered.append(isbn)
        return filtered

    def extract(self, text: str) -> List[str]:
        """ Extracts ISBN numbers from the input text.

        Parameters
        -----------
        text: str
            Text from where to extract the numbers.

        Returns
        ----------
        List[str]:
            Extracted and cleaned ISBN numbers.
        """
        isbns = [match.group() for match in re.finditer(self.pattern, text)]

        isbns = self._filter_isbns(isbns)
        isbns = self._clean_isbns(isbns)
        return isbns
