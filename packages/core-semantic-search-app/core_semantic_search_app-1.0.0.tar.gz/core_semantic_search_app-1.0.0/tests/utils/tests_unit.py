"""Utils unit testing
"""

from unittest.case import TestCase
from unittest.mock import MagicMock

from core_semantic_search_app.utils.chunking_utils import (
    get_nested_value,
    sliding_window,
    flatten_dict,
    chunk_json_dict,
)
from core_semantic_search_app.utils.model_utils.response import (
    build_doc_list,
    build_doc_data_list,
)


class TestGetNestedValue(TestCase):
    """TestGetNestedValue"""

    def test_get_nested_key_exists(self):
        """test_get_nested_key_exists

        Returns:

        """
        dictionary = {"a": {"b": {"c": "value"}}}
        result = get_nested_value(dictionary, "a.b.c")
        self.assertEqual(result, "value")

    def test_get_nested_key_does_not_exist(self):
        """test_get_nested_key_does_not_exist

        Returns:

        """
        dictionary = {"a": {"b": {"c": "value"}}}
        result = get_nested_value(dictionary, "a.b.d")
        self.assertIsNone(result)

    def test_get_nested_not_dict(self):
        """test_get_nested_not_dict

        Returns:

        """
        result = get_nested_value(list(), "a.b.c")
        self.assertIsNone(result)

    def test_get_nested_empty_dict(self):
        """test_get_nested_empty_dict

        Returns:

        """
        result = get_nested_value(dict(), "a.b.c")
        self.assertIsNone(result)

    def test_get_nested_empty_keys(self):
        """test_get_nested_empty_keys

        Returns:

        """
        dictionary = {"a": {"b": {"c": "value"}}}
        result = get_nested_value(dictionary, "")
        self.assertIsNone(result)

    def test_get_nested_invalid_path(self):
        """test_get_nested_invalid_path

        Returns:

        """
        dictionary = {"a": {"b": {"c": "value"}}}
        result = get_nested_value(dictionary, "a..b.c")
        self.assertIsNone(result)


class TestFlattenDict(TestCase):
    """TestFlattenDict"""

    def test_flatten_dict(self):
        """test_flatten_dict

        Returns:

        """
        dictionary = {"a": 1, "b": 2}
        expected = {"a": 1, "b": 2}
        self.assertEqual(dict(flatten_dict(dictionary)), expected)

    def test_flatten_nested_dict(self):
        """test_flatten_nested_dict

        Returns:

        """
        dictionary = {"a": 1, "b": {"c": 2, "d": 3}}
        expected = {"a": 1, "b > c": 2, "b > d": 3}
        self.assertEqual(dict(flatten_dict(dictionary)), expected)

    def test_flatten_dict_with_list(self):
        """test_flatten_dict_with_list

        Returns:

        """
        dictionary = {"a": 1, "b": [2, 3]}
        expected = {"a": 1, "b > 0": 2, "b > 1": 3}
        self.assertEqual(dict(flatten_dict(dictionary)), expected)

    def test_flatten_dict_with_nested_list(self):
        """test_flatten_dict_with_nested_list

        Returns:

        """
        dictionary = {"a": 1, "b": [2, [3, 4]]}
        expected = {"a": 1, "b > 0": 2, "b > 1 > 0": 3, "b > 1 > 1": 4}
        self.assertEqual(dict(flatten_dict(dictionary)), expected)

    def test_flatten_empty_dict(self):
        """test_flatten_empty_dict

        Returns:

        """
        dictionary = {}
        expected = {}
        self.assertEqual(dict(flatten_dict(dictionary)), expected)

    def test_flatten_empty_list(self):
        """test_flatten_empty_list

        Returns:

        """
        dictionary = {"a": []}
        expected = {}
        self.assertEqual(dict(flatten_dict(dictionary)), expected)

    def test_flatten_none_value(self):
        """test_flatten_none_value

        Returns:

        """
        dictionary = {"a": None}
        expected = {"a": None}
        self.assertEqual(dict(flatten_dict(dictionary)), expected)

    def test_flatten_mixed_types(self):
        """test_flatten_mixed_types

        Returns:

        """
        dictionary = {"a": 1, "b": "test", "c": True, "d": None}
        expected = {"a": 1, "b": "test", "c": True, "d": None}
        self.assertEqual(dict(flatten_dict(dictionary)), expected)


