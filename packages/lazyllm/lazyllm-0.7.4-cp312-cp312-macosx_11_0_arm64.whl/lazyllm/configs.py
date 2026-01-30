import os
from enum import Enum
import json
import threading
from typing import List, Union, Optional
from contextlib import contextmanager
from contextvars import ContextVar
from asyncio import events
import lazyllm


class Mode(Enum):
    """An enumeration."""
    Display = 0,
    Normal = 1,
    Debug = 2,


class _ConfigMeta(type):
    """<property object at 0x7fb328336750>"""
    _registered_cfgs = dict()
    _env_name_map = dict()
    _homes = dict()
    _doc = ''
    _instances = dict()
    _lock = threading.RLock()

    def __call__(cls, prefix: str = 'LAZYLLM', *args, **kwargs):
        if prefix.lower() not in cls._instances:
            with cls._lock:
                if prefix.lower() not in cls._instances:
                    cls._instances[prefix.lower()] = super().__call__(prefix, *args, **kwargs)
        return cls._instances[prefix.lower()]

    @staticmethod
    def _get_description(name):
        desc = _ConfigMeta._registered_cfgs[name]
        if not desc: raise ValueError(f'Description for {name} is not found')
        doc = (f'  - Description: {desc["description"]}, type: `{desc["type"].__name__}`, '
               'default: `{desc["default"]}`<br>\n')
        if (options := desc.get('options')):
            doc += f'  - Options: {", ".join(options)}<br>\n'
        if (env := desc.get('env')):
            if isinstance(env, str):
                doc += f'  - Environment Variable: {("LAZYLLM_" + env).upper()}<br>\n'
            elif isinstance(env, dict):
                doc += '  - Environment Variable:<br>\n'
                for k, v in env.items():
                    doc += f'{("    - LAZYLLM_" + k).upper()}: {v}<br>\n'
        return doc

    @staticmethod
    def add(name: str, type: type, default: Optional[Union[int, str, bool]] = None, env: Union[str, dict] = None,
            *, options: Optional[List] = None, description: Optional[str] = None):
        update_params = dict(type=type, default=default, env=env, options=options, description=description)
        if name not in _ConfigMeta._registered_cfgs or _ConfigMeta._registered_cfgs[name] != update_params:
            _ConfigMeta._registered_cfgs[name] = update_params
            if not env: env = name.lower()
            for k in ([env] if isinstance(env, str) else env.keys() if isinstance(env, dict) else env):
                _ConfigMeta._env_name_map[k.lower()] = name
        for v in _ConfigMeta._instances.values():
            v._update_impl(name, type, default, env)

    def _get_default_home(prefix):
        return _ConfigMeta._homes[prefix]

    @property
    def __doc__(self):
        doc = f'{self._doc}\n**LazyLLM Configurations:**\n\n'
        return doc + '<br>\n'.join([f'- **{name}**:<br>\n{self._get_description(name)}'
                                    for name in self._registered_cfgs.keys()])

    @__doc__.setter
    def __doc__(self, value):
        self._doc = value

    def __contains__(self, key):
        return key.lower() in self._instances or '_' in key and key.split('_')[0].lower() in self._instances


_ConfigMeta.add('home', str, None, 'HOME', description='The default home directory for LazyLLM.')

