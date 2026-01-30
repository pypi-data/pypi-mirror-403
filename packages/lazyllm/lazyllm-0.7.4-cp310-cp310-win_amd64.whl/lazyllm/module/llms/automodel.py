from typing import Any, Optional, Union
import lazyllm
from lazyllm import LOG
from .online_module import OnlineModule
from .trainablemodule import TrainableModule
from .utils import get_candidate_entries, process_trainable_args, process_online_args


class AutoModel:
    """A factory for quickly creating either an online ``OnlineModule`` or a local ``TrainableModule``. It prioritizes user-provided arguments; when ``config`` is enabled, settings in ``auto_model_config_map`` can override them, and it automatically decides which module to build: 

- For online mode, arguments are passed through to ``OnlineModule`` (automatically matching OnlineChatModule / OnlineEmbeddingModule / OnlineMultiModalModule).

- For local mode, it initializes ``TrainableModule`` with ``model`` and user parameters, then reads the config map for configuration values.

Args:
    model (str): Name of the model, e.g., ``Qwen3-32B``. Required.
    config_id (Optional[str]): ID from the config file. Defaults to empty.
    source (Optional[str]): Provider for online modules (``qwen`` / ``glm`` / ``openai``). Set to ``local`` to force a local TrainableModule.
    type (Optional[str]): Model type. If omitted, it will try to fetch from kwargs or be inferred by the online module.
    config (Union[str, bool]): Whether to enable overrides from ``auto_model_config_map``, or a user-specified config file path. Defaults to True.
    **kwargs: Accepts `base_model` and `embed_model_name` as synonyms for `model`; does not accept other user-provided fields.
"""

    def __new__(cls, model: Optional[str] = None, *, config_id: Optional[str] = None, source: Optional[str] = None,  # noqa C901
                type: Optional[str] = None, config: Union[str, bool] = True, **kwargs: Any):
        # check and accomodate user params
        model = model or kwargs.pop('base_model', kwargs.pop('embed_model_name', None))
        if model in lazyllm.online.chat:
            source, model = model, None

        if not model:
            try:
                return lazyllm.OnlineModule(source=source, type=type)
            except Exception as e:
                raise RuntimeError(f'`model` is not provided in AutoModel, and {e}') from None

        trainable_entry, online_entry = get_candidate_entries(model, config_id, source, config)

        # 1) first: try TrainableModule with trainable config (for directly connecting deployed endpoint)
        if trainable_entry is not None:
            trainable_args = process_trainable_args(
                model=model, type=type, source=source, config=config, entry=trainable_entry
            )
            try:
                module = TrainableModule(**trainable_args)
                if module._url or module._impl._get_deploy_tasks.flag: return module
            except Exception as e:
                LOG.warning('Fail to create `TrainableModule`, will try to '
                            f'load model {model} with `OnlineModule`. Since the error: {e}')

        # 2) second: try OnlineModule with online config if found
        if online_entry is not None:
            online_args = process_online_args(model=model, source=source, type=type, entry=online_entry)
            if online_args: return OnlineModule(**online_args)

        # 3) finally: fallback (no config or config unusable)
        try:
            return OnlineModule(model=model, source=source, type=type)
        except Exception as e:
            LOG.warning('`OnlineModule` creation failed, and will try to '
                        f'load model {model} with local `TrainableModule`. Since the error: {e}')
            return TrainableModule(model, type=type)