class TestSlidingWindow(TestCase):
    """TestSlidingWindow"""

    def test_default_window_size_and_overlap(self):
        """test_default_window_size_and_overlap

        Returns:

        """
        text = " ".join(str(i) for i in range(1000))
        result = list(sliding_window(text))
        self.assertGreater(len(result), 0)

    def test_custom_window_size(self):
        """test_custom_window_size

        Returns:

        """
        text = " ".join(str(i) for i in range(100))
        window_size = 10
        overlap = 5
        result = list(
            sliding_window(text, chunk_size=window_size, chunk_overlap=overlap)
        )
        for window in result:
            self.assertLessEqual(len(window.split()), window_size)

    def test_empty_text(self):
        """test_empty_text

        Returns:

        """
        text = ""
        result = list(sliding_window(text))
        self.assertEqual(result, [])

    def test_single_word_text(self):
        """test_single_word_text

        Returns:

        """
        text = "test"
        result = list(sliding_window(text))
        self.assertEqual(result, ["test"])

    def test_overlap_bigger_than_window_size(self):
        """test_overlap_bigger_than_window_size

        Returns:

        """
        text = " ".join(str(i) for i in range(10))
        with self.assertRaises(ValueError):
            list(sliding_window(text, chunk_size=10, chunk_overlap=20))

    def test_text_with_fewer_words_than_window_size(self):
        """test_text_with_fewer_words_than_window_size

        Returns:

        """
        text = " ".join(str(i) for i in range(5))
        result = list(sliding_window(text, chunk_size=100, chunk_overlap=20))
        self.assertEqual(len(result), 1)

    def test_large_text(self):
        """test_large_text

        Returns:

        """
        text = " ".join(str(i) for i in range(10000))
        chunk_size = 2000
        chunk_overlap = 200
        chunks = sliding_window(
            text, chunk_size=chunk_size, chunk_overlap=chunk_overlap
        )
        self.assertGreater(len(chunks), 1)

    def test_text_without_spaces(self):
        """test_text_without_spaces

        Returns:

        """
        text = "a" * 100
        chunk_size = 20
        chunk_overlap = 0
        chunks = sliding_window(
            text, chunk_size=chunk_size, chunk_overlap=chunk_overlap
        )
        self.assertEqual(len(chunks), 5)

    def test_text_without_spaces_and_overlap(self):
        """test_text_without_spaces_and_overlap

        Returns:

        """
        text = "a" * 100
        chunk_size = 20
        chunk_overlap = 5
        chunks = sliding_window(
            text, chunk_size=chunk_size, chunk_overlap=chunk_overlap
        )
        self.assertGreater(len(chunks), 5)

    def test_text_with_multiple_consecutive_spaces(self):
        """test_text_with_multiple_consecutive_spaces

        Returns:

        """
        text = " ".join(str(i) for i in range(100))
        text = text.replace(" ", "   ")
        chunk_size = 20
        chunk_overlap = 5
        chunks = sliding_window(
            text, chunk_size=chunk_size, chunk_overlap=chunk_overlap
        )
        self.assertGreater(len(chunks), 1)


