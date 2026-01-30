import lazyllm
from lazyllm.components.utils.downloader.model_downloader import LLMType
from typing import Any, Dict, Optional
from .map_model_type import get_model_type
from .base import OnlineChatModuleBase
from .base.utils import select_source_with_default_key


class _ChatModuleMeta(type):

    def __instancecheck__(self, __instance: Any) -> bool:
        if isinstance(__instance, OnlineChatModuleBase):
            return True
        return super().__instancecheck__(__instance)


class OnlineChatModule(metaclass=_ChatModuleMeta):
    """Used to manage and create access modules for large model platforms currently available on the market. Currently, it supports openai, sensenova, glm, kimi, qwen, doubao, ppio and deepseek (since the platform does not allow recharges for the time being, access is not supported for the time being). For how to obtain the platform's API key, please visit [Getting Started](/#platform)

Args:
    model (str): Specify the model to access (Note that you need to use Model ID or Endpoint ID when using Doubao. For details on how to obtain it, see [Getting the Inference Access Point](https://www.volcengine.com/docs/82379/1099522). Before using the model, you must first activate the corresponding service on the Doubao platform.), default is ``gpt-3.5-turbo(openai)`` / ``SenseChat-5(sensenova)`` / ``glm-4(glm)`` / ``moonshot-v1-8k(kimi)`` / ``qwen-plus(qwen)`` / ``mistral-7b-instruct-v0.2(doubao)`` / ``deepseek/deepseek-v3.2(ppio)`` .
    source (str): Specify the type of module to create. Options include  ``openai`` /  ``sensenova`` /  ``glm`` /  ``kimi`` /  ``qwen`` / ``doubao`` / ``ppio`` / ``deepseek (not yet supported)`` .
    base_url (str): Specify the base link of the platform to be accessed. The default is the official link.
    system_prompt (str): Specify the requested system prompt. The default is the official system prompt.
    stream (bool): Whether to request and output in streaming mode, default is streaming.
    return_trace (bool): Whether to record the results in trace, default is False.      


Examples:
    >>> import lazyllm
    >>> from functools import partial
    >>> m = lazyllm.OnlineChatModule(source="sensenova", stream=True)
    >>> query = "Hello!"
    >>> with lazyllm.ThreadPoolExecutor(1) as executor:
    ...     future = executor.submit(partial(m, llm_chat_history=[]), query)
    ...     while True:
    ...         if value := lazyllm.FileSystemQueue().dequeue():
    ...             print(f"output: {''.join(value)}")
    ...         elif future.done():
    ...             break
    ...     print(f"ret: {future.result()}")
    ...
    output: Hello
    output: ! How can I assist you today?
    ret: Hello! How can I assist you today?
    >>> from lazyllm.components.formatter import encode_query_with_filepaths
    >>> vlm = lazyllm.OnlineChatModule(source="sensenova", model="SenseChat-Vision")
    >>> query = "what is it?"
    >>> inputs = encode_query_with_filepaths(query, ["/path/to/your/image"])
    >>> print(vlm(inputs))
    """

    @staticmethod
    def _encapsulate_parameters(base_url: str, model: str, stream: bool, return_trace: bool, **kwargs) -> Dict[str, Any]:
        params = {'stream': stream, 'return_trace': return_trace}
        if base_url is not None:
            params['base_url'] = base_url
        if model is not None:
            params['model'] = model
        params.update(kwargs)
        return params

    def __new__(self, model: str = None, source: str = None, base_url: str = None, stream: bool = True,
                return_trace: bool = False, skip_auth: bool = False, type: Optional[str] = None,
                api_key: str = None, **kwargs):
        if model in lazyllm.online.chat and source is None: source, model = model, source
        if source is None and api_key is not None:
            raise ValueError('No source is given but an api_key is provided.')
        source, default_key = select_source_with_default_key(lazyllm.online.chat,
                                                             explicit_source=source,
                                                             type=LLMType.CHAT)
        if default_key and not api_key:
            api_key = default_key

        if type is None and model:
            type = get_model_type(model)
        if type in ['embed', 'rerank', 'cross_modal_embed']:
            raise AssertionError(f'\'{model}\' should use OnlineEmbeddingModule')
        elif type in ['stt', 'tts', 'sd']:
            raise AssertionError(f'\'{model}\' should use OnlineMultiModalModule')
        params = OnlineChatModule._encapsulate_parameters(base_url, model, stream, return_trace, api_key=api_key,
                                                          skip_auth=skip_auth, type=type.upper() if type else None,
                                                          **kwargs)
        if skip_auth:
            source = source or 'openai'
            if not base_url:
                raise KeyError('base_url must be set for local serving.')

        return getattr(lazyllm.online.chat, source)(**params)
