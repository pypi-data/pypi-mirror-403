from enum import StrEnum
from types import MappingProxyType
from typing import Literal, LiteralString, NotRequired, TypeAlias, TypedDict

Word: TypeAlias = LiteralString


RelatedWordCode = Literal[
    "nouns_adjective",
    "adjectives_noun",
    "synonyms",
    "triggers",
    "antonyms",
    "hypernyms",
    "hyponyms",
    "holonyms",
    "meronyms",
    "frequent_followers",
    "frequent_predecessors",
    "homophones",
    "consonant",
]


_lookup_related_code = MappingProxyType(
    {
        "nouns_adjective": "jja",
        "adjectives_noun": "jjb",
        "synonyms": "syn",
        "triggers": "trg",
        "antonyms": "ant",
        "hypernyms": "spc",
        "hyponyms": "gen",
        "holonyms": "com",
        "meronyms": "par",
        "frequent_followers": "bga",
        "frequent_predecessors": "bgb",
        "homophones": "hom",
        "consonant": "cns",
    }
)


MetadataFlag = Literal[
    "definitions",
    "parts_of_speech",
    "syllable_count",
]


_lookup_metadata_flag = MappingProxyType(
    {
        "definitions": "d",
        "parts_of_speech": "p",
        "syllable_count": "s",
    }
)


class WordRelation(StrEnum):
    """
    When paired with a `Word`, the `Word` will be in a predefined lexical relation.
    """

    nouns_adjective = "jja"
    adjectives_noun = "jjb"
    synonyms = "syn"
    triggers = "trg"
    antonyms = "ant"
    hypernyms = "spc"
    hyponyms = "gen"
    holonyms = "com"
    meronyms = "par"
    frequent_followers = "bga"
    frequent_predecessors = "bgb"
    homophones = "hom"
    consonant = "cns"


class WordMetadata(StrEnum):
    """
    Extra lexical knowledge for a `Word`
    """

    definitions = "d"
    parts_of_speech = "p"
    syllable_count = "s"


class WordObject(TypedDict):
    """
    Representation of a word from the Datamuse API
    """

    word: Word
    defs: NotRequired[list[str]]
    tags: NotRequired[list[str]]
    numSyllables: NotRequired[int]


WordArray: TypeAlias = list[WordObject]
