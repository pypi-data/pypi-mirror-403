from typing import List, Optional, Union, Dict, Set, Callable, Any
from lazyllm import ModuleBase, once_wrapper, LOG, TempPathGenerator, parallel

from .doc_node import DocNode
from enum import Enum
from .document import Document, UrlDocument, DocImpl
from .store import LAZY_ROOT_NAME
from .similarity import registered_similarities
import functools
import lazyllm


class _PostProcess(object):
    def __init__(self, output_format: Optional[str] = None, join: Union[bool, str] = False) -> None:
        assert output_format in (None, 'content', 'dict'), 'output_format should be None, \'content\', or \'dict\''
        self._output_format = output_format
        if join is True: join = ''
        assert join is False or (isinstance(join, str) and output_format == 'content'), (
            'Only content output can be joined')
        self._join = join

    def _post_process(self, nodes):
        if self._output_format == 'content':
            nodes = [node.get_content() for node in nodes]
            if isinstance(self._join, str): nodes = self._join.join(nodes)
        elif self._output_format == 'dict':
            nodes = [node.to_dict() for node in nodes]
        return nodes


class _RetrieverBase(ModuleBase):
    class Priority(str, Enum):
        ignore = 'ignore'
        low = 'low'
        normal = 'normal'
        high = 'high'

        def __repr__(self): return self.casefold()


