import re
import difflib
from typing import List, Optional, Dict, Any

import lazyllm

from lazyllm import AutoModel, warp, package
from ....module import LLMBase

DEFAULT_INSTRUCTION = '纠正输入句子中的语法错误，并只输出正确的句子，绝对不允许输出其他内容，' \
                      '例如：输入"我喜欢编程成"，输出"我喜欢编程"输入句子为：{sentence}'
DEFAULT_MAX_TOKENS = 512
DEFAULT_BATCH_SIZE = 4
DEFAULT_TEMPERATURE = 0.6


def get_errors(corrected_text, origin_text):  # noqa: C901
    """Compare corrected text with original text to find error locations and contents.

Uses sequence matching algorithm to compare differences between two texts, returns a list of errors,
each containing original character, corrected character, and position information.

Args:
    corrected_text (str): The corrected text.
    origin_text (str): The original text.

Returns:
    list: List of errors, each element is a tuple (orig_char, corr_char, pos) where:
        - orig_char (str): Original character, empty string if insertion error.
        - corr_char (str): Corrected character, empty string if deletion error.
        - pos (int): Position of error in original text.


Examples:
        >>> from lazyllm.tools.review.tools.chinese_corrector import get_errors
        >>> errors = get_errors("我喜欢编程", "我喜欢编程成")
        >>> print(errors)
        [('', '成', 6)]
    """
    errors = []
    unk_tokens = set([' ', '“', '”', '‘', '’', '琊', '\n', '…', '擤', '\t', '玕', ''])

    def add_error(orig_char, corr_char, pos):
        if orig_char not in unk_tokens and corr_char not in unk_tokens:
            errors.append((orig_char, corr_char, pos))

    matcher = difflib.SequenceMatcher(None, origin_text, corrected_text)

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'equal':
            continue

        origin_part = origin_text[i1:i2]
        corrected_part = corrected_text[j1:j2]

        min_len = min(len(origin_part), len(corrected_part))

        for idx in range(min_len):
            add_error(origin_part[idx], corrected_part[idx], i1 + idx)

        for idx in range(min_len, len(origin_part)):
            add_error(origin_part[idx], '', i1 + idx)

        insert_pos = i1 + len(origin_part) if tag == 'replace' else i1
        for idx in range(min_len, len(corrected_part)):
            add_error('', corrected_part[idx], insert_pos)

    return sorted(errors, key=lambda x: x[2])


