import base64
import io
import logging
import mimetypes
import os
import re
from functools import lru_cache
from pathlib import Path
from tempfile import SpooledTemporaryFile
from typing import List, cast, Type

import pymupdf
import requests
from bs4 import BeautifulSoup
from markdownify import MarkdownConverter
from pydantic import Field, BaseModel
from pylatexenc.latex2text import latex2text
from pylatexenc.latexwalker import LatexWalkerError
from pymultirole_plugins.v1.converter import ConverterParameters, ConverterBase
from pymultirole_plugins.v1.schema import Document, Boundary, AltText
from starlette.datastructures import UploadFile

logger = logging.getLogger("pymultirole")

PADDLEOCR_URL = os.getenv(
    "PADDLEOCR_URL", None
)


class PaddleOCRParameters(ConverterParameters):
    base_url: str = Field(
        PADDLEOCR_URL,
        description="""PaddleOCR endpoint base url""", extra="advanced"
    )
    max_pages_split: int = Field(
        -1,
        description="""To split a large PDF file into files of no more than max pages""",
        extra="advanced"
    )
    latex_to_text: bool = Field(
        True,
        description="""Convert LaTeX codes to plain text with unicode characters"""
    )
    include_image_base64_as_altTexts: bool = Field(
        False, extra="advanced",
        description="""To include the image data as base64 altTexts"""
    )


class PaddleOCRConverter(ConverterBase):
    """PaddleOCR PDF converter ."""

    def convert(
            self, source: UploadFile, parameters: ConverterParameters
    ) -> List[Document]:
        params: PaddleOCRParameters = cast(PaddleOCRParameters, parameters)
        client = get_client(params.base_url)
        docs = []
        doc = client.split_and_convert(source, params)
        docs.append(doc)
        return docs

    @classmethod
    def get_model(cls) -> Type[BaseModel]:
        return PaddleOCRParameters


@lru_cache(maxsize=None)
def get_client(base_url):
    client = PaddleOCRClient(base_url)
    return client


def auto_table_headers(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for table in soup.find_all("table"):
        first_row = table.find("tr")
        if first_row:
            for cell in first_row.find_all("td", recursive=False):
                cell.name = "th"
    return str(soup)


class PaddleOCRClient:
    def __init__(self, base_url):
        self.base_url = base_url[0:-1] if base_url.endswith("/") else base_url
        self.use_base64 = True
        self.dsession = requests.Session()
        self.dsession.headers.update({
            'Accept': 'application/json'
        })
        self.dsession.verify = False

    def split_and_convert(self, source: UploadFile, params: PaddleOCRParameters):
        docs = {}
        max_pages = params.max_pages_split

        if max_pages > 0:
            pdfdoc = pymupdf.open(stream=source.file.read())
            total_pages = pdfdoc.page_count
            for start in range(0, total_pages, max_pages):
                end = min(start + max_pages, total_pages)
                pdfpart = pymupdf.open()  # nouveau PDF
                for page_num in range(start, end):
                    pdfpart.insert_pdf(pdfdoc, from_page=page_num, to_page=page_num)
                partbytes = pdfpart.tobytes()
                partfile = UploadFile(filename=source.filename, file=io.BytesIO(partbytes))
                doc = self.convert(partfile, start, params)
                docs[start] = (doc)
                pdfpart.close()
            pdfdoc.close()
        else:
            docs[0] = self.convert(source, 0, params)

        if len(docs) > 0:
            consolidated = docs.pop(0)
            for start, doc in docs.items():
                offset = len(doc.text)
                consolidated.text += doc.text
                consolidated.altTexts.extend(doc.altTexts)
                consolidated.boundaries['page'].extend([Boundary(start=b.start + offset, end=b.end + offset) for b in doc.boundaries['page']])
            return consolidated
        else:
            return docs

    def convert(self, source: UploadFile, part: int, params: PaddleOCRParameters):
        doc = None
        altTexts = []
        latex_regex = r"(\$[^\$]+\$)"
        link_regex = r"<div[^>]*><img src=\"([^\"]*)\"[^>]*></div>"
        title_regex = r"^(#{1,6})\s+(.*)$"
        table_regex = r"<table[^>]*>.*</table>"
        md = MarkdownConverter(heading_style='atx', sup_symbol=" ")
        input_file = source.file._file if isinstance(source.file, SpooledTemporaryFile) else source.file

        try:
            file_url = None
            if self.use_base64:
                data = source.file.read()
                rv = base64.b64encode(data)
                file_url = rv.decode('utf-8')
            else:
                file_url = self.upload(source)
            if file_url is not None:
                resp = self.dsession.post(
                    f"{self.base_url}/layout-parsing",
                    json={
                        'file': file_url,
                        'fileType': 0
                    },
                    headers={'content-type': 'application/json'},
                )
                if resp.ok:
                    result = resp.json()
                    if result['errorCode'] == 0:
                        pages = []
                        start = 0
                        text = ""
                        title = None
                        for pi, page in enumerate(result['result']['layoutParsingResults']):
                            markdown = page['markdown']['text']
                            images = page['markdown']['images']
                            if pi == 0:
                                firstline = markdown.split('\n', 1)[0] if '\n' in markdown else markdown
                                match = re.match(title_regex, firstline)
                                if match:
                                    title = match.group(2)  # texte du titre

                            def convert_latex(matchobj):
                                m = matchobj.group(0)
                                try:
                                    return latex2text(m)
                                except LatexWalkerError:
                                    # logger.warning("An exception was thrown during lateX conversion!", exc_info=True)
                                    return m

                            ptext = re.sub(latex_regex, convert_latex, markdown, 0, re.MULTILINE) if params.latex_to_text else markdown

                            def convert_links(matchobj):
                                m = matchobj.group(0)
                                m_id = matchobj.group(1)
                                link = m
                                if m_id in images:
                                    m_path = Path(m_id)
                                    img_id = f"{part}/{m_id}"
                                    mime_type, _ = mimetypes.guess_type(m_path)
                                    m_url = f"data:{mime_type};base64,{images[m_id]}"
                                    if params.include_image_base64_as_altTexts:
                                        altTexts.append(
                                            AltText(name=img_id, text=m_url, properties={'mime-type': mime_type}))
                                        link = f"![{img_id}]({m_id})"
                                return link
                            if params.include_image_base64_as_altTexts:
                                ptext = re.sub(link_regex, convert_links, ptext, 0,
                                               re.MULTILINE) if params.latex_to_text else page['markdown']

                            def convert_tables(matchobj):
                                m = matchobj.group(0)
                                html = auto_table_headers(m)
                                table = md.convert(html)
                                return table

                            ptext = re.sub(table_regex, convert_tables, ptext, 0,
                                           re.MULTILINE)

                            text += ptext + '\n'
                            pages.append(Boundary(start=start, end=len(text)))
                            start = len(text)
                        doc = Document(identifier=source.filename, title=title or source.filename, text=text,
                                       altTexts=altTexts,
                                       boundaries={'page': pages},
                                       metadata={'original': source.filename, 'mime-type': 'text/markdown'})
                else:
                    logger.warning(f"Unsuccessful OCR conversion: {source.filename}")
                    resp.raise_for_status()
        except BaseException as err:
            logger.error(
                f"Cannot convert PDF from file {source.filename}, type={type(input_file)}",
                exc_info=True,
            )
            raise err
        return doc