class Retriever(_RetrieverBase, _PostProcess):
    """
Create a retrieval module for document querying and retrieval. This constructor initializes a retrieval module that configures the document retrieval process based on the specified similarity metric.

Args:
    doc: An instance of the document module. The document module can be a single instance or a list of instances. If it is a single instance, it means searching for a single Document, and if it is a list of instances, it means searching for multiple Documents.
    group_name: The name of the node group on which to perform the retrieval.
    similarity: The similarity function to use for setting up document retrieval. Defaults to 'dummy'. Candidates include ["bm25", "bm25_chinese", "cosine"].
    similarity_cut_off: Discard the document when the similarity is below the specified value. In a multi-embedding scenario, if you need to specify different values for different embeddings, you need to specify them in a dictionary, where the key indicates which embedding is specified and the value indicates the corresponding threshold. If all embeddings use the same threshold, you only need to specify one value.
    index: The type of index to use for document retrieval. Currently, only 'default' is supported.
    topk: The number of documents to retrieve with the highest similarity.
    embed_keys: Indicates which embeddings are used for retrieval. If not specified, all embeddings are used for retrieval.
    target:The name of the target document group for result conversion
    output_format: Represents the output format, with a default value of None. Optional values include 'content' and 'dict', where 'content' corresponds to a string output format and 'dict' corresponds to a dictionary.
    join:  Determines whether to concatenate the output of k nodes - when output format is 'content', setting True returns a single concatenated string while False returns a list of strings (each corresponding to a node's text content); when output format is 'dict', joining is unsupported (join defaults to False) and the output will be a dictionary containing 'content', 'embedding' and 'metadata' keys.

The `group_name` has three built-in splitting strategies, all of which use `SentenceSplitter` for splitting, with the difference being in the chunk size:

- CoarseChunk: Chunk size is 1024, with an overlap length of 100
- MediumChunk: Chunk size is 256, with an overlap length of 25
- FineChunk: Chunk size is 128, with an overlap length of 12

Also, `Image` is available for `group_name` since LazyLLM supports image embedding and retrieval.


Examples:
    
    >>> import lazyllm
    >>> from lazyllm.tools import Retriever, Document, SentenceSplitter
    >>> m = lazyllm.OnlineEmbeddingModule()
    >>> documents = Document(dataset_path='/path/to/user/data', embed=m, manager=False)
    >>> rm = Retriever(documents, group_name='CoarseChunk', similarity='bm25', similarity_cut_off=0.01, topk=6)
    >>> rm.start()
    >>> print(rm("user query"))
    >>> m1 = lazyllm.TrainableModule('bge-large-zh-v1.5').start()
    >>> document1 = Document(dataset_path='/path/to/user/data', embed={'online':m , 'local': m1}, manager=False)
    >>> document1.create_node_group(name='sentences', transform=SentenceSplitter, chunk_size=1024, chunk_overlap=100)
    >>> retriever = Retriever(document1, group_name='sentences', similarity='cosine', similarity_cut_off=0.4, embed_keys=['local'], topk=3)
    >>> print(retriever("user query"))
    >>> document2 = Document(dataset_path='/path/to/user/data', embed={'online':m , 'local': m1}, manager=False)
    >>> document2.create_node_group(name='sentences', transform=SentenceSplitter, chunk_size=512, chunk_overlap=50)
    >>> retriever2 = Retriever([document1, document2], group_name='sentences', similarity='cosine', similarity_cut_off=0.4, embed_keys=['local'], topk=3)
    >>> print(retriever2("user query"))
    >>>
    >>> filters = {
    >>>     "author": ["A", "B", "C"],
    >>>     "public_year": [2002, 2003, 2004],
    >>> }
    >>> document3 = Document(dataset_path='/path/to/user/data', embed={'online':m , 'local': m1}, manager=False)
    >>> document3.create_node_group(name='sentences', transform=SentenceSplitter, chunk_size=512, chunk_overlap=50)
    >>> retriever3 = Retriever([document1, document3], group_name='sentences', similarity='cosine', similarity_cut_off=0.4, embed_keys=['local'], topk=3)
    >>> print(retriever3(query="user query", filters=filters))
    >>> document4 = Document(dataset_path='/path/to/user/data', embed=lazyllm.TrainableModule('siglip'))
    >>> retriever4 = Retriever(document4, group_name='Image', similarity='cosine')
    >>> nodes = retriever4("user query")
    >>> print([node.get_content() for node in nodes])
    >>> document5 = Document(dataset_path='/path/to/user/data', embed=m, manager=False)
    >>> rm = Retriever(document5, group_name='CoarseChunk', similarity='bm25_chinese', similarity_cut_off=0.01, topk=3, output_format='content')
    >>> rm.start()
    >>> print(rm("user query"))
    >>> document6 = Document(dataset_path='/path/to/user/data', embed=m, manager=False)
    >>> rm = Retriever(document6, group_name='CoarseChunk', similarity='bm25_chinese', similarity_cut_off=0.01, topk=3, output_format='content', join=True)
    >>> rm.start()
    >>> print(rm("user query"))
    >>> document7 = Document(dataset_path='/path/to/user/data', embed=m, manager=False)
    >>> rm = Retriever(document7, group_name='CoarseChunk', similarity='bm25_chinese', similarity_cut_off=0.01, topk=3, output_format='dict')
    >>> rm.start()
    >>> print(rm("user query"))
    """
    def __init__(self, doc: object, group_name: str, similarity: Optional[str] = None,
                 similarity_cut_off: Union[float, Dict[str, float]] = float('-inf'), index: str = 'default',
                 topk: int = 6, embed_keys: Optional[List[str]] = None, target: Optional[str] = None,
                 output_format: Optional[str] = None, join: Union[bool, str] = False,
                 weight: Optional[float] = None, priority: Optional[_RetrieverBase.Priority] = None, **kwargs):
        super().__init__()

        if similarity:
            _, mode, _ = registered_similarities[similarity]
        else:
            similarity = 'cosine'
            mode = 'embedding'  # TODO FIXME XXX should be removed after similarity args refactor
        group_name, target = str(group_name), (str(target) if target else None)

        self._docs: List[Document] = [doc] if isinstance(doc, Document) else doc
        # NOTE: multi docs is deprecated and will be removed in the future
        if len(self._docs) > 1:
            LOG.warning('[Retriever] Multi docs is deprecated and will be removed in the future,'
                        ' please use multiple Retrievers instead.')
        self._group_name = group_name
        if index == 'smart_embedding_index':
            index = 'default'
            LOG.warning('[Retriever] `smart_embedding_index` is deprecated, converted to `default`')
        self._mode = mode
        self._index = index
        self._topk = topk
        self._similarity = similarity  # similarity function str
        self._similarity_kw = kwargs  # kw parameters
        self._similarity_cut_off = similarity_cut_off
        self._embed_keys = embed_keys
        self._per_doc_embed_keys = False
        self._target = target
        self._weight, self._priority = weight, priority
        if weight or priority:
            assert not (weight and priority), f'Cannot provide weight({weight}) and priority({priority}) together!'
            assert not output_format or not join, 'shouldn\'t provide output_format/join when weight or priority is set'

        self._init_submodules_and_embed_keys()
        _PostProcess.__init__(self, output_format, join)

    weight = property(lambda self: self._weight)
    priority = property(lambda self: self._priority)

    @once_wrapper
    def _lazy_init(self):
        docs = []
        per_doc_embed_keys = [] if self._per_doc_embed_keys else None
        for idx, doc in enumerate(self._docs):
            if isinstance(doc, UrlDocument) or self._group_name in doc._impl.node_groups \
                    or self._group_name in DocImpl._builtin_node_groups \
                    or self._group_name in DocImpl._global_node_groups:
                docs.append(doc)
                if self._per_doc_embed_keys:
                    per_doc_embed_keys.append(self._embed_keys[idx])
        if not docs: raise RuntimeError(f'Group {self._group_name} not found in document {self._docs}')
        self._docs = docs
        if self._per_doc_embed_keys:
            self._embed_keys = per_doc_embed_keys

    def _init_submodules_and_embed_keys(self):
        group_name = self._group_name
        embed_keys = self._embed_keys
        self._per_doc_embed_keys = (not embed_keys and self._mode == 'embedding')
        if self._per_doc_embed_keys:
            # NOTE: store per-doc embed keys aligned with self._docs order
            self._embed_keys = []
        for doc in self._docs:
            assert isinstance(doc, (Document, UrlDocument)), 'Only Document or List[Document] are supported'
            if isinstance(doc, UrlDocument):
                if embed_keys:
                    self._validate_remote_vec_retr_params(doc, group_name, embed_keys)
                else:
                    group_name, doc_embed_keys = self._validate_remote_vec_retr_params(doc, group_name, None)
                    if self._per_doc_embed_keys:
                        self._embed_keys.append(doc_embed_keys)
                continue
            self._submodules.append(doc)
            if self._per_doc_embed_keys:
                doc_embed_keys = list(doc._impl.embed.keys())
                self._embed_keys.append(doc_embed_keys)
            else:
                doc_embed_keys = embed_keys
            doc.activate_group(group_name, doc_embed_keys)
            if self._target: doc.activate_group(self._target)

    def __getstate__(self):
        state = {'group_name': self._group_name, 'similarity': self._similarity,
                 'similarity_cut_off': self._similarity_cut_off, 'index': self._index, 'topk': self._topk,
                 'similarity_kw': self._similarity_kw, 'embed_keys': self._embed_keys, 'target': self._target,
                 'output_format': self._output_format, 'join': self._join,
                 'per_doc_embed_keys': self._per_doc_embed_keys}
        docs = []
        for doc in self._docs:
            if isinstance(doc, UrlDocument):
                docs.append({'url': doc._manager._url, 'name': doc._curr_group})
            else:
                assert isinstance(doc._manager._kbs, lazyllm.ServerModule), \
                    'Only UrlDocument and Document with ServerModule are supported'
                docs.append({'url': doc._manager._kbs._url, 'name': doc._curr_group})
        state['docs'] = docs
        return state

    def __setstate__(self, state):
        ModuleBase.__init__(self)
        self._group_name = state['group_name']
        self._similarity = state['similarity']
        self._similarity_cut_off = state['similarity_cut_off']
        self._index = state['index']
        self._topk = state['topk']
        self._similarity_kw = state['similarity_kw']
        self._embed_keys = state['embed_keys']
        self._per_doc_embed_keys = state.get('per_doc_embed_keys', False)
        self._target = state['target']
        self._output_format = state['output_format']
        self._join = state['join']
        self._docs = [Document(url=doc['url'], name=doc['name']) for doc in state['docs']]
        _PostProcess.__init__(self, self._output_format, self._join)

    def _validate_remote_vec_retr_params(self, doc: UrlDocument, group_name, embed_keys: Optional[List[str]] = None):
        active_groups = doc.active_node_groups
        if not active_groups:
            raise RuntimeError(f'No active groups found in document {doc._manager._url}')
        if group_name not in active_groups:
            raise RuntimeError(f'Group {group_name} not found or not activated in document {doc._manager._url}')
        if not embed_keys:
            resolved_embed_keys = list(active_groups[group_name])
            return group_name, resolved_embed_keys
        else:
            for k in embed_keys:
                if k not in active_groups[group_name]:
                    raise RuntimeError(f'Embedding key {k} not found in group {group_name} '
                                       f'from document {doc._manager._url},'
                                       f'available keys: {list(active_groups[group_name])}')
            return group_name, embed_keys

    def forward(
            self, query: str, filters: Optional[Dict[str, Union[str, int, List, Set]]] = None,
            **kwargs
    ) -> Union[List[DocNode], str]:
        self._lazy_init()
        all_nodes: List[DocNode] = []
        if self._per_doc_embed_keys:
            if len(self._embed_keys) != len(self._docs):
                raise RuntimeError('Per-doc embed_keys misaligned with docs after lazy init')
        for idx, doc in enumerate(self._docs):
            embed_keys = self._embed_keys[idx] if self._per_doc_embed_keys else self._embed_keys
            nodes = doc.forward(query=query, group_name=self._group_name, similarity=self._similarity,
                                similarity_cut_off=self._similarity_cut_off, index=self._index,
                                topk=self._topk, similarity_kws=self._similarity_kw, embed_keys=embed_keys,
                                filters=filters, **kwargs)
            if nodes and self._target and self._target != nodes[0]._group:
                nodes = doc.find(self._target)(nodes)
            all_nodes.extend(nodes)
        return self._post_process(all_nodes)


