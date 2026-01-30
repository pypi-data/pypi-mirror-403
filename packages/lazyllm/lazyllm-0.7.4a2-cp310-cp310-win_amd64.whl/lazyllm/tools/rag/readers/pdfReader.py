import io
from pathlib import Path
from typing import List, Optional, Callable
from lazyllm.common import retry
from lazyllm.thirdparty import fsspec, pypdf
from lazyllm import LOG

from .readerBase import get_default_fs, is_default_fs
from ..doc_node import DocNode
from .readerBase import _RichReader

RETRY_TIMES = 3


class PDFReader(_RichReader):
    """Reader for extracting text content from PDF files.

Args:
    split_doc (bool): If True (default), parses into a `RichDocNode` which can be used with `RichTransform` to extract nodes with page information;
        if False, parses into a plain text `DocNode`.
    post_func (Optional[Callable[[List[DocNode]], List[DocNode]]]): Post-processing function.
        Must return a ``List[DocNode]`` and will write ``extra_info`` into each node's ``global_metadata``.
    return_trace (bool): Whether to return the processing trace. Default is True.
    return_full_document (bool, deprecated): This parameter will be removed in a future version. Please use `split_doc` instead.

Notes:
    When `split_doc=True`, returns a `RichDocNode`; otherwise returns a `DocNode`. Both cases return a single node.
    When `split_doc=True`, it is strongly recommended to use it with `RichTransform`, which can extract nodes with page information and other metadata;
    without `RichTransform`, the parsed nodes will fall back to plain text nodes.
"""
    def __init__(self, split_doc: bool = True,
                 post_func: Optional[Callable[[List[DocNode]], List[DocNode]]] = None,
                 return_trace: bool = True, *, return_full_document=None) -> None:
        if return_full_document is not None:
            LOG.warning('return_full_document is deprecated, please use split_doc instead')
            assert split_doc ^ return_full_document, \
                'split_doc and return_full_document cannot be both True or False'
            split_doc = not return_full_document
        super().__init__(post_func=post_func, split_doc=split_doc, return_trace=return_trace)

    @retry(stop_after_attempt=3)
    def _load_data(self, file: Path, fs: Optional['fsspec.AbstractFileSystem'] = None) -> List[DocNode]:
        if not isinstance(file, Path): file = Path(file)

        fs = fs or get_default_fs()
        with fs.open(file, 'rb') as fp:
            stream = fp if is_default_fs(fs) else io.BytesIO(fp.read())
            pdf = pypdf.PdfReader(stream)
            num_pages = len(pdf.pages)
            docs = []
            if self._split_doc:
                for page in range(num_pages):
                    page_text = pdf.pages[page].extract_text()
                    page_label = pdf.page_labels[page]
                    metadata = {'page_label': page_label}
                    docs.append(DocNode(text=page_text, metadata=metadata))
            else:
                text = '\n'.join(pdf.pages[page].extract_text() for page in range(num_pages))
                docs.append(DocNode(text=text))
            return docs
