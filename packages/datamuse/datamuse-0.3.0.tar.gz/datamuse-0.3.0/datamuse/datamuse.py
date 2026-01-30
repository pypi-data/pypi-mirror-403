import functools
from types import MappingProxyType
from typing import Any, final

import certifi
import urllib3

from datamuse.annotations import (
    MetadataFlag,
    RelatedWordCode,
    Word,
    WordArray,
    WordObject,
    _lookup_metadata_flag,
    _lookup_related_code,
)


@final
class Datamuse:
    """
    The [Datamuse API](https://www.datamuse.com/api/) is a word-finding query engine for developers.

    Use it in your apps to find words that match a given set of constraints and that are likely in a given context.
    Specify a wide variety of constraints on meaning, spelling, sound, and vocabulary in your queries, in any combination.
    """

    __API_URL = "api.datamuse.com"
    __slots__ = ("__pool", "__metadata_flags", "__metadata", "_metadata")

    def __init__(self) -> None:
        self.__pool = urllib3.HTTPSConnectionPool(
            host=self.__API_URL,
            port=443,
            cert_reqs="CERT_REQUIRED",
            ca_certs=certifi.where(),
        )
        self.__metadata_flags: dict[str, str] = {}
        self.__metadata: dict[str, dict[str, Any]] = {}
        self._metadata = MappingProxyType(self.__metadata)

    @property
    def metadata(self):
        """
        A mapping of a word to its metadata.
        """
        return self._metadata

    def _get_words(self, **kwds: Word):
        parsed = self.__get("/words", **kwds, **self.__metadata_flags)
        self.__metadata_flags.clear()
        return parsed

    def _get_suggestions(self, **kwds: Word):
        parsed = self.__get("/sug", **kwds, **self.__metadata_flags)
        self.__metadata_flags.clear()
        return parsed

    @functools.lru_cache
    def __get(self, url: str, **kwds: Word) -> list[Word]:
        json_response = self.__pool.request(method="GET", url=url, fields=kwds).json()
        words = self._make_metadata(json_response)
        return words or [obj["word"] for obj in json_response]

    def _make_metadata(self, json_response: WordArray) -> list[Word]:
        """
        Builds a `metadata` dict by parsing the JSON Reponse, returing a flattened list of string.

        The `metadata` is updated per parsing.
        The keys may not be same across parsing since it depends on the
        metdata flags with which the API call was made.

        :param json_response: The json response from the datamuse api
        :type json_response: WordArray
        :return: A flattened list of string
        :rtype: list[Word]
        """
        words = []

        if self.__metadata_flags:
            flags = self.__metadata_flags["md"]

            for obj in json_response:
                word = obj["word"]
                words.append(word)

                if word not in self.__metadata:
                    self.__metadata[word] = {}

                for f in flags:
                    match f:
                        case "d":
                            self._make_definitions(obj)
                        case "p":
                            self._make_parts_of_speech(obj)
                        case "s":
                            self._make_syllable_count(obj)
                        case "_":  # pragma: no cover
                            # TODO: support remaining documenetd metadata flags
                            continue
        return words

    def _make_definitions(self, obj: WordObject, /):
        # TODO: what is the `defHeadWord` in api response?
        self.__metadata[obj["word"]].update(
            definitions=list(map(str.expandtabs, obj.get("defs", [])))
        )

    def _make_syllable_count(self, obj: WordObject, /):
        self.__metadata[obj["word"]].update(syllable_count=obj.get("numSyllables", 0))

    def _make_parts_of_speech(self, obj: WordObject, /):
        self.__metadata[obj["word"]].update(parts_of_speech=[])
        for t in obj.get("tags", []):
            match t:
                case "n":
                    self.__metadata[obj["word"]]["parts_of_speech"].append("noun")
                case "v":
                    self.__metadata[obj["word"]]["parts_of_speech"].append("verb")
                case "adj":
                    self.__metadata[obj["word"]]["parts_of_speech"].append("adjective")
                case "adv":
                    self.__metadata[obj["word"]]["parts_of_speech"].append("adverb")
                case _:
                    pass

    def synonyms(self, ml: Word):
        """
        words with a meaning similar to `ml`

        :param ml: means like
        """
        return self._get_words(ml=ml)

    def associations(self, ml: Word, start: Word = "*", end: Word = "*"):
        """
        words related to `ml`

        :param ml: means like
        :param start: start with
        :param end: end in
        """
        return self._get_words(ml=ml, sp=start + end)

    def homophones(self, sl: Word):
        """
        words that sound like `sl`

        :param sl: sounds like
        """
        return self._get_words(sl=sl)

    def pattern(self, start: Word, end: Word, letters: int):
        """
        words that start with `start`, end in `end`, and have `letters` in between

        :param start: start with
        :param end: end in
        :param letters: letters in between
        """
        return self._get_words(sp=f"{start[0]}{'?' * letters}{end[0]}")

    def orthographic_neighbours(self, sp: Word):
        """
        words that are spelled similarly to `sp`

        :param sp: spelled like
        """
        return self._get_words(sp=sp)

    def related(self, word: Word, rel: RelatedWordCode):
        """
        words that are related by `rel`

        :param word: the word
        :param rel: related word
        """
        return self._get_words(**{f"rel_{_lookup_related_code[rel]}": word})  # pyright: ignore[reportArgumentType]

    def suggestions(self, s: Word):
        """
        sugesstions from prefix hint string `s`

        :param s: prefix hint string
        """
        return self._get_suggestions(s=s)

    def with_metadata(self, *md: MetadataFlag):
        """
        Include extra lexical knowledge for a `Word`.

        Accessible through the `metadata` property.

        :param md: the metadata
        """
        self.__metadata_flags.update(
            md="".join({_lookup_metadata_flag[meta] for meta in md})
        )
        return self