class TempRetriever(_RetrieverBase, _PostProcess):
    """
TempRetriever Base class. used for `TempDocRetriever` and `ContextRetriever`.

Args:
    embed: The embedding function.
    output_format: The format of the output result (e.g., JSON). Optional, defaults to None.
    join: Whether to merge multiple result segments (set to True or specify a separator like "
").
"""
    def __init__(self, embed: Callable = None, output_format: Optional[str] = None, join: Union[bool, str] = False):
        super().__init__()
        self._doc = Document(doc_files=[])
        self._embed = embed
        self._node_groups = []
        _PostProcess.__init__(self, output_format, join)

    def create_node_group(self, name: str = None, *, transform: Callable, parent: str = LAZY_ROOT_NAME,
                          trans_node: bool = None, num_workers: int = 0, **kwargs):
        """
Create document processing node group for configuring document chunking and transformation strategies.

Args:
    name (str): Name of the node group. Auto-generated if None.
    transform (Callable): Function to process documents in this group.
    parent (str): Parent group name. Defaults to root group.
    trans_node (bool): Whether to transform nodes. Inherits from parent if None.
    num_workers (int): Parallel workers for processing. Default 0 (sequential).
    **kwargs: Additional group parameters.

**Returns:**

- self: Current instance supporting chained calls
"""
        self._doc.create_node_group(name, transform=transform, parent=parent,
                                    trans_node=trans_node, num_workers=num_workers, **kwargs)
        return self

    def add_subretriever(self, group: str, **kwargs):
        """
Add a sub-retriever with search configuration.

Args:
    group (str): Target node group name.
    **kwargs: Retriever configuration parameters including:
        - similarity (str): Similarity calculation method, 'cosine' (cosine similarity) or 'bm25' (BM25 algorithm)
        - Other retriever-specific parameters

**Returns:**

- self: For method chaining.
"""
        if 'similarity' not in kwargs: kwargs['similarity'] = ('cosine' if self._embed else 'bm25')
        self._node_groups.append((group, kwargs))
        return self

    def _get_retrievers_impl(self, doc_files: List[str], init: bool = False):
        active_node_groups = self._node_groups or [[Document.MediumChunk,
                                                    dict(similarity=('cosine' if self._embed else 'bm25'))]]
        doc = Document(embed=self._embed, doc_files=doc_files)
        doc._impl.node_groups = self._doc._impl.node_groups
        retrievers = [Retriever(doc, name, **kw) for (name, kw) in active_node_groups]
        if init: lazyllm.parallel(*retrievers).sum('hello world')
        return retrievers

    def _get_retrievers(self, doc_files: List[str], init: bool = False):
        raise NotImplementedError('Please implement it at subclass')

    def forward(self, files: Union[str, List[str]], query: str):
        if isinstance(files, str): files = [files]
        retrievers = self._get_retrievers(tuple(set(files)))
        r = lazyllm.parallel(*retrievers).sum
        return self._post_process(r(query))


