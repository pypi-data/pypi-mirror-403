from .base import NodeTransform
from ..doc_node import RichDocNode, DocNode
from typing import List


class RichTransform(NodeTransform):
    """
Transform a `RichDocNode` into a list of `DocNode` objects, and preserve the metadata of each `DocNode`.
The input must be a `RichDocNode` instance.

Args:
    node (RichDocNode): Rich document node to unwrap.

Returns:
    List[DocNode]: The underlying node list.


Examples:
    
    >>> from lazyllm.tools.rag.transform import RichTransform
    >>> nodes = RichTransform().transform(rich_node)
    """
    __support_rich__ = True

    def _clone_node(self, n: DocNode) -> DocNode:
        new_node = DocNode(content=n.text, metadata=n.metadata,
                           global_metadata=n.global_metadata)
        new_node.excluded_embed_metadata_keys = n.excluded_embed_metadata_keys
        new_node.excluded_llm_metadata_keys = n.excluded_llm_metadata_keys
        return new_node

    def transform(self, node: RichDocNode, **kwargs) -> List[DocNode]:
        assert isinstance(node, RichDocNode), f'Expected RichDocNode, got {type(node)}'
        return [self._clone_node(sub_node) for sub_node in node.nodes]