class Config(metaclass=_ConfigMeta):
    """Config is a configuration class provided by LazyLLM, which loads configurations of LazyLLM framework from config files,
environment variables, or specify them explicitly. it can export all configuration items as well.
The Config module automatically generates an object named 'config' containing all configurations.

Args:
    prefix (str, optional): Environment variable prefix. Defaults to 'LAZYLLM'
    home (str, optional): Configuration file directory path. Defaults to '~/.lazyllm'

**LazyLLM Configurations:**

- **home**:<br>
  - Description: The default home directory for LazyLLM., type: `str`, default: `{desc["default"]}`<br>
  - Environment Variable: LAZYLLM_HOME<br>
<br>
- **mode**:<br>
  - Description: The default mode for LazyLLM., type: `Mode`, default: `{desc["default"]}`<br>
  - Environment Variable:<br>
    - LAZYLLM_DISPLAY: Mode.Display<br>
    - LAZYLLM_DEBUG: Mode.Debug<br>
<br>
- **repr_ml**:<br>
  - Description: Whether to use Markup Language for repr., type: `bool`, default: `{desc["default"]}`<br>
  - Environment Variable: LAZYLLM_REPR_USE_ML<br>
<br>
- **repr_show_child**:<br>
  - Description: Whether to show child modules in repr., type: `bool`, default: `{desc["default"]}`<br>
  - Environment Variable: LAZYLLM_REPR_SHOW_CHILD<br>
<br>
- **rag_store**:<br>
  - Description: The default store for RAG., type: `str`, default: `{desc["default"]}`<br>
  - Environment Variable: LAZYLLM_RAG_STORE<br>
<br>
- **gpu_type**:<br>
  - Description: The default GPU type for LazyLLM., type: `str`, default: `{desc["default"]}`<br>
  - Environment Variable: LAZYLLM_GPU_TYPE<br>
<br>
- **train_target_root**:<br>
  - Description: The default target root for training., type: `str`, default: `{desc["default"]}`<br>
  - Environment Variable: LAZYLLM_TRAIN_TARGET_ROOT<br>
<br>
- **infer_log_root**:<br>
  - Description: The default log root for inference., type: `str`, default: `{desc["default"]}`<br>
  - Environment Variable: LAZYLLM_INFER_LOG_ROOT<br>
<br>
- **temp_dir**:<br>
  - Description: The default temp directory for LazyLLM., type: `str`, default: `{desc["default"]}`<br>
  - Environment Variable: LAZYLLM_TEMP_DIR<br>
<br>
- **thread_pool_worker_num**:<br>
  - Description: The default number of workers for thread pool., type: `int`, default: `{desc["default"]}`<br>
  - Environment Variable: LAZYLLM_THREAD_POOL_WORKER_NUM<br>
<br>
- **deploy_skip_check_kw**:<br>
  - Description: Whether to skip check keywords for deployment., type: `bool`, default: `{desc["default"]}`<br>
  - Environment Variable: LAZYLLM_DEPLOY_SKIP_CHECK_KW<br>
<br>
- **allow_internal_network**:<br>
  - Description: Whether to allow loading images from internal network addresses. Set to False for security in production environments., type: `bool`, default: `{desc["default"]}`<br>
  - Environment Variable: LAZYLLM_ALLOW_INTERNAL_NETWORK<br>
<br>
- **redis_url**:<br>
  - Description: The URL of the Redis server., type: `str`, default: `{desc["default"]}`<br>
  - Environment Variable: LAZYLLM_REDIS_URL<br>
<br>
- **redis_recheck_delay**:<br>
  - Description: The delay of the Redis server check., type: `int`, default: `{desc["default"]}`<br>
  - Environment Variable: LAZYLLM_REDIS_RECHECK_DELAY<br>
<br>
- **use_builtin**:<br>
  - Description: Whether to use registry modules in python builtin., type: `bool`, default: `{desc["default"]}`<br>
  - Environment Variable: LAZYLLM_USE_BUILTIN<br>
<br>
- **default_fsqueue**:<br>
  - Description: The default file system queue to use., type: `str`, default: `{desc["default"]}`<br>
  - Environment Variable: LAZYLLM_DEFAULT_FSQUEUE<br>
<br>
- **fsqredis_url**:<br>
  - Description: The URL of the Redis server for the file system queue., type: `str`, default: `{desc["default"]}`<br>
  - Environment Variable: LAZYLLM_FSQREDIS_URL<br>
<br>
- **default_recent_k**:<br>
  - Description: The number of recent inputs that RecentQueue keeps track of., type: `int`, default: `{desc["default"]}`<br>
  - Environment Variable: LAZYLLM_DEFAULT_RECENT_K<br>
<br>
- **save_flow_result**:<br>
  - Description: Whether to save the intermediate result of the pipeline., type: `bool`, default: `{desc["default"]}`<br>
  - Environment Variable: LAZYLLM_SAVE_FLOW_RESULT<br>
<br>
- **parallel_multiprocessing**:<br>
  - Description: Whether to use multiprocessing for parallel execution, if not, default to use threading., type: `bool`, default: `{desc["default"]}`<br>
  - Environment Variable: LAZYLLM_PARALLEL_MULTIPROCESSING<br>
<br>
- **launcher**:<br>
  - Description: The default remote launcher to use if no launcher is specified., type: `str`, default: `{desc["default"]}`<br>
  - Environment Variable: LAZYLLM_DEFAULT_LAUNCHER<br>
<br>
- **cuda_visible**:<br>
  - Description: Whether to set the CUDA_VISIBLE_DEVICES environment variable., type: `bool`, default: `{desc["default"]}`<br>
  - Environment Variable: LAZYLLM_CUDA_VISIBLE<br>
<br>
- **partition**:<br>
  - Description: The default slurm partition to use if no partition is specified., type: `str`, default: `{desc["default"]}`<br>
  - Environment Variable: LAZYLLM_SLURM_PART<br>
<br>
- **sco.workspace**:<br>
  - Description: The default SCO workspace to use if no workspace is specified., type: `str`, default: `{desc["default"]}`<br>
  - Environment Variable: LAZYLLM_SCO_WORKSPACE<br>
<br>
- **sco_env_name**:<br>
  - Description: The default SCO environment name to use if no environment name is specified., type: `str`, default: `{desc["default"]}`<br>
  - Environment Variable: LAZYLLM_SCO_ENV_NAME<br>
<br>
- **sco_keep_record**:<br>
  - Description: Whether to keep the record of the Sensecore job., type: `bool`, default: `{desc["default"]}`<br>
  - Environment Variable: LAZYLLM_SCO_KEEP_RECORD<br>
<br>
- **sco_resource_type**:<br>
  - Description: The default SCO resource type to use if no resource type is specified., type: `str`, default: `{desc["default"]}`<br>
  - Environment Variable: LAZYLLM_SCO_RESOURCE_TYPE<br>
<br>
- **k8s_env_name**:<br>
  - Description: The default k8s environment name to use if no environment name is specified., type: `str`, default: `{desc["default"]}`<br>
  - Environment Variable: LAZYLLM_K8S_ENV_NAME<br>
<br>
- **k8s_config_path**:<br>
  - Description: The default k8s configuration path to use if no configuration path is specified., type: `str`, default: `{desc["default"]}`<br>
  - Environment Variable: LAZYLLM_K8S_CONFIG_PATH<br>
<br>
- **k8s_device_type**:<br>
  - Description: The default k8s device type to use if no device type is specified., type: `str`, default: `{desc["default"]}`<br>
  - Environment Variable: LAZYLLM_K8S_DEVICE_TYPE<br>
<br>
- **model_source**:<br>
  - Description: The default model source to use., type: `str`, default: `{desc["default"]}`<br>
  - Environment Variable: LAZYLLM_MODEL_SOURCE<br>
<br>
- **model_cache_dir**:<br>
  - Description: The default model cache directory to use(Read and Write)., type: `str`, default: `{desc["default"]}`<br>
  - Environment Variable: LAZYLLM_MODEL_CACHE_DIR<br>
<br>
- **model_path**:<br>
  - Description: The default model path to use(ReadOnly)., type: `str`, default: `{desc["default"]}`<br>
  - Environment Variable: LAZYLLM_MODEL_PATH<br>
<br>
- **model_source_token**:<br>
  - Description: The default token for configed model source(hf or ms) to use., type: `str`, default: `{desc["default"]}`<br>
  - Environment Variable: LAZYLLM_MODEL_SOURCE_TOKEN<br>
<br>
- **data_path**:<br>
  - Description: The default data path to use., type: `str`, default: `{desc["default"]}`<br>
  - Environment Variable: LAZYLLM_DATA_PATH<br>
<br>
- **openai_api**:<br>
  - Description: Whether to use OpenAI API for vllm deployer., type: `bool`, default: `{desc["default"]}`<br>
  - Environment Variable: LAZYLLM_OPENAI_API<br>
<br>
- **use_ray**:<br>
  - Description: Whether to use Ray for ServerModule(relay server)., type: `bool`, default: `{desc["default"]}`<br>
  - Environment Variable: LAZYLLM_USE_RAY<br>
<br>
- **num_gpus_per_node**:<br>
  - Description: The number of GPUs per node for Ray launcher when deploy models., type: `int`, default: `{desc["default"]}`<br>
  - Environment Variable: LAZYLLM_NUM_GPUS_PER_NODE<br>
<br>
- **lmdeploy_eager_mode**:<br>
  - Description: Whether to use eager mode for lmdeploy., type: `bool`, default: `{desc["default"]}`<br>
  - Environment Variable: LAZYLLM_LMDEPLOY_EAGER_MODE<br>
<br>
- **default_embedding_engine**:<br>
  - Description: The default embedding engine to use., type: `str`, default: `{desc["default"]}`<br>
  - Environment Variable: LAZYLLM_DEFAULT_EMBEDDING_ENGINE<br>
<br>
- **mindie_home**:<br>
  - Description: The home directory of MindIE., type: `str`, default: `{desc["default"]}`<br>
  - Environment Variable: LAZYLLM_MINDIE_HOME<br>
<br>
- **gpu_memory**:<br>
  - Description: The memory of the GPU., type: `int`, default: `{desc["default"]}`<br>
  - Environment Variable: LAZYLLM_GPU_MEMORY<br>
<br>
- **cache_dir**:<br>
  - Description: The default result cache directory for module to use(Read and Write)., type: `str`, default: `{desc["default"]}`<br>
  - Environment Variable: LAZYLLM_CACHE_DIR<br>
<br>
- **cache_strategy**:<br>
  - Description: The default cache strategy to use(memory, file, sqlite, redis)., type: `str`, default: `{desc["default"]}`<br>
  - Environment Variable: LAZYLLM_CACHE_STRATEGY<br>
<br>
- **cache_mode**:<br>
  - Description: The default cache mode to use(Read and Write, Read Only, Write Only, None)., type: `str`, default: `{desc["default"]}`<br>
  - Options: RW, RO, WO, NONE<br>
  - Environment Variable: LAZYLLM_CACHE_MODE<br>
<br>
- **cache_online_module**:<br>
  - Description: Whether to cache the online module result. Use for unit test., type: `bool`, default: `{desc["default"]}`<br>
  - Environment Variable: LAZYLLM_CACHE_ONLINE_MODULE<br>
<br>
- **aiping_api_key**:<br>
  - Description: The API key for aiping, type: `str`, default: `{desc["default"]}`<br>
  - Environment Variable: LAZYLLM_AIPING_API_KEY<br>
<br>
- **aiping_model_name**:<br>
  - Description: The default model name for aiping, type: `str`, default: `{desc["default"]}`<br>
  - Environment Variable: LAZYLLM_AIPING_MODEL_NAME<br>
<br>
- **aiping_text2image_model_name**:<br>
  - Description: The default text2image model name for aiping, type: `str`, default: `{desc["default"]}`<br>
  - Environment Variable: LAZYLLM_AIPING_TEXT2IMAGE_MODEL_NAME<br>
<br>
- **deepseek_api_key**:<br>
  - Description: The API key for deepseek, type: `str`, default: `{desc["default"]}`<br>
  - Environment Variable: LAZYLLM_DEEPSEEK_API_KEY<br>
<br>
- **deepseek_model_name**:<br>
  - Description: The default model name for deepseek, type: `str`, default: `{desc["default"]}`<br>
  - Environment Variable: LAZYLLM_DEEPSEEK_MODEL_NAME<br>
<br>
- **doubao_api_key**:<br>
  - Description: The API key for doubao, type: `str`, default: `{desc["default"]}`<br>
  - Environment Variable: LAZYLLM_DOUBAO_API_KEY<br>
<br>
- **doubao_model_name**:<br>
  - Description: The default model name for doubao, type: `str`, default: `{desc["default"]}`<br>
  - Environment Variable: LAZYLLM_DOUBAO_MODEL_NAME<br>
<br>
- **doubao_text2image_model_name**:<br>
  - Description: The default text2image model name for doubao, type: `str`, default: `{desc["default"]}`<br>
  - Environment Variable: LAZYLLM_DOUBAO_TEXT2IMAGE_MODEL_NAME<br>
<br>
- **glm_api_key**:<br>
  - Description: The API key for glm, type: `str`, default: `{desc["default"]}`<br>
  - Environment Variable: LAZYLLM_GLM_API_KEY<br>
<br>
- **glm_model_name**:<br>
  - Description: The default model name for glm, type: `str`, default: `{desc["default"]}`<br>
  - Environment Variable: LAZYLLM_GLM_MODEL_NAME<br>
<br>
- **glm_stt_model_name**:<br>
  - Description: The default stt model name for glm, type: `str`, default: `{desc["default"]}`<br>
  - Environment Variable: LAZYLLM_GLM_STT_MODEL_NAME<br>
<br>
- **glm_text2image_model_name**:<br>
  - Description: The default text2image model name for glm, type: `str`, default: `{desc["default"]}`<br>
  - Environment Variable: LAZYLLM_GLM_TEXT2IMAGE_MODEL_NAME<br>
<br>
- **kimi_api_key**:<br>
  - Description: The API key for kimi, type: `str`, default: `{desc["default"]}`<br>
  - Environment Variable: LAZYLLM_KIMI_API_KEY<br>
<br>
- **kimi_model_name**:<br>
  - Description: The default model name for kimi, type: `str`, default: `{desc["default"]}`<br>
  - Environment Variable: LAZYLLM_KIMI_MODEL_NAME<br>
<br>
- **minimax_api_key**:<br>
  - Description: The API key for minimax, type: `str`, default: `{desc["default"]}`<br>
  - Environment Variable: LAZYLLM_MINIMAX_API_KEY<br>
<br>
- **minimax_model_name**:<br>
  - Description: The default model name for minimax, type: `str`, default: `{desc["default"]}`<br>
  - Environment Variable: LAZYLLM_MINIMAX_MODEL_NAME<br>
<br>
- **minimax_text2image_model_name**:<br>
  - Description: The default text2image model name for minimax, type: `str`, default: `{desc["default"]}`<br>
  - Environment Variable: LAZYLLM_MINIMAX_TEXT2IMAGE_MODEL_NAME<br>
<br>
- **minimax_tts_model_name**:<br>
  - Description: The default tts model name for minimax, type: `str`, default: `{desc["default"]}`<br>
  - Environment Variable: LAZYLLM_MINIMAX_TTS_MODEL_NAME<br>
<br>
- **openai_api_key**:<br>
  - Description: The API key for openai, type: `str`, default: `{desc["default"]}`<br>
  - Environment Variable: LAZYLLM_OPENAI_API_KEY<br>
<br>
- **openai_model_name**:<br>
  - Description: The default model name for openai, type: `str`, default: `{desc["default"]}`<br>
  - Environment Variable: LAZYLLM_OPENAI_MODEL_NAME<br>
<br>
- **ppio_api_key**:<br>
  - Description: The API key for ppio, type: `str`, default: `{desc["default"]}`<br>
  - Environment Variable: LAZYLLM_PPIO_API_KEY<br>
<br>
- **ppio_model_name**:<br>
  - Description: The default model name for ppio, type: `str`, default: `{desc["default"]}`<br>
  - Environment Variable: LAZYLLM_PPIO_MODEL_NAME<br>
<br>
- **qwen_api_key**:<br>
  - Description: The API key for qwen, type: `str`, default: `{desc["default"]}`<br>
  - Environment Variable: LAZYLLM_QWEN_API_KEY<br>
<br>
- **qwen_model_name**:<br>
  - Description: The default model name for qwen, type: `str`, default: `{desc["default"]}`<br>
  - Environment Variable: LAZYLLM_QWEN_MODEL_NAME<br>
<br>
- **qwen_stt_model_name**:<br>
  - Description: The default stt model name for qwen, type: `str`, default: `{desc["default"]}`<br>
  - Environment Variable: LAZYLLM_QWEN_STT_MODEL_NAME<br>
<br>
- **qwen_text2image_model_name**:<br>
  - Description: The default text2image model name for qwen, type: `str`, default: `{desc["default"]}`<br>
  - Environment Variable: LAZYLLM_QWEN_TEXT2IMAGE_MODEL_NAME<br>
<br>
- **qwen_tts_model_name**:<br>
  - Description: The default tts model name for qwen, type: `str`, default: `{desc["default"]}`<br>
  - Environment Variable: LAZYLLM_QWEN_TTS_MODEL_NAME<br>
<br>
- **sensenova_secret_key**:<br>
  - Description: The secret key for SenseNova., type: `str`, default: `{desc["default"]}`<br>
  - Environment Variable: LAZYLLM_SENSENOVA_SECRET_KEY<br>
<br>
- **sensenova_api_key**:<br>
  - Description: The API key for sensenova, type: `str`, default: `{desc["default"]}`<br>
  - Environment Variable: LAZYLLM_SENSENOVA_API_KEY<br>
<br>
- **sensenova_model_name**:<br>
  - Description: The default model name for sensenova, type: `str`, default: `{desc["default"]}`<br>
  - Environment Variable: LAZYLLM_SENSENOVA_MODEL_NAME<br>
<br>
- **siliconflow_api_key**:<br>
  - Description: The API key for siliconflow, type: `str`, default: `{desc["default"]}`<br>
  - Environment Variable: LAZYLLM_SILICONFLOW_API_KEY<br>
<br>
- **siliconflow_model_name**:<br>
  - Description: The default model name for siliconflow, type: `str`, default: `{desc["default"]}`<br>
  - Environment Variable: LAZYLLM_SILICONFLOW_MODEL_NAME<br>
<br>
- **siliconflow_text2image_model_name**:<br>
  - Description: The default text2image model name for siliconflow, type: `str`, default: `{desc["default"]}`<br>
  - Environment Variable: LAZYLLM_SILICONFLOW_TEXT2IMAGE_MODEL_NAME<br>
<br>
- **siliconflow_tts_model_name**:<br>
  - Description: The default tts model name for siliconflow, type: `str`, default: `{desc["default"]}`<br>
  - Environment Variable: LAZYLLM_SILICONFLOW_TTS_MODEL_NAME<br>
<br>
- **trainable_module_config_map_path**:<br>
  - Description: The default path for trainable module config map., type: `str`, default: `{desc["default"]}`<br>
  - Environment Variable: LAZYLLM_TRAINABLE_MODULE_CONFIG_MAP_PATH<br>
<br>
- **auto_model_config_map_path**:<br>
  - Description: The default path for automodel config map., type: `str`, default: `{desc["default"]}`<br>
  - Environment Variable: LAZYLLM_AUTO_MODEL_CONFIG_MAP_PATH<br>
<br>
- **trainable_magic_mock**:<br>
  - Description: Whether to use magic mock for trainable module(used for unit test)., type: `bool`, default: `{desc["default"]}`<br>
  - Environment Variable: LAZYLLM_TRAINABLE_MAGIC_MOCK<br>
<br>
- **cache_local_module**:<br>
  - Description: Whether to cache the local module result. Use for unit test., type: `bool`, default: `{desc["default"]}`<br>
  - Environment Variable: LAZYLLM_CACHE_LOCAL_MODULE<br>
<br>
- **raise_on_add_doc_error**:<br>
  - Description: Whether to raise an error when adding doc failed., type: `bool`, default: `{desc["default"]}`<br>
  - Environment Variable: LAZYLLM_RAISE_ON_ADD_DOC_ERROR<br>
<br>
- **language**:<br>
  - Description: The language of the documentation., type: `str`, default: `{desc["default"]}`<br>
  - Environment Variable: LAZYLLM_LANGUAGE<br>
<br>
- **init_doc**:<br>
  - Description: whether to init docs, type: `bool`, default: `{desc["default"]}`<br>
  - Environment Variable: LAZYLLM_INIT_DOC<br>
<br>
- **max_embedding_workers**:<br>
  - Description: The default number of workers for embedding in RAG., type: `int`, default: `{desc["default"]}`<br>
  - Environment Variable: LAZYLLM_MAX_EMBEDDING_WORKERS<br>
<br>
- **default_dlmanager**:<br>
  - Description: The default document list manager for RAG., type: `str`, default: `{desc["default"]}`<br>
  - Environment Variable: LAZYLLM_DEFAULT_DOCLIST_MANAGER<br>
<br>
- **auto_detect_encoding**:<br>
  - Description: Whether auto detecting txt encoding, type: `bool`, default: `{desc["default"]}`<br>
  - Environment Variable: LAZYLLM_AUTO_DETECT_ENCODING<br>
<br>
- **enable_chardet**:<br>
  - Description: Whether to use chardet when detect txt encoding, type: `bool`, default: `{desc["default"]}`<br>
  - Environment Variable: LAZYLLM_ENABLE_CHARDET<br>
<br>
- **use_encoding_cache**:<br>
  - Description: Whether use cahce to accelerate txt encoding, type: `bool`, default: `{desc["default"]}`<br>
  - Environment Variable: LAZYLLM_USE_ENCODING_CACHE<br>
<br>
- **paddleocr_api_key**:<br>
  - Description: The API key for PaddleOCR, type: `str`, default: `{desc["default"]}`<br>
  - Environment Variable: LAZYLLM_PADDLEOCR_API_KEY<br>
<br>
- **rag_filename_as_id**:<br>
  - Description: Whether to use filename as id for RAG., type: `bool`, default: `{desc["default"]}`<br>
  - Environment Variable: LAZYLLM_RAG_FILENAME_AS_ID<br>
<br>
- **use_fallback_reader**:<br>
  - Description: Whether to use fallback reader for RAG., type: `bool`, default: `{desc["default"]}`<br>
  - Environment Variable: LAZYLLM_USE_FALLBACK_READER<br>
<br>
- **eval_result_dir**:<br>
  - Description: The default result directory for eval., type: `str`, default: `{desc["default"]}`<br>
  - Environment Variable: LAZYLLM_EVAL_RESULT_DIR<br>
<br>
- **debug**:<br>
  - Description: Whether to enable debug mode., type: `bool`, default: `{desc["default"]}`<br>
  - Environment Variable: LAZYLLM_DEBUG<br>
<br>
- **log_name**:<br>
  - Description: The name of the log file., type: `str`, default: `{desc["default"]}`<br>
  - Environment Variable: LAZYLLM_LOG_NAME<br>
<br>
- **expected_log_modules**:<br>
  - Description: The expected log modules, separated by comma., type: `str`, default: `{desc["default"]}`<br>
  - Environment Variable: LAZYLLM_EXPECTED_LOG_MODULES<br>
<br>
- **log_level**:<br>
  - Description: The level of the log., type: `str`, default: `{desc["default"]}`<br>
  - Environment Variable: LAZYLLM_LOG_LEVEL<br>
<br>
- **log_format**:<br>
  - Description: The format of the log., type: `str`, default: `{desc["default"]}`<br>
  - Environment Variable: LAZYLLM_LOG_FORMAT<br>
<br>
- **log_dir**:<br>
  - Description: The directory of the log file., type: `str`, default: `{desc["default"]}`<br>
  - Environment Variable: LAZYLLM_LOG_DIR<br>
<br>
- **log_file_level**:<br>
  - Description: The level of the log file., type: `str`, default: `{desc["default"]}`<br>
  - Environment Variable: LAZYLLM_LOG_FILE_LEVEL<br>
<br>
- **log_file_size**:<br>
  - Description: The size of the log file., type: `str`, default: `{desc["default"]}`<br>
  - Environment Variable: LAZYLLM_LOG_FILE_SIZE<br>
<br>
- **log_file_retention**:<br>
  - Description: The retention of the log file., type: `str`, default: `{desc["default"]}`<br>
  - Environment Variable: LAZYLLM_LOG_FILE_RETENTION<br>
<br>
- **log_file_mode**:<br>
  - Description: The mode of the log file., type: `str`, default: `{desc["default"]}`<br>
  - Environment Variable: LAZYLLM_LOG_FILE_MODE<br>
"""
    def __init__(self, prefix: str = 'LAZYLLM', home: Optional[str] = None, config_file: str = 'config.json'):
        self._prefix = prefix.upper()
        self._impl, self._cfgs = dict(), dict()
        if not home:
            home = '.lazyllm' if self._prefix == 'LAZYLLM' else f'.lazyllm_{prefix.lower()}'
            home = os.path.join(os.path.expanduser('~'), home)
        _ConfigMeta._homes[self._prefix] = home
        self._update_impl('home', str, None, 'HOME')
        os.makedirs(self['home'], exist_ok=True)
        self._cgf_path = os.path.join(self['home'], config_file)
        if os.path.exists(self._cgf_path):
            with open(self._cgf_path, 'r+') as f:
                self._cfgs = Config.get_config(json.loads(f))
        for name, cfg in _ConfigMeta._registered_cfgs.items():
            if name == 'home': continue
            self._update_impl(name, cfg['type'], cfg['default'], cfg['env'])

    def add(self, name: str, type: type, default: Optional[Union[int, str, bool]] = None, env: Union[str, dict] = None,
            *, options: Optional[List] = None, description: Optional[str] = None):
        """Loads value into LazyLLM configuration item. The function first attempts to find the value with the given name from the
dict loaded from config.json. If found, it removes the key from the dict and saves the value to the config.
If 'env' is a string, the function calls getenv to look for the corresponding LazyLLM environment variable, and if
it's found, writes it to the config. If 'env' is a dictionary, the function attempts to call getenv to find the
environment variables corresponding to the keys in the dict and convert them to boolean type.
If the converted boolean value is True, the value corresponding to the current key in the dict is written to the config.

Args:
    name (str): The name of the configuration item
    type (type): The type of the configuration
    default (optional): The default value of the configuration if no value can be obtained
    env (optional): The name of the environment variable without the prefix, or a dictionary where the keys are the
    names of the environment variables(without the prefix), and the values are what to be added to the configuration.
"""
        if (name := name.lower()) in Config.__dict__.keys():
            raise RuntimeError(f'{name} is attribute of Config, please change it!')
        _ConfigMeta.add(name, type, default, env, options=options, description=description)

    def getenv(self, name, type, default=None):
        """Get value of LazyLLM-related environment variables.

Args:
    name (str): The name of the environment variable （without the prefix）, case-insensitive. The function obtains value
    from environment variable by concatenating the prefix and this name, with all uppercase letters.
    type (type): Specifies the type of the configuration, for example, str. For boolean types, the function will
    convert inputs ‘TRUE’, ‘True’, 1, ‘ON’, and ‘1’ to True.
    default (optional): If the value of the environment variable cannot be obtained, this value is returned.
"""
        r = os.getenv(f'{self._prefix}_{name.upper()}', default)
        if type == bool:
            return r in (True, 'TRUE', 'True', 1, 'ON', '1')
        return type(r) if r is not None else r

    @staticmethod
    def get_config(cfg):
        """
Static method: Get configuration from config dictionary.
This is a simple configuration retrieval method mainly used to extract configuration information from already loaded configuration dictionaries.

Args:
    cfg (dict): The configuration dictionary read from the config file.
"""
        return cfg

    def get_all_configs(self):
        """Get all configurations from the config.

Args:
    None.


Examples:
    >>> import lazyllm
    >>> from lazyllm.configs import config
    >>> config['launcher']
    'empty'
    >>> config.get_all_configs()
    {'home': '~/.lazyllm/', 'mode': <Mode.Normal: (1,)>, 'repr_ml': False, 'rag_store': 'None', 'redis_url': 'None', ...}
    """
        return self._impl

    def done(self):
        """Check if any configuration items in the config.json file that is not loaded by the add method.

Args:
    None.
"""
        ins = _ConfigMeta._instances['lazyllm']
        assert len(ins._cfgs) == 0, f'Invalid cfgs ({"".join(ins._cfgs.keys())}) are given in {ins._cgf_path}'

    @contextmanager
    def temp(self, name, value):
        """
Context manager for temporary configuration modification.
Temporarily modifies the value of the specified configuration item within the with statement block, and automatically restores the original value when exiting the block.
Attention: this function is not thread-safe, you should not use it in multi-thread or multi-coroutine environment.

Args:
    name (str): The name of the configuration item to temporarily change.
    value (Any): The temporary value to set.
"""
        old_value = self[name]
        self._impl[name] = value
        yield
        self._impl[name] = old_value

    def _update_impl(self, name: str, type: type, default: Optional[Union[int, str, bool]] = None,
                     env: Union[str, dict, list] = None):
        self._impl[name] = self._cfgs.pop(name) if name in self._cfgs else (
            _ConfigMeta._get_default_home(self._prefix) if name == 'home' else default)
        if isinstance(env, dict):
            for k, v in env.items():
                if self.getenv(k, bool):
                    self._impl[name] = v
                    break
        elif isinstance(env, list):
            for k in env:
                if (v := self.getenv(k, type)):
                    self._impl[name] = v
                    break
        elif env:
            self._impl[name] = self.getenv(env, type, self._impl[name])
        if not isinstance(self._impl[name], type) and self._impl[name] is not None: raise TypeError(
            f'Invalid config type for {name}, type is {type}')

    def __getitem__(self, name):
        try:
            if isinstance(name, bytes): name = name.decode('utf-8')
            name = name.lower()
            if name.startswith(f'{self._prefix.lower()}_'): name = name[len(self._prefix) + 1:]
            return self._impl[name]
        except KeyError as e:
            raise KeyError(f'Error occured when getting key `{name}` from lazyllm global config, msg is: {e}')

    def __str__(self):
        return str(self._impl)

    @property
    def _envs(self):
        return [f'{self._prefix}_{e}'.lower() for e in _ConfigMeta._env_name_map.keys()]

    def refresh(self, targets: Union[bytes, str, List[str]] = None) -> None:
        """
Refresh configuration items based on the latest environment variable values.  
If `targets` is a string, updates the single corresponding configuration item;  
if it's a list, updates multiple;  
if None, scans all environment-variable-mapped configuration items and updates them.

Args:
    targets (str | list[str] | None): Name of the config key or list of keys to refresh, or None to refresh all environment-backed keys.
"""
        names, all_envs = targets, self._envs
        if isinstance(targets, bytes): targets = targets.decode('utf-8')
        if isinstance(targets, str): names = [targets.lower()]
        elif targets is None:
            names = [key.lower() for key in os.environ.keys() if key.lower() in all_envs]
        assert isinstance(names, list)
        for name in names:
            if name.lower() in all_envs:
                name = _ConfigMeta._env_name_map[name[len(self._prefix) + 1:]]
            elif name in Config: continue
            cfg = _ConfigMeta._registered_cfgs[name]
            if name in self._impl: self._update_impl(name, cfg['type'], cfg['default'], cfg['env'])