class TempDocRetriever(TempRetriever):
    """
A temporary document retriever that inherits from TempRetriever, used for quickly processing temporary files and performing retrieval tasks.

Args:
    embed: The embedding function.
    output_format: The format of the output result (e.g., JSON). Optional, defaults to None.
    join: Whether to merge multiple result segments (set to True or specify a separator like "
").


Examples:
    
    >>> import lazyllm
    >>> from lazyllm.tools import TempDocRetriever, Document, SentenceSplitter
    >>> retriever = TempDocRetriever(output_format="text", join="
    ---------------
    ")
        retriever.create_node_group(transform=lambda text: [s.strip() for s in text.split("。") if s] )
        retriever.add_subretriever(group=Document.MediumChunk, topk=3)
        files = ["/path/to/file.txt"]
        results = retriever.forward(files, "什么是机器学习?")
        print(results)
    """
    @functools.lru_cache(maxsize=128)  # noqa B019
    def _get_retrievers(self, doc_files: List[str]):
        return self._get_retrievers_impl(doc_files)

    def __del__(self):
        self._get_retrievers.cache_clear()


class ContextRetriever(TempRetriever):
    """
A context-based retriever that inherits from TempRetriever, designed to perform retrieval directly over in-memory text content rather than physical document files.

It internally converts the provided context strings into temporary files using TempPathGenerator, builds retrievers on demand, and caches them for efficient reuse.

Args:
    embed: The embedding function used for vector-based retrieval. If not provided, a keyword-based method (e.g., BM25) is used.
    output_format: The format of the output result (e.g., "text", "json"). Optional, defaults to None.
    join: Whether to merge multiple retrieved segments. Can be True or a custom separator string such as "\n".


Examples:
    >>> ctx1 = '大学之道，在明明德，
    在亲民，在止于至善。
    知止而后有定，定而后能静，静而后能安。'
    >>> ctx2 = '子曰：学而时习之，不亦说乎？
    有朋自远方来，不亦乐乎？'
    >>> ret = ContextRetriever(output_format='dict')
    >>> ret.create_node_group('block', transform=lambda x: x.split('
    '))
    >>> ret.add_subretriever(Document.CoarseChunk, topk=1)
    >>> ret.add_subretriever('block', topk=3)
    >>> ret([ctx1, ctx2], '大学')
    """
    def forward(self, context: Union[str, List[str]], query):
        return super().forward(context, query)

    @functools.lru_cache(maxsize=128)  # noqa B019
    def _get_retrievers(self, context: List[str]):
        with TempPathGenerator(context) as pathes:
            return super()._get_retrievers_impl(pathes, init=True)

    def __del__(self):
        self._get_retrievers.cache_clear()


