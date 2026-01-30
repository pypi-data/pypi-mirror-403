from rara_meta_extractor.regex_extractors import ISBNRegexExtractor
import pytest


def test_isbn_regex_extraction():
    ex = ISBNRegexExtractor()
    test_texts = [
        "Keskus Praxis ; ISBN 897 -9949 -662-25-5 (pdf)",
        "balabla S 897 9949 662 25 5 aa",
        "balabla ISBN 897     9949 662    25 5 aa",
        "balabla ISBN 897-9949-662-25-5 aa",
        "balabla ISBN 897 9949 662 - 25 5 aa",
        "balabla ISBN 897   -9949-662 - 25- 5 aa"
    ]
    for text in test_texts:
        isbn = ex.extract(text)
        assert len(isbn) == 1
        assert isbn[0] == "8979949662255"