class _NamespaceConfig(object):
    def __init__(self):
        self.__config = Config()
        self.__threading_config = threading.local()
        self.__context_var_config = ContextVar('lazyllm.Config')

    @property
    def _config(self):
        if events._get_running_loop() is not None:
            config = self.__context_var_config.get(None)
        else:
            config = getattr(self.__threading_config, 'config', None)
        return config or self.__config

    @contextmanager
    def namespace(self, space: str):
        if events._get_running_loop() is not None:
            old_config = self.__context_var_config.get(None)
            self.__context_var_config.set(Config(space))
            yield
            self.__context_var_config.set(old_config)
        else:
            old_config = getattr(self.__threading_config, 'config', None)
            self.__threading_config.config = Config(space)
            yield
            self.__threading_config.config = old_config

    @property
    def _impl(self): return self._config._impl

    def add(self, name: str, type: type, default: Optional[Union[int, str, bool]] = None, env: Union[str, dict] = None,
            *, options: Optional[List] = None, description: Optional[str] = None):
        if (name := name.lower()) in Config.__dict__.keys() or name in _NamespaceConfig.__dict__.keys():
            raise RuntimeError(f'{name} is attribute of Config, please change it!')
        _ConfigMeta.add(name, type, default, env, options=options, description=description)
        return self

    def __getitem__(self, __key):
        return self._config[__key]

    def __getattr__(self, __key: str):
        try:
            return self[__key]
        except KeyError:
            raise AttributeError(f'Config has no attribute {__key}')

    def refresh(self, targets: Union[bytes, str, List[str]] = None) -> None:
        return self._config.refresh(targets)

    def get_all_configs(self):
        return self._config._impl

    @contextmanager
    def temp(self, name, value):
        with self._config.temp(name, value):
            yield

    def done(self):
        return self._config.done()

    @property
    def prefix(self):
        return self._config._prefix


