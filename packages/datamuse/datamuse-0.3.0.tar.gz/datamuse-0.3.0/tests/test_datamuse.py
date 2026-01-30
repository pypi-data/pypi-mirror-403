import pytest

from datamuse.annotations import _lookup_metadata_flag, _lookup_related_code


class TestDatamuse:
    def test_synonyms(self, word_mock, datamuse_mock):
        mock = datamuse_mock(
            method="GET",
            url="/words",
            response=[{"word": word_mock}],
            match_query={"ml": word_mock},
        )
        synonyms = mock.synonyms(word_mock)
        assert word_mock in synonyms

    @pytest.mark.parametrize("start, end", [("", ""), ("s", "e")])
    def test_associations(self, word_mock, datamuse_mock, start, end):
        mock = datamuse_mock(
            method="GET",
            url="/words",
            response=[{"word": word_mock}],
            match_query={"ml": word_mock, "sp": start + end},
        )
        associations = mock.associations(word_mock, start, end)
        assert word_mock in associations

    def test_homophones(self, word_mock, datamuse_mock):
        mock = datamuse_mock(
            method="GET",
            url="/words",
            response=[{"word": word_mock}],
            match_query={"sl": word_mock},
        )
        homopohones = mock.homophones(word_mock)
        assert word_mock in homopohones

    def test_pattern(self, words_mock, datamuse_mock):
        start, end = words_mock(2)
        mock = datamuse_mock(
            method="GET",
            url="/words",
            response=[{"word": start}, {"word": end}],
            match_query={"sp": start[0] + "?" * 2 + end[0]},
        )
        pattern = mock.pattern(start, end, 2)
        assert start in pattern
        assert end in pattern

    def test_orthographic_neighbours(self, word_mock, datamuse_mock):
        mock = datamuse_mock(
            method="GET",
            url="/words",
            response=[{"word": word_mock}],
            match_query={"sp": word_mock},
        )
        homopohones = mock.orthographic_neighbours(word_mock)
        assert word_mock in homopohones

    def test_suggestions(self, words_mock, datamuse_mock):
        words = words_mock(10)
        search_prefix = words[0]

        mock = datamuse_mock(
            method="GET",
            url="/sug",
            response=[{"word": word} for word in words],
            match_query={"s": search_prefix},
        )
        suggestions = mock.suggestions(search_prefix)
        assert suggestions == words

    @pytest.mark.parametrize(
        "parameter, code",
        [(parameter, code) for parameter, code in _lookup_related_code.items()],
    )
    def test_related(self, datamuse_mock, word_mock, parameter, code):
        mock = datamuse_mock(
            method="GET",
            url="/words",
            response=[{"word": word_mock}],
            match_query={f"rel_{code}": word_mock},
        )
        related = mock.related(word_mock, parameter)
        assert word_mock in related

    @pytest.mark.parametrize("flag", _lookup_metadata_flag)
    def test_with_metadata_words(self, datamuse_mock, word_mock, flag):
        mock = datamuse_mock(
            method="GET",
            url="/words",
            response=[
                {
                    "word": word_mock,
                    "tags": ["u", "n", "v", "adj", "adv"],
                    "defs": [word_mock],
                    "numSyllables": len(word_mock),
                }
            ],
            match_query={"ml": word_mock, "md": f"{_lookup_metadata_flag[flag]}"},
        )
        synonyms = mock.with_metadata(flag).synonyms(word_mock)
        assert word_mock in synonyms
        assert word_mock in mock.metadata
        assert flag in mock.metadata[word_mock]
