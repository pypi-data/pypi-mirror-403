import requests
import lazyllm
from typing import Tuple, List, Dict, Union
from ..base import (
    OnlineChatModuleBase, LazyLLMOnlineEmbedModuleBase,
    LazyLLMOnlineRerankModuleBase, LazyLLMOnlineText2ImageModuleBase
)
from lazyllm.components.formatter import encode_query_with_filepaths
from lazyllm.components.utils.file_operate import bytes_to_file
from ..fileHandler import FileHandlerBase

TIMEOUT = 300

class AipingChat(OnlineChatModuleBase, FileHandlerBase):
    """AipingChat is an online chat module for AIPing, inheriting from OnlineChatModuleBase and FileHandlerBase.

Provides an interface to interact with AIPing's large language models, supporting chat generation, file handling, and model fine-tuning. Supports multiple models including Vision-Language Models (VLM) such as Qwen2.5-VL, Qwen3-VL, GLM-4.5V, GLM-4.6V, etc.

Args:
    base_url (str): Base URL for the API, defaults to "https://aiping.cn/api/v1/".
    model (str): Name of the model to use, defaults to "DeepSeek-R1".
    api_key (Optional[str]): API key for accessing AIPing service. If not provided, it is read from lazyllm config.
    stream (bool): Whether to enable streaming output, defaults to True.
    return_trace (bool): Whether to return debug trace information, defaults to False.
    **kwargs: Additional parameters passed to OnlineChatModuleBase.

Features:
    1. Supports multiple large language models, including general chat models and vision-language models
    2. Supports streaming output for better user experience
    3. Integrated file handling functionality, supporting fine-tuning data format validation and conversion
    4. Built-in system prompt: "You are an intelligent assistant developed by AIPing. You are a helpful assistant."
    5. Supports API key validation to ensure service security
"""
    VLM_MODEL_PREFIX = [
        'Qwen2.5-VL-',
        'Qwen3-VL-',
        'GLM-4.5V',
        'GLM-4.6V'
    ]

    def __init__(self, base_url: str = 'https://aiping.cn/api/v1/', model: str = 'DeepSeek-R1',
                 api_key: str = None, stream: bool = True, return_trace: bool = False, **kwargs):
        super().__init__(api_key=api_key or lazyllm.config['aiping_api_key'], base_url=base_url, model_name=model,
                         stream=stream, return_trace=return_trace, **kwargs)
        FileHandlerBase.__init__(self)
        if stream:
            self._model_optional_params['stream'] = True

    def _get_system_prompt(self):
        return 'You are an intelligent assistant developed by AIPing. You are a helpful assistant.'

    def _validate_api_key(self):
        try:
            data = {
                'model': self._model_name,
                'messages': [{'role': 'user', 'content': 'hi'}],
                'max_tokens': 1
            }
            response = requests.post(self._chat_url, headers=self._header, json=data, timeout=TIMEOUT)
            return response.status_code == 200
        except Exception:
            return False


class AipingEmbed(LazyLLMOnlineEmbedModuleBase):
    """Aiping text embedding module, inheriting from OnlineEmbeddingModuleBase.

Provides an interface to interact with AIPing's text embedding service, supporting conversion of text to vector representations with batch processing support.

Args:
    embed_url (str): Embedding API URL, defaults to "https://aiping.cn/api/v1/embeddings".
    embed_model_name (str): Name of the embedding model to use, defaults to "text-embedding-v1".
    api_key (Optional[str]): API key for accessing AIPing service. If not provided, it is read from lazyllm config.
    batch_size (int): Batch size for processing, defaults to 16.
    **kw: Additional parameters passed to the base class.

Features:
    1. Converts text to high-dimensional vector representations
    2. Supports batch text processing for improved efficiency
    3. Configurable batch size to accommodate different performance requirements
    4. Seamless integration with AIPing API
"""
    def __init__(self, embed_url: str = 'https://aiping.cn/api/v1/embeddings',
                 embed_model_name: str = 'text-embedding-v1', api_key: str = None,
                 batch_size: int = 16, **kw):
        super().__init__(embed_url, api_key or lazyllm.config['aiping_api_key'],
                         embed_model_name, batch_size=batch_size, **kw)