config = _NamespaceConfig().add('mode', Mode, Mode.Normal, dict(DISPLAY=Mode.Display, DEBUG=Mode.Debug),
                                description='The default mode for LazyLLM.'
        ).add('repr_ml', bool, False, 'REPR_USE_ML', description='Whether to use Markup Language for repr.'
        ).add('repr_show_child', bool, False, 'REPR_SHOW_CHILD',
              description='Whether to show child modules in repr.'
        ).add('rag_store', str, 'none', 'RAG_STORE', description='The default store for RAG.'
        ).add('gpu_type', str, 'A100', 'GPU_TYPE', description='The default GPU type for LazyLLM.'
        ).add('train_target_root', str, os.path.join(os.getcwd(), 'save_ckpt'), 'TRAIN_TARGET_ROOT',
              description='The default target root for training.'
        ).add('infer_log_root', str, os.path.join(os.getcwd(), 'infer_log'), 'INFER_LOG_ROOT',
              description='The default log root for inference.'
        ).add('temp_dir', str, os.path.join(os.getcwd(), '.temp'), 'TEMP_DIR',
              description='The default temp directory for LazyLLM.'
        ).add('thread_pool_worker_num', int, 16, 'THREAD_POOL_WORKER_NUM',
              description='The default number of workers for thread pool.'
        ).add('deploy_skip_check_kw', bool, False, 'DEPLOY_SKIP_CHECK_KW',
              description='Whether to skip check keywords for deployment.'
        ).add('allow_internal_network', bool, False, 'ALLOW_INTERNAL_NETWORK',
              description='Whether to allow loading images from internal network addresses. '
                          'Set to False for security in production environments.')

