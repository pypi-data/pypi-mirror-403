import numpy as np

from onnx_clip.tokenizer import (
    SimpleTokenizer,
    basic_clean,
    bytes_to_unicode,
    get_pairs,
    whitespace_clean,
)


class TestHelperFunctions:
    """Tests for tokenizer helper functions."""

    def test_bytes_to_unicode_length(self):
        """Test that bytes_to_unicode returns 256 mappings."""
        result = bytes_to_unicode()
        assert len(result) == 256

    def test_bytes_to_unicode_is_cached(self):
        """Test that bytes_to_unicode is cached (same object returned)."""
        result1 = bytes_to_unicode()
        result2 = bytes_to_unicode()
        assert result1 is result2

    def test_get_pairs_single_char(self):
        """Test get_pairs with single character word."""
        result = get_pairs(("a",))
        assert result == set()

    def test_get_pairs_two_chars(self):
        """Test get_pairs with two character word."""
        result = get_pairs(("a", "b"))
        assert result == {("a", "b")}

    def test_get_pairs_multiple_chars(self):
        """Test get_pairs with multiple characters."""
        result = get_pairs(("h", "e", "l", "l", "o"))
        expected = {("h", "e"), ("e", "l"), ("l", "l"), ("l", "o")}
        assert result == expected

    def test_basic_clean_strips_whitespace(self):
        """Test that basic_clean strips leading/trailing whitespace."""
        result = basic_clean("  hello world  ")
        assert result == "hello world"

    def test_basic_clean_unescapes_html(self):
        """Test that basic_clean unescapes HTML entities."""
        result = basic_clean("hello &amp; world")
        assert result == "hello & world"

    def test_whitespace_clean_collapses(self):
        """Test that whitespace_clean collapses multiple spaces."""
        result = whitespace_clean("hello    world")
        assert result == "hello world"

    def test_whitespace_clean_tabs_newlines(self):
        """Test that whitespace_clean handles tabs and newlines."""
        result = whitespace_clean("hello\t\n  world")
        assert result == "hello world"


class TestSimpleTokenizerInit:
    """Tests for SimpleTokenizer initialization."""

    def test_init_downloads_vocab(self):
        """Test that tokenizer initializes and downloads vocab if needed."""
        tokenizer = SimpleTokenizer()
        assert tokenizer.encoder is not None
        assert tokenizer.decoder is not None
        assert tokenizer.bpe_ranks is not None

    def test_special_tokens_in_encoder(self):
        """Test that special tokens are in the encoder."""
        tokenizer = SimpleTokenizer()
        sot_token = "<" + "|startoftext|" + ">"
        eot_token = "<" + "|endoftext|" + ">"
        assert sot_token in tokenizer.encoder
        assert eot_token in tokenizer.encoder


class TestSimpleTokenizerEncode:
    """Tests for SimpleTokenizer encode method."""

    def test_encode_simple_text(self):
        """Test encoding simple text."""
        tokenizer = SimpleTokenizer()
        result = tokenizer.encode("hello")
        assert isinstance(result, list)
        assert all(isinstance(x, int) for x in result)
        assert len(result) > 0

    def test_encode_returns_list_of_ints(self):
        """Test that encode returns list of integers."""
        tokenizer = SimpleTokenizer()
        result = tokenizer.encode("a photo of a cat")
        assert isinstance(result, list)
        assert all(isinstance(token, int) for token in result)

    def test_encode_different_texts_different_tokens(self):
        """Test that different texts produce different tokens."""
        tokenizer = SimpleTokenizer()
        result1 = tokenizer.encode("cat")
        result2 = tokenizer.encode("dog")
        assert result1 != result2


class TestSimpleTokenizerTokenize:
    """Tests for SimpleTokenizer tokenize method."""

    def test_tokenize_single_text(self):
        """Test tokenizing a single text string."""
        tokenizer = SimpleTokenizer()
        result = tokenizer.tokenize("hello world")

        assert isinstance(result, np.ndarray)
        assert result.dtype == np.int64
        assert result.shape == (1, 77)

    def test_tokenize_list_of_texts(self, sample_texts: list[str]):
        """Test tokenizing a list of texts."""
        tokenizer = SimpleTokenizer()
        result = tokenizer.tokenize(sample_texts)

        assert result.shape == (len(sample_texts), 77)

    def test_tokenize_custom_context_length(self):
        """Test tokenizing with custom context length."""
        tokenizer = SimpleTokenizer()
        result = tokenizer.tokenize("hello", context_length=50)

        assert result.shape == (1, 50)

    def test_tokenize_includes_sot_eot(self):
        """Test that tokenized output includes SOT and EOT tokens."""
        tokenizer = SimpleTokenizer()
        sot_token = "<" + "|startoftext|" + ">"
        eot_token = "<" + "|endoftext|" + ">"
        result = tokenizer.tokenize("hello")

        sot_id = tokenizer.encoder[sot_token]
        eot_id = tokenizer.encoder[eot_token]

        assert result[0, 0] == sot_id
        # EOT should be somewhere in the sequence
        assert eot_id in result[0]

    def test_tokenize_pads_short_text(self):
        """Test that short texts are padded to context_length."""
        tokenizer = SimpleTokenizer()
        result = tokenizer.tokenize("hi", context_length=77)

        # Should have padding zeros
        assert 0 in result[0]

    def test_tokenize_truncates_long_text(self):
        """Test that long texts are truncated."""
        tokenizer = SimpleTokenizer()
        long_text = "word " * 100  # Very long text
        result = tokenizer.tokenize(long_text, context_length=77)

        assert result.shape == (1, 77)


class TestBPEMethod:
    """Tests for the BPE encoding method."""

    def test_bpe_caches_results(self):
        """Test that BPE results are cached."""
        tokenizer = SimpleTokenizer()
        token = "hello"

        # First call should compute and cache
        result1 = tokenizer.bpe(token)
        # Second call should use cache
        result2 = tokenizer.bpe(token)

        assert result1 == result2
        assert token in tokenizer.cache

    def test_bpe_returns_string(self):
        """Test that BPE returns a string."""
        tokenizer = SimpleTokenizer()
        result = tokenizer.bpe("test")
        assert isinstance(result, str)