class AipingRerank(LazyLLMOnlineRerankModuleBase):
    """Aiping reranking module, inheriting from OnlineEmbeddingModuleBase.

Provides an interface to interact with AIPing's reranking service, used for reordering a list of documents based on their relevance to a given query. Returns a list of tuples containing document index and relevance score.

Args:
    embed_url (str): Reranking API URL, defaults to "https://aiping.cn/api/v1/rerank".
    embed_model_name (str): Name of the reranking model to use, defaults to "Qwen3-Reranker-0.6B".
    api_key (Optional[str]): API key for accessing AIPing service. If not provided, it is read from lazyllm config.
    **kw: Additional parameters passed to the base class.

Properties:
    type (str): Returns model type, fixed as "RERANK".

Features:
    1. Reranks documents based on query relevance
    2. Supports custom ranking parameters (e.g., top_n)
    3. Returns index and relevance score for each document
    4. Suitable for search result optimization and document recommendation scenarios
"""
    def __init__(self, embed_url: str = 'https://aiping.cn/api/v1/rerank',
                 embed_model_name: str = 'Qwen3-Reranker-0.6B', api_key: str = None, **kw):
        super().__init__(embed_url, api_key or lazyllm.config['aiping_api_key'],
                         embed_model_name, **kw)

    @property
    def type(self):
        return 'RERANK'

    def _encapsulated_data(self, query: str, documents: List[str], top_n: int, **kwargs) -> Dict[str, str]:
        json_data = {
            'model': self._embed_model_name,
            'query': query,
            'documents': documents,
            'top_n': top_n
        }
        if len(kwargs) > 0:
            json_data.update(kwargs)

        return json_data

    def _parse_response(self, response: Dict, input: Union[List, str]) -> List[Tuple]:
        results = response.get('results', [])
        if not results:
            return []
        return [(result['index'], result['relevance_score']) for result in results]


class AipingText2Image(LazyLLMOnlineText2ImageModuleBase):
    """Aiping text-to-image module, inheriting from OnlineMultiModalBase.

Provides an interface to interact with AIPing's image generation service, supporting image generation from text descriptions. Supports parameters such as negative prompts, image count, size, and random seeds.

Args:
    api_key (Optional[str]): API key for accessing AIPing service. If not provided, it is read from lazyllm config.
    model_name (str): Name of the model to use, defaults to "Qwen-Image".
    base_url (str): Base URL for the API, defaults to "https://aiping.cn/api/v1/".
    return_trace (bool): Whether to return debug trace information, defaults to False.
    **kwargs: Additional parameters passed to the base class.

Features:
    1. Generates high-quality images from text prompts
    2. Supports negative prompts to filter unwanted image features
    3. Configurable number of images to generate (n parameter)
    4. Supports multiple image size specifications
    5. Supports random seed control for reproducible results
    6. Automatically downloads generated images and encodes them as files
    7. Default negative prompt: "模糊，低质量"

Note:
    - This module automatically downloads generated images to local files
    - The returned result contains file path information for easy subsequent processing
"""
    def __init__(self, api_key: str = None, model_name: str = 'Qwen-Image',
                 base_url: str = 'https://aiping.cn/api/v1/',
                 return_trace: bool = False, **kwargs):
        super().__init__(model_name=model_name, api_key=api_key or lazyllm.config['aiping_api_key'],
                         return_trace=return_trace, **kwargs)
        self._endpoint = 'images/generations'
        self._base_url = base_url

    def _make_request(self, endpoint, payload, timeout=TIMEOUT):
        headers = {
            'Authorization': f'Bearer {self._api_key}',
            'Content-Type': 'application/json'
        }

        url = f'{self._base_url}{endpoint}'

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            lazyllm.LOG.error(f'Request failed: {e}')
            raise

    def _forward(self, input: str = None, negative_prompt: str = None, n: int = None,
                 size: str = None, seed: int = None, **kwargs):
        if not input:
            raise ValueError('Prompt is required')

        input_params = {
            'prompt': input,
            'negative_prompt': negative_prompt or '模糊，低质量'
        }

        extra_body = {}

        if n is not None:
            extra_body['n'] = n

        if size is not None:
            extra_body['size'] = size

        if seed is not None:
            extra_body['seed'] = seed

        payload = {
            'model': self._model_name,
            'input': input_params
        }

        if extra_body:
            payload['extra_body'] = extra_body

        try:
            result = self._make_request(self._endpoint, payload)

            images = result.get('data')
            if not images or not isinstance(images, list) or not images:
                raise ValueError(f'Unexpected response format: {result}')

            image_urls = [img.get('url') for img in images if img.get('url')]
            if not image_urls:
                raise ValueError(f'No image URLs found in response: {result}')

            return encode_query_with_filepaths(None, bytes_to_file([requests.get(url).content for url in image_urls]))

        except Exception as e:
            lazyllm.LOG.error(f'Failed to generate image: {e}')
            raise Exception(f'Failed to generate image: {str(e)}')