def refresh_config(key):
    if key in Config:
        Config._instances[key.split('_')[0].lower()].refresh(key)


class Namespace(object):
    """A namespace wrapper used to invoke LazyLLM module constructors under a specified configuration namespace.

`namespace` can be used either as a context manager or as a lightweight wrapper for single calls.
It allows binding LazyLLM configuration and module construction to a specific namespace
without affecting the global configuration.

Supported modules include:
AutoModel, OnlineModule, OnlineChatModule, OnlineEmbeddingModule, and OnlineMultiModalModule.

**Usage:**

- As a context manager: within a `with lazyllm.namespace(space)` block, all LazyLLM configuration
  and module construction will use the given namespace.
- As a wrapper call: using `lazyllm.namespace(space).OnlineChatModule(...)` applies the namespace
  only to that single constructor call.

**Notes:**

- A `namespace` instance is not thread-safe. In multi-threaded environments,
  create a separate instance per thread even if they share the same space name.


Examples:
    >>> import os
    >>> import lazyllm
    >>> from lazyllm import namespace
    >>> with lazyllm.namespace('my'):
    ...     assert lazyllm.config['gpu_type'] == 'A100'
    ...     os.environ['MY_GPU_TYPE'] = 'H100'
    ...     assert lazyllm.config['gpu_type'] == 'H100'
    ...
    >>>
    >>> assert lazyllm.config['gpu_type'] == 'A100'
    >>>
    >>> with lazyllm.namespace('my'):
    ...     m = lazyllm.OnlineChatModule()
    ...
    >>> m = lazyllm.namespace('my').OnlineChatModule()
    """
    supported = set()

    def __init__(self, space: str):
        self._space = space
        self._cm = None

    @staticmethod
    def register_module(module: Union[str, List[str]]):
        """Register LazyLLM module names that can be proxied by `namespace`.

Registered module names will be added to the class-level `namespace.supported` set,
allowing them to be constructed via `namespace(space).<ModuleName>(...)`
under the specified namespace.

This is a class-level registration method and affects all `namespace` instances.

**Parameters:**

- module (str | List[str]): The module name(s) to register.
  - A string registers a single module name;
  - A list of strings registers multiple module names at once.


Examples:
    >>> import lazyllm
    >>> from lazyllm import namespace
    >>> namespace.register_module('OnlineChatModule')
    >>> 'OnlineChatModule' in namespace.supported
    True
    >>> namespace.register_module(['AutoModel', 'OnlineEmbeddingModule'])
    >>> 'AutoModel' in namespace.supported
    True
    >>> 'OnlineEmbeddingModule' in namespace.supported
    True
    >>> namespace('my').OnlineChatModule().space
    'my'
    """
        if isinstance(module, str):
            Namespace.supported.add(module)
        else:
            Namespace.supported.update(module)

    def __getattr__(self, __key):
        def wrapper(*args, **kw):
            with lazyllm.config.namespace(self._space):
                return getattr(lazyllm, __key)(*args, **kw)

        if __key in Namespace.supported:
            return wrapper
        raise AttributeError(f'Namespace has no attribute {__key}, all support attribute are {Namespace.supported}')

    def __enter__(self):
        if self._cm: raise RuntimeError('Namespace is not thread-safe, please use another Namespace object with '
                                        'the same space name in multi-thread environment')
        self._cm = lazyllm.config.namespace(self._space)
        self._cm.__enter__()
        return self

    def __exit__(self, exc_type, exc, tb):
        return self._cm.__exit__(exc_type, exc, tb)
