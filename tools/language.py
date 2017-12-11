# -*- coding: utf-8 -*-
from itertools import chain

from nltk.corpus import wordnet


def get_synonyms(word, pos):
    # pos values = {
    # ADJ, ADJ_SAT, ADV, NOUN or VERB.
    # }  # None = *
    synsets = wordnet.synsets(word, pos=pos)
    # lemmas = [w.lemmas() for w in synsets]
    all_lemma_names = set(chain.from_iterable([w.lemma_names() for w in synsets]))
    return all_lemma_names


print(get_synonyms('hello', None))
