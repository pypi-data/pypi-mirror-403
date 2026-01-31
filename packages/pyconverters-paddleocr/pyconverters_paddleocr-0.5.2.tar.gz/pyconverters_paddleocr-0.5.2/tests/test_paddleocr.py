from pathlib import Path
from typing import List

import pytest
from pymultirole_plugins.v1.schema import Document
from starlette.datastructures import UploadFile

from pyconverters_paddleocr.paddleocr import PaddleOCRConverter, PaddleOCRParameters


# @pytest.mark.skip(reason="Not a test")
def test_paddleocr_pdf():
    converter = PaddleOCRConverter()
    parameters = PaddleOCRParameters(base_url="http://188.231.87.195:9093", max_pages_split=10,
                                     include_image_base64_as_altTexts=True)
    # parameters = PaddleOCRParameters(segment=True)
    testdir = Path(__file__).parent
    source = Path(testdir, "data/ENG product fact files_general offer_2025_30pages.pdf")
    with source.open("rb") as fin:
        docs: List[Document] = converter.convert(
            UploadFile(source.name, fin, "application/pdf"), parameters
        )
    assert len(docs) == 1
    assert docs[0].identifier == 'ENG product fact files_general offer_2025_30pages.pdf'
    assert docs[0].title == '2025 GENERAL SPORTS OFFER PRODUCT FACT FILE'

    json_file = source.with_suffix(".json")
    with json_file.open("w") as fout:
        print(docs[0].json(exclude_none=True, exclude_unset=True, indent=2), file=fout)

    md_file = source.with_suffix(".md")
    with md_file.open("w") as fout:
        fout.write(docs[0].text)


@pytest.mark.skip(reason="Not a test")
def test_paddleocr_pdf_no_latex():
    converter = PaddleOCRConverter()
    parameters = PaddleOCRParameters(base_url="http://188.231.87.195:9093")
    testdir = Path(__file__).parent
    source = Path(testdir, "data/ijms-22-07070-v2.pdf")
    with source.open("rb") as fin:
        docs: List[Document] = converter.convert(
            UploadFile(source.name, fin, "application/pdf"), parameters
        )
    assert len(docs) == 1
    assert docs[0].identifier == 'ijms-22-07070-v2.pdf'
    assert "$" not in docs[0].text

    json_file = source.with_suffix(".json")
    with json_file.open("w") as fout:
        print(docs[0].json(exclude_none=True, exclude_unset=True, indent=2), file=fout)
