# SPDX-FileCopyrightText: 2025 Jannik Schmitt <jannik.schmitt@deepsight.de>
#
# SPDX-License-Identifier: Apache-2.0
from re import Pattern

from limes.analyzers.de.barriers import GermanBarrier
from limes.analyzers.de.resources.regular_expressions import (
    ADJECTIVE_SUFFIXES,
    NEGATION_AFFIXES,
    NOUN_PROPERTY_SUFFIXES,
)
from limes.analyzers.de.resources.word_lists import (
    EDUCATIONAL_LANGUAGE,
    FOREIGN_WORDS,
    NEGATION_RULE_EXCEPTIONS,
)
from limes.analyzers.interfaces import BarrierAnalyzer, Lexicon
from limes.analyzers.models import DecomposedNegationCompound, Stem
from limes.models import Barrier
from limes.protocols import DocumentProtocol, TokenProtocol

_PARTICIPLE_TAGS = ["VAPP", "VMPP", "VVPP", "VERB"]


class GermanBarrierAnalyzer(BarrierAnalyzer):
    """
    A `BarrierAnalyzer` that is specific to the German language.

    Please note that this object is a Callable, and provides logic for
    automatically identifying and sequentially executing all Barrier detection
    functions, courtesy of its `BarrierAnalyzer` superclass.
    """

    def __init__(self, lexicon: Lexicon, simplify_explanations: bool = True):
        """
        Parameters
        ----------
        simplify_explanations : bool, optional
            If True, use simplified barrier descriptions; otherwise use
            standard descriptions. Defaults to True.
        """
        super().__init__(simplify_explanations=simplify_explanations)
        self._lexicon = lexicon

    @property
    def supported_barriers(self) -> list[Barrier]:
        """
        A list of all types of barriers that this analyzer can detect.
        """
        return [
            self._make_barrier(barrier.value, affected_tokens=None)
            for barrier in GermanBarrier
        ]

    def detect_foreign_phrases(
        self,
        sentence: DocumentProtocol,
    ) -> list[Barrier]:
        """
        Identify words that might be difficult to understand without being
        necessary.
        """
        foreign_words_instances = []
        for token in sentence:
            lemma = token.lemma_
            for phrase_length, phrases in FOREIGN_WORDS.items():
                if phrase_length == "1":
                    if lemma in phrases:
                        foreign_words_instances.append(
                            self._make_barrier(
                                GermanBarrier.FOREIGN_PHRASE.value,
                                affected_tokens=[token],
                            )
                        )
                    continue
                for phrase in phrases:
                    assert isinstance(phrase, list)
                    current_token = lemma
                    matching_tokens = []
                    for i, component in enumerate(phrase):
                        if component != current_token:
                            break
                        matching_tokens.append(sentence[token.i + i])
                        try:
                            current_token = sentence[token.i + i + 1].lemma_
                        except IndexError:
                            continue
                    if len(matching_tokens) == len(phrase):
                        foreign_words_instances.append(
                            self._make_barrier(
                                GermanBarrier.FOREIGN_PHRASE.value,
                                affected_tokens=matching_tokens,
                            )
                        )
        return foreign_words_instances

    def detect_educational_language_words(
        self,
        sentence: DocumentProtocol,
    ) -> list[Barrier]:
        """
        Identify verbs that are needlessly complicated.
        """
        educational_language_words = []
        for token in sentence:
            if token.pos_ not in ["VERB", "ADJ", "ADV"]:
                continue
            lemma = token.lemma_
            for disallowed_words in EDUCATIONAL_LANGUAGE.values():
                if lemma in disallowed_words:
                    educational_language_words.append(
                        self._make_barrier(
                            GermanBarrier.EDUCATIONAL_LANGUAGE.value,
                            affected_tokens=[token],
                        )
                    )
        return educational_language_words

    def _find_regex_matches(
        self,
        regex_list: list[Pattern],
        sentence: DocumentProtocol,
        compare_against_lemma: bool = True,
        valid_pos: list[str] | None = None,
        valid_deps: list[str] | None = None,
    ) -> list[TokenProtocol]:
        """
        Identify all tokens in the provided sentence for which a regular
        expression in the provided list creates a full match.
        """
        matches = []
        for token in sentence:
            if valid_pos and token.pos_ not in valid_pos:
                continue
            if valid_deps and token.dep_ not in valid_deps:
                continue
            if compare_against_lemma:
                text = token.lemma_
            else:
                text = token.text
            for regex in regex_list:
                if regex.fullmatch(text):
                    matches.append(token)
                    break
        return matches

    def detect_compound_adjective(
        self,
        sentence: DocumentProtocol,
    ) -> list[Barrier]:
        """
        Identify adjectives that contain meaning injected via suffix.
        """
        matches = self._find_regex_matches(
            ADJECTIVE_SUFFIXES, sentence, valid_pos=["ADV", "ADJ"]
        )
        barriers = [
            self._make_barrier(
                GermanBarrier.COMPOUND_ADJECTIVE.value,
                affected_tokens=[token],
            )
            for token in matches
        ]
        return barriers

    def detect_attribute_nouns(
        self,
        sentence: DocumentProtocol,
    ) -> list[Barrier]:
        """
        Identify nouns that encode attributes or processes. This is an indication for
        substantiation.
        """
        attribute_nouns = []
        for token in sentence:
            if token.pos_ != "NOUN":
                continue
            lemma = token.lemma_
            for suffix in NOUN_PROPERTY_SUFFIXES:
                if suffix.fullmatch(lemma):
                    attribute_nouns.append(
                        self._make_barrier(
                            GermanBarrier.ATTRIBUTE_NOUN.value,
                            affected_tokens=[token],
                        )
                    )
                    break
        return attribute_nouns

    def detect_collocational_verb_construct(
        self,
        sentence: DocumentProtocol,
    ) -> list[Barrier]:
        """
        Identify units of meaning that could be broken down into a single verb.
        """
        relevant_pos_tags = {"VERB", "ADP", "NOUN"}
        verb_constructs = []
        for token in sentence:
            if token.dep_ != "cvc":
                continue
            construct_components = [token]
            for ancestor in token.ancestors:
                if ancestor.pos_ in relevant_pos_tags:
                    construct_components.append(ancestor)
                    break
            for child in token.children:
                if child.pos_ in relevant_pos_tags:
                    construct_components.append(child)
                    break
            verb_constructs.append(
                self._make_barrier(
                    GermanBarrier.COLLOCATIONAL_VERB_CONSTRUCT.value,
                    affected_tokens=construct_components,
                )
            )
        return verb_constructs

    def detect_substitute_expression_for_modality(
        self,
        sentence: DocumentProtocol,
    ) -> list[Barrier]:
        """
        Identify phrases that use needlessly complex vocabulary instead of
        simple modal verbs.
        """
        potential_matches = []
        for token in sentence:
            match = None
            if token.pos_ != "VERB":
                continue
            if token.morph.get("VerbForm") != "Inf":
                match = self._detect_modal_phrase_kommen_in_betracht(token)
                if match:
                    potential_matches.append(match)
                    continue
            for detector in [
                self._detect_modal_phrase_in_der_lage,
                self._detect_modal_phrase_erlauben,
            ]:
                match = detector(token, sentence)
                if match:
                    potential_matches.append(match)
                    break
            if match:
                continue
            for detector in [
                self._detect_modal_phrase_lassen,
                self._detect_modal_phrase_sein_haben_zu,
            ]:
                match = detector(token)
                if match:
                    potential_matches.append(match)
                    break

        modal_phrases = []
        for match in potential_matches:
            match.sort()
            modal_phrases.append(
                self._make_barrier(
                    GermanBarrier.MODAL_PHRASE.value,
                    affected_tokens=[sentence[i] for i in match],
                )
            )
        return modal_phrases

    def _detect_modal_phrase_sein_haben_zu(
        self,
        token: TokenProtocol,
    ) -> list[int] | None:
        """
        Identify sequences that match a "sein + zu + Infinitiv" pattern.
        """
        particle_idx = None
        if "zu" not in str(token):
            for child in token.children:
                if child.lemma_ == "zu":
                    particle_idx = child.i
                    break
            if particle_idx is None:
                return None
        for ancestor in token.ancestors:
            if ancestor.lemma_ in ["sein", "haben"]:
                match = [ancestor.i]
                if particle_idx:
                    match.append(particle_idx)
                match.append(token.i)
                return match
        return None

    def _detect_modal_phrase_lassen(
        self,
        token: TokenProtocol,
    ) -> list[int] | None:
        """
        Identify sequences that match a "sich [Infinitiv] lassen" pattern.
        """
        match = []
        for ancestor in token.ancestors:
            if ancestor.lemma_ == "lassen":
                match.append(ancestor.i)
                break
        for child in token.children:
            if child.lemma_ == "sich":
                match.append(child.i)
                break
        if len(match) == 2:
            match.append(token.i)
            return match
        return None

    def _detect_modal_phrase_in_der_lage(
        self,
        token: TokenProtocol,
        sentence: DocumentProtocol,
    ) -> list[int] | None:
        """
        Identify sequences that match a "sich [Infinitiv] lassen" pattern.
        """
        match = []
        for ancestor in token.ancestors:
            if ancestor.lemma_ != "lage":
                continue
            if ancestor.i < 2:
                continue
            if sentence[ancestor.i - 1].lemma_ != "der":
                continue
            if sentence[ancestor.i - 2].lemma_ != "in":
                continue
            match += [ancestor.i - 2, ancestor.i - 1, ancestor.i]
            break
        if not match:
            return None
        if "zu" not in str(token):
            for child in token.children:
                if child.lemma_ == "zu":
                    match.append(child.i)
        match.append(token.i)
        return match

    def _detect_modal_phrase_erlauben(
        self,
        token: TokenProtocol,
        sentence: DocumentProtocol,
    ) -> list[int] | None:
        """
        Identify sequences that match a "sich [Infinitiv] lassen" pattern.
        """
        match = []
        particle_idx = None
        if "zu" not in str(token):
            for child in token.children:
                if child.lemma_ == "zu":
                    particle_idx = child.i
                    break
            if particle_idx is None:
                return None
        for ancestor in token.ancestors:
            if ancestor.lemma_ != "es":
                continue
            if ancestor.i < 1 or sentence[ancestor.i - 1].lemma_ != "erlauben":
                continue
            match = [ancestor.i - 1, ancestor.i]
            if particle_idx:
                match.append(particle_idx)
            match.append(token.i)
            return match
        return None

    def _detect_modal_phrase_kommen_in_betracht(
        self,
        token: TokenProtocol,
    ) -> list[int] | None:
        """
        Identify sequences that match a "sich [Infinitiv] lassen" pattern.
        """
        if token.lemma_ != "kommen":
            return None
        match = None
        for child in token.children:
            if child.lemma_ != "in":
                continue
            for grandchild in child.children:
                if grandchild.lemma_ == "betracht":
                    match = [child.i, grandchild.i, token.i]
                    break
        return match

    def detect_decomposed_verbs(
        self,
        sentence: DocumentProtocol,
    ) -> list[Barrier]:
        """
        Identify verbs that are decomposed into two tokens. An example: the verb
        'einkaufen' might be decomposed into 'kaufe ein'.

        Parameters
        ----------
        sentence : DocumentProtocol
            The sentence to be analyzed.

        Returns
        -------
        A list of Barrier objects, each representing a single decomposed verb.
        Each decomposed verb consists of two parts.
        """
        decomposed_verbs = []
        for token in sentence:
            for child in token.children:
                if child.dep_ != "svp":
                    continue
                decomposed_verbs.append(
                    self._make_barrier(
                        GermanBarrier.DECOMPOSED_VERB.value,
                        affected_tokens=[token, child],
                    )
                )
        return decomposed_verbs

    def detect_passive_voice(
        self,
        sentence: DocumentProtocol,
    ) -> list[Barrier]:
        """
        Identify word couples that make up passive-voice phrasings.

        Parameters
        ----------
        sentence : DocumentProtocol
            The sentence to be analyzed.

        Returns
        -------
        A list of Barrier objects, each representing a single passive-voice
        structure (which always consists of two tokens).
        """
        passive_voice_instances = []
        for token in sentence:
            # Base token needs to have a "clause"-like dependency or be root of
            # the sentence.
            if (
                not (
                    str(token.dep_).endswith("c") and len(str(token.dep_)) == 2
                )
                and token.dep_ != "ROOT"
                and token.pos_ != "AUX"
            ):
                continue
            # Base token needs to be a conjugated form of "werden".
            if token.lemma_ != "werden":
                continue
            # If base conditions are met for given token, check if token has
            # participle child.
            for child in token.children:
                if child.fine_pos in _PARTICIPLE_TAGS:
                    passive_voice_instances.append(
                        self._make_barrier(
                            GermanBarrier.PASSIVE_VOICE.value,
                            affected_tokens=[token, child],
                        )
                    )
        return passive_voice_instances

    def detect_negation(
        self,
        sentence: DocumentProtocol,
    ) -> list[Barrier]:
        """
        Identify cases where words contain a suffix that implies the meaning of
        the word is negated.
        """
        barriers: list[Barrier] = []
        for token in sentence:
            # Only nouns and adjectives may appear negated by affix.
            if token.pos_ == "NOUN":
                pos = "NOUN"
            # We fold adverbs into adjectives because they are functionally
            # similar for these purposes.
            elif token.pos_ in ["ADJ", "ADV"]:
                pos = "ADJ"
            else:
                continue

            # Attempt to decompose the token.
            decomp_comp = self._decompose_negation_compound(token)
            if decomp_comp is None:
                continue

            # Rule out false positives by comparing to a list of knonw issues.
            if (
                token.lemma_
                in NEGATION_RULE_EXCEPTIONS[decomp_comp.type][
                    decomp_comp.affix
                ][pos]
            ):
                continue

            double_negative = self._detect_double_negative(
                token=token,
                sentence=sentence,
            )
            # Double negatives are barriers regardless of lexicalization.
            if double_negative:
                barriers.append(double_negative)
                continue

            # If the token is a stand-alone negative compound, only consider it
            # a barrier if it is not lexicalized.
            if not self._negative_is_lexicalized(
                negative=token.lemma_,
                positive=decomp_comp.stem,
            ):
                barriers.append(
                    self._make_barrier(
                        GermanBarrier.NEGATION_AFFIX.value,
                        affected_tokens=[token],
                    )
                )

        return barriers

    def _decompose_negation_compound(
        self,
        token: TokenProtocol,
    ) -> DecomposedNegationCompound | None:
        """
        Break up a token into affix and stem and categorize the type of affix.
        If the token does not contain any relevant affix, returns None.
        """
        lemma = token.lemma_
        for affix_type, regex_list in NEGATION_AFFIXES.items():
            for regex in regex_list:
                match = regex.fullmatch(lemma)
                if match is None:
                    continue

                stem_str = match.group("stem")
                # If token is noun, the stem of negation compound should also
                # be a noun and therefore capitalized in German.
                # Compound negatives driven by suffixes are often subject to word class
                # changes (e.g. "Zucker" -> "zuckerfrei"); that is why we are looking
                # for capitalized words in this case.
                if token.pos_ == "NOUN" or affix_type == "suffix":
                    stem_str = stem_str.capitalize()

                stem_freq = self._lexicon.get_frequency(stem_str)
                # Stems with no frequency information are not lexicalized and
                # therefore not candidates for negation compounds with the given
                # suffix.
                if stem_freq is None:
                    continue

                return DecomposedNegationCompound(
                    stem=Stem(
                        string=stem_str,
                        freq=stem_freq,
                    ),
                    affix=match.group("affix"),
                    type=affix_type,
                )
        return None

    def _negative_is_lexicalized(
        self,
        negative: str,
        positive: Stem,
        threshold: float = 0.5,
    ) -> bool | None:
        """
        Check whether we can assume lexicalization of the negative based on the
        size of the frequency delta. If the positive is not contained in the
        lexicon, return None.
        """
        freq_neg = self._lexicon.get_frequency(negative)

        # If lexicon doesn't know the negative, we assume it is not lexicalized.
        if freq_neg is None:
            return False

        return freq_neg > threshold * positive.freq

    def _detect_double_negative(
        self,
        token: TokenProtocol,
        sentence: DocumentProtocol,
    ) -> Barrier | None:
        """
        Identify whether a given compound negation is preceeded by a negative,
        implying a double negative. This function assumes that the given token
        is a compound negative.
        """
        # Check left neighbor for negative.
        if token.i > 0:
            neighbor = sentence[token.i - 1]
            if neighbor.lemma_ in ["nicht", "kein", "ohne"]:
                return self._make_barrier(
                    GermanBarrier.DOUBLE_NEGATION.value,
                    affected_tokens=[neighbor, token],
                )
        return None

    def detect_long_sentence(
        self,
        sentence: DocumentProtocol,
    ) -> list[Barrier]:
        """
        Identify sentences that are too long.
        """
        words = [t for t in sentence if t.pos_ != "PUNCT"]
        if len(words) >= 15:
            return [
                self._make_barrier(
                    GermanBarrier.LONG_SENTENCE.value,
                    affected_tokens=words,
                )
            ]
        return []

    def detect_numeral_words(
        self,
        sentence: DocumentProtocol,
    ) -> list[Barrier]:
        """
        Identify whether a given token is a numeral word (e.g. "sechs" rather
        than "6").
        """
        numeral_words = []
        for token in sentence:
            if token.pos_ != "NUM":
                continue
            text = token.text
            if any(char.isdigit() for char in text):
                continue
            if not any(char.isalpha() for char in text):
                continue
            numeral_words.append(
                self._make_barrier(
                    GermanBarrier.NUMERAL_WORD.value,
                    affected_tokens=[token],
                )
            )
        return numeral_words