class _CompositeRetrieverBase(_RetrieverBase, _PostProcess):
    def __init__(self, *retrievers: List[Retriever], strict: bool = True, topk: Optional[int] = None,
                 output_format: Optional[str] = None, join: Union[bool, str] = False):
        super().__init__()
        if retrievers:
            self._check_retrievers(retrievers)
            self._cached_values = None
        self._retrievers = parallel(*retrievers)
        self._strict = strict
        self._valid = False  # will be set in _further_check
        self._capture = False
        self._topk = topk
        _PostProcess.__init__(self, output_format, join)

    _items = property(lambda self: self._retrievers._items)
    submodules = property(lambda self: self._items)

    def __enter__(self):
        assert len(self._items) == 0, f'Cannot init {self.__class__}\'s element twice! Existing element: {self._items}'
        assert not self._capture, f'{self.__class__}.__erter__() cannot support multi-thread'
        self._capture = True
        self._retrievers.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._retrievers.__exit__(exc_type, exc_val, exc_tb)
        self._capture = False
        self._check_retrievers(self._items)
        self._cached_values = None

    def __setattr__(self, name: str, value):
        if name not in self.__dict__ and '_capture' in self.__dict__ and self._capture:
            setattr(self._retrievers, name, value)
        else:
            super(__class__, self).__setattr__(name, value)

    def _check_retrievers(self, retrievers: List[Retriever]):
        if not retrievers: return
        for v in retrievers:
            if self._strict and not isinstance(v, _RetrieverBase): raise RuntimeError(
                'Non-Retriever element detected. If you insist on using it, please set strict=False.')
            if getattr(v, '_output_format', None) or getattr(v, '_join', None):
                raise RuntimeError(f'You should set output_format / join to {self.__class__} instead of sub-retrievers')
        self._further_check(retrievers)

    def _get_cached_value(self, name, default=None):
        if getattr(self, '_cached_values', None) is None:
            self._cached_values = [(getattr(r, name, default) or default) for r in self._items]
        return self._cached_values

    @staticmethod
    def _real_params_checkf(x): raise NotImplementedError()

    def _get_real_params(self, params, name, err_msg):
        if params:
            if len(params) != len(self._items):
                raise RuntimeError(f'Dimension mismatch: expected {len(self._items)} {name} '
                                   f'for {len(self._items)} retrievers, but got {len(params)}.')
            if (error := list(p for p in params if not self.__class__._real_params_checkf(p))):
                raise RuntimeError(f'Invalid {name}: all {name} must be one of {err_msg}, yours are {error}')
        elif self._valid:
            params = getattr(self, name)
        else:
            raise RuntimeError(f'`{name}` not fully provided, please check your parameters')
        return params

    def _further_check(self, retrievers: List[Retriever]): pass


