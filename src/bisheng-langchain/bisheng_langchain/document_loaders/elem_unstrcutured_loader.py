      
# flake8: noqa
"""Loads PDF with semantic splilter."""
import base64
import logging
import os
from typing import List

import requests
from langchain.docstore.document import Document
from langchain.document_loaders.pdf import BasePDFLoader

logger = logging.getLogger(__name__)


def merge_partitions(partitions):
    text_elem_sep = '\n'
    doc_content = []
    is_first_elem = True
    last_label = ''
    prev_length = 0
    metadata = dict(bboxes=[], pages=[], indexes=[], types=[])
    for part in partitions:
        label, text = part['type'], part['text']
        extra_data = part['metadata']['extra_data']
        if is_first_elem:
            f_text = text + '\n' if label == 'Title' else text
            doc_content.append(f_text)
            is_first_elem = False
        else:
            if last_label == 'Title' and label == 'Title':
                doc_content.append('\n' + text)
            elif label == 'Title':
                doc_content.append('\n\n' + text)
            elif label == 'Table':
                doc_content.append('\n\n' + text)
            else:
                doc_content.append(text_elem_sep + text)

        last_label = label
        metadata['bboxes'].extend(list(map(lambda x: list(map(int, x)), extra_data['bboxes'])))
        metadata['pages'].extend(extra_data['pages'])
        metadata['types'].extend(extra_data['types'])

        indexes = extra_data['indexes']
        up_indexes = [[s + prev_length, e + prev_length] for (s, e) in indexes]
        metadata['indexes'].extend(up_indexes)
        prev_length += len(doc_content[-1])

    content = ''.join(doc_content)
    return content, metadata


class ElemUnstructuredLoader(BasePDFLoader):
    """Loads a PDF with pypdf and chunks at character level. dummy version

    Loader also stores page numbers in metadata.
    """

    def __init__(self,
                 file_name: str,
                 file_path: str,
                 unstructured_api_key: str = None,
                 unstructured_api_url: str = None,
                 start: int = 0,
                 n: int = None,
                 verbose: bool = False,
                 kwargs: dict = {}) -> None:
        """Initialize with a file path."""
        self.unstructured_api_url = unstructured_api_url
        self.unstructured_api_key = unstructured_api_key
        self.headers = {'Content-Type': 'application/json'}
        self.file_name = file_name
        self.start = start
        self.n = n
        self.extra_kwargs = kwargs
        super().__init__(file_path)

    def load(self) -> List[Document]:
        """Load given path as pages."""
        b64_data = base64.b64encode(open(self.file_path, 'rb').read()).decode()
        parameters = {'start': self.start, 'n': self.n}
        parameters.update(self.extra_kwargs)
        payload = dict(filename=os.path.basename(self.file_name),
                       b64_data=[b64_data],
                       mode='partition',
                       parameters=parameters)

        resp = requests.post(self.unstructured_api_url, headers=self.headers, json=payload).json()

        if 200 != resp.get('status_code'):
            logger.info(f'not return resp={resp}')
        partitions = resp['partitions']
        if not partitions:
            logger.info(f'partition_error resp={resp}')
        logger.info(f'unstruct_return code={resp.get("status_code")}')

        partitions = resp['partitions']
        content, metadata = merge_partitions(partitions)
        metadata['source'] = self.file_name

        doc = Document(page_content=content, metadata=metadata)
        return [doc]


class ElemUnstructuredLoaderV0(BasePDFLoader):
    """The appropriate parser is automatically selected based on the file format and OCR is supported
    """

    def __init__(self,
                 file_name: str,
                 file_path: str,
                 is_skip: bool,
                 unstructured_api_key: str = None,
                 unstructured_api_url: str = None,
                 start: int = 0,
                 n: int = None,
                 verbose: bool = False,
                 kwargs: dict = {}) -> None:
        """Initialize with a file path."""
        self.unstructured_api_url = unstructured_api_url
        self.unstructured_api_key = unstructured_api_key
        self.start = start
        self.n = n
        self.headers = {'Content-Type': 'application/json'}
        self.file_name = file_name
        self.is_skip = is_skip
        self.extra_kwargs = kwargs
        super().__init__(file_path)

    def load(self) -> List[Document]:
        if self.is_skip:
            logger.info("文档已存在向量库，跳过解析")
            return []
        else:
            b64_data = base64.b64encode(open(self.file_path, 'rb').read()).decode()
            payload = dict(filename=os.path.basename(self.file_name), b64_data=[b64_data], mode='text')
            payload.update({'start': self.start, 'n': self.n})
            payload.update(self.extra_kwargs)
            resp = requests.post(self.unstructured_api_url, headers=self.headers, json=payload).json()

            if 200 != resp.get('status_code'):
                logger.info(f'not return resp={resp}')

            page_content = resp['text']
            meta = {'source': self.file_name}
            doc = Document(page_content=page_content, metadata=meta)
            return [doc]

    