class ChineseCorrector:
    """Chinese text corrector that uses large language models to correct grammar and spelling errors in Chinese sentences.

Can correct single sentences or batches of sentences by configuring different language models,
and returns correction results with error details.

Args:
    llm: Optional, large language model instance. Uses default model if None.
    base_url (str): Optional, base URL for model service.
    model (str): Optional, model name to use.
    api_key (str): Optional, API key, defaults to 'null'.
    source (str): Model source, defaults to 'openai'.


Examples:
        >>> import lazyllm
        >>> from lazyllm.tools.review.tools.chinese_corrector import ChineseCorrector
        >>> corrector = ChineseCorrector()
        >>> result = corrector.correct("我喜欢编程成")
        >>> print(result)
        {'source': '我喜欢编程成', 'target': '我喜欢编程', 'errors': [('成', '', 6)]}
        >>>
        >>> results = corrector.correct_batch(["句子1", "句子2"])
        >>> print(results)
        [{'source': '句子1', 'target': '修正后句子1', 'errors': [...]}, ...]
    """
    def __init__(self, llm: Optional[LLMBase] = None, base_url: Optional[str] = None,
                 model: Optional[str] = None, api_key: Optional[str] = 'null',
                 source: str = 'openai', **_: Any):
        if llm:
            base_llm = llm
        else:
            base_llm = AutoModel(source=source, model=model)
        self.base_llm = base_llm.prompt(lazyllm.AlpacaPrompter(DEFAULT_INSTRUCTION))

    def _predict(self, sentences: List[str], max_tokens: Optional[int] = None,
                 temperature: Optional[float] = None, **kwargs) -> List[Dict[str, Any]]:
        if not sentences:
            return []

        llm_kwargs = {
            'max_tokens': max_tokens or DEFAULT_MAX_TOKENS,
            'temperature': temperature if temperature is not None else DEFAULT_TEMPERATURE
        }

        llm_kwargs.update(kwargs)

        results: List[Dict[str, Any]] = []
        for sentence in sentences:
            try:
                response = self.base_llm(
                    dict(sentence=sentence),
                    stream_output=False,
                    **llm_kwargs,
                )
                response = self._post_process(response, sentence)
                errors = get_errors(response, sentence)
            except Exception as e:
                lazyllm.LOG.error(
                    f'Error predicting sentence {sentence[:50]}{"..." if len(sentence) > 50 else ""}. '
                    f'with max_tokens: {max_tokens}, temperature: {temperature}'
                    f'Error: {e}'
                )
                response = ''
                errors = []
            results.append(
                {
                    'source': sentence,
                    'target': response,
                    'errors': errors,
                }
            )

        return results

    def correct(self, sentence: str, **kwargs) -> Dict[str, Any]:
        """Correct grammar and spelling errors in a single Chinese sentence.

Uses the configured language model to correct the input sentence and returns a dictionary
containing the original text, corrected text, and error details.

Args:
    sentence (str): The Chinese sentence to correct.
    **kwargs: Additional parameters passed to the language model, such as max_tokens, temperature, etc.

Returns:
    dict: Dictionary containing the following keys:
        - source (str): The original input sentence.
        - target (str): The corrected sentence.
        - errors (list): List of errors, each element is a tuple (orig_char, corr_char, pos).
"""
        results = self._predict([sentence], **kwargs)
        return results[0] if results else {'source': sentence, 'target': sentence, 'errors': []}

    def correct_batch(self, sentences: List[str], batch_size: int = DEFAULT_BATCH_SIZE,
                      concurrency: Optional[int] = 2, **kwargs) -> List[Dict[str, Any]]:
        """Batch correct grammar and spelling errors in multiple Chinese sentences.

Uses parallel processing to correct multiple sentences efficiently. Returns a list of dictionaries
containing correction results for each sentence.

Args:
    sentences (list): List of Chinese sentences to correct.
    batch_size (int): Optional, batch size, defaults to 4.
    concurrency (int): Optional, concurrency level, defaults to 2.
    **kwargs: Additional parameters passed to the language model, such as max_tokens, temperature, etc.

Returns:
    list: List of dictionaries, each containing correction results with keys:
        - source (str): The original input sentence.
        - target (str): The corrected sentence.
        - errors (list): List of errors, each element is a tuple (orig_char, corr_char, pos).
"""
        if not sentences:
            return []

        def process_sentence(sent: str) -> Dict[str, Any]:
            try:
                res = self._predict([sent], **kwargs)
                return res[0] if res else {'source': sent, 'target': sent, 'errors': []}
            except Exception as e:
                lazyllm.LOG.error(f'Error processing sentence: {e}')
                return {'source': sent, 'target': sent, 'errors': []}

        try:
            results_package = warp(process_sentence, _concurrent=concurrency)(package(sentences))
            results = list(results_package)
            return results
        except Exception as e:
            lazyllm.LOG.error(f'Error in warp processing: {e}')
            return [{'source': sent, 'target': sent, 'errors': []} for sent in sentences]

    def _post_process(self, response: str, origin: str) -> str:
        response = response.strip()
        match = re.search(r'</think\s*>(.*)', response, re.DOTALL)
        if match:
            response = match.group(1).strip()
        else:
            response = re.sub(r'^<think>.*?</think>', '', response, flags=re.DOTALL).strip()

        sentence_endings = ['。', '！', '？', '；', '：', '，', '、', '.', ',', '?', '!', ':']
        origin_ending = origin[-1] if origin[-1] in sentence_endings else None
        response_ending = response[-1] if response[-1] in sentence_endings else None
        if origin_ending and not response_ending:
            response += origin_ending
        elif not origin_ending and response_ending:
            response = response[:-1]
        return response