class WeightedRetriever(_CompositeRetrieverBase):
    """
WeightedRetriever combines multiple Retrievers by weighting their retrieval results.

Key characteristics:
- **Priority is not allowed**: Sub-retrievers must not define a priority attribute.
- **Weight consistency enforced**: If any retriever defines a weight, all retrievers must define one.
- **Proportional Top-K allocation**: When topk is specified, results are allocated proportionally
  according to weights, with dynamic reallocation if some retrievers return fewer results than expected.
- **Automatic weight normalization**: Weights are normalized internally to ensure stable proportional behavior.

This retriever is suitable for scenarios where fine-grained control over the contribution of
different retrieval strategies (e.g., BM25, vector search, rule-based retrieval) is required.
"""
    def _further_check(self, retrievers: List[Retriever]):
        if any(getattr(r, 'priority', None) for r in retrievers):
            raise RuntimeError('priority is not allowed in `WeightedRetriever`.')
        if all(getattr(r, 'weight', None) for r in retrievers):
            self._valid = True
        elif any(getattr(r, 'weight', None) for r in retrievers):
            raise RuntimeError('All retrievers must define a "weight" attribute if any retriever defines one.')

    @property
    def weights(self): return self._get_cached_value('weight')

    @staticmethod
    def _normalize(weights: List[float]):
        sum_weight = sum(weights, 0) + 1e-8
        return [w / sum_weight for w in weights]

    def _combine(self, result: List[List[DocNode]], weights: List[float], topk: Optional[int]):
        if not topk: return result

        current, remain = result, topk
        final = []
        while (current and remain):
            cur, cur_weight, taken = [], [], 0
            weights = self._normalize(weights)
            for r, w in zip(current, weights):
                if len(r) <= int(w * remain):
                    final.append(r)
                    taken += len(r)
                else:
                    cur.append(r)
                    cur_weight.append(w)
            if len(cur) == len(current):
                ideal, frac = zip(*[[int(w * remain), w * remain - int(w * remain)] for w in weights])
                remain -= sum(ideal, 0)
                if remain:
                    current, ideal = zip(*[(x, y) for _, x, y in sorted(zip(frac, current, ideal), key=lambda t: t[0])])
                    ideal = list(ideal)
                    for i in range(len(ideal)):
                        if not remain: break
                        ideal[i] += 1
                        remain -= 1
                final.extend([current[i][:k] for i, k in enumerate(ideal)])
                break
            remain -= taken
            current, weights = cur, cur_weight
        return sum(final, [])

    @staticmethod
    def _real_params_checkf(x): return isinstance(x, (int, float))

    def forward(self, query: str, filters: Optional[Dict[str, Union[str, int, List, Set]]] = None,
                *, weights: Optional[List[float]] = None, topk: Optional[int] = None,
                combine: Optional[Callable[[List, List, int], List]] = None,
                search_kwargs: Optional[Dict[str, Any]] = None):
        """
Execute weighted retrieval and combine results from multiple Retrievers.

This method:
- Applies provided or predefined weights to each Retriever;
- Filters out retrievers with near-zero weights to reduce unnecessary retrieval cost;
- Allocates Top-K slots proportionally based on weights, with dynamic redistribution
  when some retrievers return fewer results than expected;
- Allows a custom combine function to override the default merging logic.

Args:
    query (str): User query string.
    filters (dict, optional): Retrieval filter conditions.
    weights (List[float], optional): Weight list corresponding to each Retriever.
    topk (int, optional): Maximum number of results to return.
    combine (Callable, optional): Custom result combination function.
"""
        weights = self._get_real_params(weights, 'weights', '(int, float)')
        weights = self._normalize(weights)
        indices, weights = zip(*[(i, w) for i, w in enumerate(weights) if w > 1e-5])
        rs = self._retrievers(query, filters, _kept_items=indices, **(search_kwargs or {}))
        return self._post_process((self._combine or combine)(rs, weights, topk or self._topk))