class TestChunkJSONDict(TestCase):
    def setUp(self):
        """setUp

        Returns:

        """
        self.maxDiff = None

    def test_empty_dict(self):
        """test_empty_dict

        Returns:

        """
        json_dict = {}
        expected = []
        result = chunk_json_dict(json_dict)
        self.assertEqual(result, expected)

    def test_simple_dict(self):
        """test_simple_dict

        Returns:

        """
        json_dict = {"key1": "value1", "key2": "value2"}
        expected = ["key1 | value1 \n key2 | value2"]
        result = chunk_json_dict(json_dict)
        self.assertEqual(result, expected)

    def test_nested_dict(self):
        """test_nested_dict

        Returns:

        """
        json_dict = {"key1": {"subkey1": "subvalue1"}, "key2": "value2"}
        expected = ["key1 > subkey1 | subvalue1 \n key2 | value2"]
        result = chunk_json_dict(json_dict)
        self.assertEqual(result, expected)

    def test_large_value(self):
        """test_large_value

        Returns:

        """
        json_dict = {"key1": "a" * 1500}
        result = chunk_json_dict(json_dict, chunk_size=1000, chunk_overlap=200)
        self.assertEqual(len(result[0]), 1000)
        self.assertEqual(result[0], "key1 | " + "a" * (1000 - 7))  # 7 = key1 |
        # 1500 total - (1000 - 7) a from first chunk + 200 overlap
        expected_a = 1500 - (1000 - 7) + 200
        self.assertEqual(len(result[1]), expected_a + 7)  # 7 = key1 |
        self.assertEqual(result[1], "key1 | " + "a" * expected_a)

    def test_target_keys(self):
        """test_target_keys

        Returns:

        """
        json_dict = {"key1": "value1", "key2": "value2"}
        target_keys = ["key1"]
        expected = ["key1 | value1"]
        result = chunk_json_dict(json_dict, target_keys=target_keys)
        self.assertEqual(result, expected)

    def test_chunk_size(self):
        """test_chunk_size

        Returns:

        """
        json_dict = {"key1": "value1", "key2": "value2"}
        chunk_size = 15
        expected = ["key1 | value1", "key2 | value2"]
        result = chunk_json_dict(
            json_dict, chunk_size=chunk_size, chunk_overlap=0
        )
        self.assertEqual(result, expected)

    def test_chunk_overlap(self):
        """test_chunk_overlap

        Returns:

        """
        json_dict = {"key1": "a" * 1500}
        chunk_overlap = 200
        result = chunk_json_dict(json_dict, chunk_overlap=chunk_overlap)
        self.assertGreater(len(result[0]), len(result[1]))

    def test_key_sep(self):
        """test_key_sep

        Returns:

        """
        json_dict = {"key1": {"subkey1": "subvalue1"}}
        key_sep = "."
        expected = ["key1.subkey1 | subvalue1"]
        result = chunk_json_dict(json_dict, key_sep=key_sep)
        self.assertEqual(result, expected)

    def test_value_sep(self):
        """test_value_sep

        Returns:

        """
        json_dict = {"key1": "value1"}
        value_sep = ": "
        expected = ["key1: value1"]
        result = chunk_json_dict(json_dict, value_sep=value_sep)
        self.assertEqual(result, expected)

    def test_three_chunks(self):
        """test_three_chunks

        Returns:

        """
        json_dict = {"key1": "a" * 400, "key2": "b" * 400, "key3": "c" * 1000}
        chunk_size = 1000
        result = chunk_json_dict(json_dict, chunk_size=chunk_size)
        self.assertEqual(len(result), 3)
        # Two first values fit together in one chunk
        self.assertLess(len(result[0]) + len(result[1]), chunk_size * 2)
        # The third value needs its own chunk
        self.assertIn("key3", result[2])

    def test_mix_large_small_text(self):
        """test_mix_large_small_text

        Returns:

        """
        json_dict = {"key1": "a" * 800, "key2": "bbbbb", "key3": "c" * 800}
        chunk_size = 500
        overlap = 100
        output = chunk_json_dict(
            json_dict, chunk_size=chunk_size, chunk_overlap=overlap
        )
        self.assertEqual(len(output), 4)
        # First large text in two chunks
        self.assertIn("key1", output[0])
        self.assertIn("key1", output[1])
        # Small text fits in same chunk
        self.assertIn("key2", output[1])
        # Second large text in two chunks
        self.assertIn("key3", output[2])
        self.assertIn("key3", output[3])

    def test_key_larger_than_window(self):
        """test_key_larger_than_window

        Returns:

        """
        json_dict = {"a" * 1200: "value"}
        chunk_size = 1000
        result = chunk_json_dict(json_dict, chunk_size=chunk_size)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], "value")

    def test_key_larger_than_window_and_other_key(self):
        """test_key_larger_than_window

        Returns:

        """
        json_dict = {"a" * 1200: "value1", "b": "value2"}
        chunk_size = 1000
        result = chunk_json_dict(json_dict, chunk_size=chunk_size)
        expected = ["value1 \n b | value2"]

        self.assertEqual(result, expected)


class TestBuildDocList(TestCase):

    def test_build_doc_list(self):
        """test_build_doc_list

        Returns:

        """
        document = MagicMock()
        document.content = "content"
        document.id = 1
        document.meta = {"data_id": 1, "data_pid": "pid", "title": "title"}
        document.score = 1.0
        documents = [document]
        doc_list = build_doc_list(documents)
        expected = [
            {
                "content": "content",
                "data_id": "1",
                "data_pid": "pid",
                "data_title": "title",
                "score": 1.0,
                "snippet_id": 1,
            }
        ]
        self.assertEqual(doc_list, expected)


class TestBuildDocDataList(TestCase):

    def test_build_doc_data_list(self):
        """test_build_doc_data_list

        Returns:

        """
        document = MagicMock()
        document.content = "content"
        document.id = 1
        document.title = "title"
        documents = [document]
        data_pids = {"1": "pid"}
        doc_list = build_doc_data_list(documents, data_pids)
        expected = [
            {
                "content": "content",
                "data_id": "1",
                "data_pid": "pid",
                "data_title": "title",
            }
        ]
        self.assertEqual(doc_list, expected)

    def test_build_doc_data_list_with_empty_list(self):
        """test_build_doc_data_list_with_empty_list

        Returns:

        """
        doc_list = build_doc_data_list([])
        self.assertEqual(doc_list, [])
