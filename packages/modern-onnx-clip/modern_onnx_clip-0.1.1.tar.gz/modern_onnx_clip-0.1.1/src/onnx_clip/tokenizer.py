import gzip
import html
import logging
import os
from functools import lru_cache

import ftfy
import numpy as np
import regex as re
import requests

# Constants for OpenAI CLIP tokenizer
VOCAB_URL = "https://openaipublic.azureedge.net/clip/bpe_simple_vocab_16e6.txt.gz"
CACHE_DIR = os.path.expanduser("~/.cache/onnx-clip")


def download_vocab(target_dir: str) -> str:
    """Downloads the standard CLIP BPE vocabulary file if not present.

    Args:
        target_dir (str): Directory to save the vocabulary file.

    Returns:
        str: Path to the downloaded (or existing) vocabulary file.

    Raises:
        requests.RequestException: If the download fails.
    """
    os.makedirs(target_dir, exist_ok=True)
    target_path = os.path.join(target_dir, "bpe_simple_vocab_16e6.txt.gz")

    if os.path.exists(target_path):
        return target_path

    logging.info(f"Downloading vocab to {target_path}...")
    try:
        response = requests.get(VOCAB_URL, stream=True)
        response.raise_for_status()
        with open(target_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return target_path
    except Exception as e:
        logging.error(f"Failed to download vocab: {e}")
        raise


@lru_cache
def bytes_to_unicode() -> dict[int, str]:
    """Returns a dictionary mapping UTF-8 bytes to Unicode strings.

    This avoids mapping to whitespace/control characters that BPE might misinterpret.
    Based on the OpenAI CLIP implementation.

    Returns:
        Dict[int, str]: Mapping from byte integer values to unicode characters.
    """
    # Use numeric codes instead of unicode literals to avoid encoding issues
    bs = (
        list(range(ord("!"), ord("~") + 1))
        + list(range(0xA1, 0xAC + 1))  # ¡ to ¬
        + list(range(0xAE, 0xFF + 1))  # ® to ÿ
    )
    cs = bs[:]
    n = 0
    for b in range(2**8):
        if b not in bs:
            bs.append(b)
            cs.append(2**8 + n)
            n += 1
    cs = [chr(n) for n in cs]
    return dict(zip(bs, cs, strict=False))


def get_pairs(word: tuple[str, ...]) -> set[tuple[str, str]]:
    """Returns a set of symbol pairs in a word.

    Args:
        word (Tuple[str, ...]): Word represented as a tuple of symbols.

    Returns:
        Set[Tuple[str, str]]: Set of adjacent character pairs.
    """
    pairs = set()
    prev_char = word[0]
    for char in word[1:]:
        pairs.add((prev_char, char))
        prev_char = char
    return pairs


def basic_clean(text: str) -> str:
    """Performs basic text cleaning: fixing text encoding and unescaping HTML.

    Args:
        text (str): Input text.

    Returns:
        str: Cleaned text.
    """
    text = ftfy.fix_text(text)
    text = html.unescape(html.unescape(text))
    return text.strip()


def whitespace_clean(text: str) -> str:
    """Collapses multiple whitespaces into a single space.

    Args:
        text (str): Input text.

    Returns:
        str: Text with normalized whitespace.
    """
    text = re.sub(r"\s+", " ", text)
    text = text.strip()
    return text


class SimpleTokenizer:
    """A pure-Python implementation of the CLIP Byte-Pair Encoding (BPE) tokenizer.

    This class replicates the logic of `clip.simple_tokenizer` from OpenAI,
    allowing text tokenization without the heavy dependencies of the original library.

    Attributes:
        bpe_ranks (Dict[Tuple[str, str], int]): Priority ranking of BPE merge pairs.
        encoder (Dict[str, int]): Mapping from token strings to IDs.
        decoder (Dict[int, str]): Mapping from IDs to token strings.
    """

    def __init__(self, bpe_path: str | None = None):
        """Initializes the tokenizer.

        Args:
            bpe_path (str, optional): Path to the `bpe_simple_vocab_16e6.txt.gz` file.
                If None, it will be automatically downloaded to `~/.cache/onnx-clip`.
        """
        if bpe_path is None:
            # Auto-download to cache if not provided
            bpe_path = download_vocab(CACHE_DIR)

        self.byte_encoder = bytes_to_unicode()
        self.byte_decoder = {v: k for k, v in self.byte_encoder.items()}

        merges = []
        with gzip.open(bpe_path, "rb") as f:
            data = f.read().decode("utf-8")

        merges = data.split("\n")
        merges = merges[1 : 49152 - 256 - 2 + 1]
        merges = [tuple(merge.split()) for merge in merges]

        self.bpe_ranks = dict(zip(merges, range(len(merges)), strict=False))
        self.cache = {
            "<|startoftext|>": "<|startoftext|>",
            "<|endoftext|>": "<|endoftext|>",
        }

        vocab = list(bytes_to_unicode().values())
        vocab = [v + "</w>" for v in vocab]
        for merge in merges:
            vocab.append("".join(merge))
        vocab.extend(["<|startoftext|>", "<|endoftext|>"])
        self.encoder = dict(zip(vocab, range(len(vocab)), strict=False))
        self.decoder = {v: k for k, v in self.encoder.items()}

    def bpe(self, token: str) -> str:
        """Applies Byte-Pair Encoding to a single token.

        Args:
            token (str): The token to encode.

        Returns:
            str: Space-separated string of BPE subwords.
        """
        if token in self.cache:
            return self.cache[token]
        word = tuple(token[:-1]) + (token[-1] + "</w>",)
        pairs = get_pairs(word)

        if not pairs:
            return token + "</w>"

        while True:
            bigram = min(pairs, key=lambda pair: self.bpe_ranks.get(pair, float("inf")))
            if bigram not in self.bpe_ranks:
                break
            first, second = bigram
            new_word = []
            i = 0
            while i < len(word):
                try:
                    j = word.index(first, i)
                    new_word.extend(word[i:j])
                    i = j
                except Exception:
                    new_word.extend(word[i:])
                    break

                if word[i] == first and i < len(word) - 1 and word[i + 1] == second:
                    new_word.append(first + second)
                    i += 2
                else:
                    new_word.append(word[i])
                    i += 1
            new_word = tuple(new_word)
            word = new_word
            if len(word) == 1:
                break
            else:
                pairs = get_pairs(word)
        word = " ".join(word)
        self.cache[token] = word
        return word

    def encode(self, text: str) -> list[int]:
        """Encodes text into a list of token IDs.

        Args:
            text (str): The input text string.

        Returns:
            List[int]: List of integer token IDs (not padded, no SOT/EOT).
        """
        bpe_tokens = []
        text = whitespace_clean(basic_clean(text)).lower()
        for token in re.findall(self.pat, text):
            token = "".join(self.byte_encoder[b] for b in token.encode("utf-8"))
            bpe_tokens.extend(
                self.encoder[bpe_token] for bpe_token in self.bpe(token).split(" ")
            )
        return bpe_tokens

    @property
    def pat(self) -> str:
        """Regex pattern for tokenization."""
        return (
            r"<\|startoftext\|>|<\|endoftext\|>|'s|'t|'re|'ve|'m|'ll|'d|"
            r"[\p{L}]+|[\p{N}]|[^\s\p{L}\p{N}]+"
        )

    def tokenize(self, texts: str | list[str], context_length: int = 77) -> np.ndarray:
        """Tokenizes text and returns a numpy array suitable for model input.

        Handles Start-of-Text (SOT) and End-of-Text (EOT) tokens, padding, and
        truncation.

        Args:
            texts (Union[str, List[str]]): A single string or a list of strings.
            context_length (int, optional): The fixed length of the token sequence.
                Defaults to 77.

        Returns:
            np.ndarray: A numpy array of shape (N, context_length) with dtype int64.
        """
        if isinstance(texts, str):
            texts = [texts]

        sot_token = self.encoder["<|startoftext|>"]
        eot_token = self.encoder["<|endoftext|>"]
        all_tokens = []

        for text in texts:
            tokens = [sot_token] + self.encode(text) + [eot_token]
            if len(tokens) > context_length:
                tokens = tokens[:context_length]
                tokens[-1] = eot_token
            else:
                tokens.extend([0] * (context_length - len(tokens)))
            all_tokens.append(tokens)

        return np.array(all_tokens, dtype=np.int64)