class PriorityRetriever(_CompositeRetrieverBase):
    """
PriorityRetriever combines multiple Retrievers based on predefined priority levels.

Design principles:
- **Weights are not allowed**: Sub-retrievers must not define a weight attribute.
- **Priority-ordered merging**: Results are merged in the order of
  high → normal → low priority.
- **Ignore support**: Retrievers marked with the ignore priority are skipped during preprocessing.
- **Top-K cutoff**: Merging stops as soon as the accumulated result size reaches topk.

This retriever is suitable for scenarios where strict ordering is required and
high-priority retrieval results must be returned before others, such as
rule-based retrieval taking precedence over semantic retrieval.
"""
    def _further_check(self, retrievers: List[Retriever]):
        if any(getattr(r, 'weight', None) for r in retrievers):
            raise RuntimeError('weight is not allowed in `PriorityRetriever`.')
        self._valid = True

    def _combine(self, result: List[List[DocNode]], priorities: List[Retriever.Priority], topk: Optional[int]):
        if not topk: final = result
        final = []
        for expected in (Retriever.Priority.high, Retriever.Priority.normal, Retriever.Priority.low):
            final.extend([r for r, p in zip(result, priorities) if p == expected])
            if sum([len(r) for r in final], 0) >= topk: break
        return sum(final, [])

    @property
    def priorities(self):
        return self._get_cached_value('priority', Retriever.Priority.normal)

    @staticmethod
    def _real_params_checkf(x):
        return x in list(Retriever.Priority)

    def forward(self, query: str, filters: Optional[Dict[str, Union[str, int, List, Set]]] = None,
                *, priorities: Optional[List[Retriever.Priority]] = None, topk: Optional[int] = None,
                combinef: Optional[Callable[[List, List, int], List]] = None,
                search_kwargs: Optional[Dict[str, Any]] = None):
        """
Execute priority-based retrieval and merge results from multiple Retrievers.

This method:
- Uses provided priorities or those defined on each Retriever;
- Skips retrievers with the ignore priority during preprocessing;
- Merges results in the order of high → normal → low priority;
- Stops merging as soon as the accumulated results reach topk.

Args:
    query (str): User query string.
    filters (dict, optional): Retrieval filter conditions.
    priorities (List[Retriever.Priority], optional): Priority list for each Retriever.
    topk (int, optional): Maximum number of results to return.
    combinef (Callable, optional): Custom priority-based combination function.
"""
        priorities = self._get_real_params(priorities, 'priorities', list(Retriever.Priority))
        # Top-k is not used during the preprocessing stage.
        indices, priorities = zip(*[(i, p) for i, p in enumerate(priorities) if p != Retriever.Priority.ignore])
        rs = self._retrievers(query, filters, _kept_items=indices, **(search_kwargs or {}))
        return self._post_process((combinef or self._combine)(rs, priorities, topk or self._topk))
