import functools
from typing import final

import certifi
import urllib3

from datamuse.annotations import RelatedWordCode, Word, _lookup_related_code


@final
class Datamuse:
    """
    The [Datamuse](https://www.datamuse.com/) [API](https://www.datamuse.com/api/) is a word-finding query engine for developers.

    You can use it in your apps to find words that match a given set of constraints and that are likely in a given context.
    You can specify a wide variety of constraints on meaning, spelling, sound, and vocabulary in your queries, in any combination.
    """

    __API_URL = "api.datamuse.com"
    __slots__ = ("__pool",)

    def __init__(self) -> None:
        self.__pool = urllib3.HTTPSConnectionPool(
            host=self.__API_URL,
            port=443,
            cert_reqs="CERT_REQUIRED",
            ca_certs=certifi.where(),
        )

    @functools.lru_cache
    def __get_words(self, **kwds: Word | RelatedWordCode) -> list[Word]:
        response = self.__pool.request(method="GET", url="/words", fields=kwds)
        return [word["word"] for word in response.json()]

    @functools.lru_cache
    def __get_suggestions(self, **kwds: Word | RelatedWordCode) -> list[Word]:
        response = self.__pool.request(method="GET", url="/sug", fields=kwds)
        return [word["word"] for word in response.json()]

    def synonyms(self, ml: Word):
        """
        words with a meaning similar to `ml`

        :param ml: means like
        """
        return self.__get_words(ml=ml)

    def associations(self, ml: Word, start: Word = "*", end: Word = "*"):
        """
        words related to `ml`

        :param ml: means like
        :param start: start with
        :param end: end in
        """
        return self.__get_words(ml=ml, sp=start + end)

    def homophones(self, sl: Word):
        """
        words that sound like `sl`

        :param sl: sounds like
        """
        return self.__get_words(sl=sl)

    def pattern(self, start: Word, end: Word, letters: int):
        """
        words that start with `start`, end in `end`, and have `letters` in between

        :param start: start with
        :param end: end in
        :param letters: letters in between
        """
        return self.__get_words(sp=f"{start[0]}{'?' * letters}{end[0]}")

    def orthographic_neighbours(self, sp: Word):
        """
        words that are spelled similarly to `sp`

        :param sp: spelled like
        """
        return self.__get_words(sp=sp)

    def related(self, word: Word, rel: RelatedWordCode):
        """
        words that are related by `rel`

        :param word: the word
        :param rel: related word
        """
        return self.__get_words(**{f"rel_{_lookup_related_code[rel]}": word})

    def suggestions(self, s: Word):
        """
        sugesstions from prefix hint string `s`

        :param s: prefix hint string
        """
        return self.__get_suggestions(s=s)
