from types import MappingProxyType
from typing import Literal, LiteralString, TypeAlias

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
