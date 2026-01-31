# SPDX-FileCopyrightText: 2025 Jannik Schmitt <jannik.schmitt@deepsight.de>
#
# SPDX-License-Identifier: Apache-2.0
"""Barrier templates for supported Barriers."""

from enum import Enum

from limes.models import (
    BarrierCategorization,
    BarrierDescriptionStyle,
    BarrierTemplate,
)


class GermanBarrierCategory(BarrierCategorization):
    """The category to which a barrier belongs."""

    HIGH_LANGUAGE_LEVEL = "Hohes sprachliches Niveau"
    COMPLEX_VERB_CONSTRUCT = "Komplexe Verb-Konstruktion"
    NEGATION = "Verneinung"
    SENTENCE_STRUCTURE = "Satzbau"
    INFORMATION_STRUCTURE = "Informationsstruktur"
    COMPOUNDS = "Komposita"
    WORD_CHOICE = "Wortwahl"


class GermanBarrier(Enum):
    # Category: High Language Level
    FOREIGN_PHRASE = BarrierTemplate(
        title="Fremdwort(-phrase)",
        category=GermanBarrierCategory.HIGH_LANGUAGE_LEVEL,
        descriptions={
            BarrierDescriptionStyle.STANDARD: (
                "Ein Lehnwort, das aus anderen Sprachen übernommen wurde aber "
                "noch so unangepasst ist, dass es als fremd empfunden wird."
            ),
            BarrierDescriptionStyle.SIMPLIFIED: (
                "Ein Wort, das aus einer anderen Sprache kommt und "
                "möglicherweise nicht verstanden wird."
            ),
        },
        suggested_improvement="Ein anderes Wort mit gleicher Bedeutung finden.",
    )
    EDUCATIONAL_LANGUAGE = BarrierTemplate(
        title="Bildungssprachlicher Ausdruck",
        category=GermanBarrierCategory.HIGH_LANGUAGE_LEVEL,
        descriptions={
            BarrierDescriptionStyle.STANDARD: (
                "Ein Wort/mehrere Wörter, das/die in der gegebenen Form selten "
                "in der Alltagssprache vorkommt/vorkommen."
            ),
            BarrierDescriptionStyle.SIMPLIFIED: (
                "Wörter, die im Alltag selten benutzt werden."
            ),
        },
        suggested_improvement=(
            "Ein anderes Wort bzw. einen anderen Ausdruck mit gleicher "
            "Bedeutung finden."
        ),
    )
    COMPOUND_ADJECTIVE = BarrierTemplate(
        title="Zusammengesetztes Adjektiv",
        category=GermanBarrierCategory.HIGH_LANGUAGE_LEVEL,
        descriptions={
            BarrierDescriptionStyle.STANDARD: (
                "Ein Adjektiv aus zwei Teilen, dessen Gesamtbedeutung "
                "basierend auf den Teilen erst ermittelt werden muss. Das "
                "belastet das Arbeitsgedächtnis."
            ),
            BarrierDescriptionStyle.SIMPLIFIED: (
                "Ein zusammengesetztes Adjektiv, das man erst auseinandernehmen "
                "muss, um es zu verstehen."
            ),
        },
        suggested_improvement=(
            "Die Einzelwörter des zusammengesetzten Adjektivs in eine "
            "Wortgruppe (z.B. zwei einzelne Wörter) oder einen Satz überführen."
        ),
    )
    ATTRIBUTE_NOUN = BarrierTemplate(
        title="Eigenschafts-Substantiv",
        category=GermanBarrierCategory.HIGH_LANGUAGE_LEVEL,
        descriptions={
            BarrierDescriptionStyle.STANDARD: (
                "Ein Substantiv, das eine Eigenschaft oder einen Vorgang "
                "bezeichnet."
            ),
            BarrierDescriptionStyle.SIMPLIFIED: (
                "Ein Substantiv, das eigentlich eine Eigenschaft oder "
                "Handlung meint."
            ),
        },
        suggested_improvement=(
            "Sie stellen nicht immer eine Barriere dar, bei längeren "
            "Substantiven sollte man aber prüfen, ob eine Vereinfachung durch "
            "Rückführung auf das eigentliche Adjektiv möglich ist."
        ),
    )
    COLLOCATIONAL_VERB_CONSTRUCT = BarrierTemplate(
        title="Funktionsverbgefüge",
        category=GermanBarrierCategory.HIGH_LANGUAGE_LEVEL,
        descriptions={
            BarrierDescriptionStyle.STANDARD: (
                "Eine Phrase, bei der die Bedeutung vom Verb auf das "
                "Substantiv ausgelagert wurde und bei der das Verb nicht mit "
                "seiner alltäglichen Bedeutung verstanden werden darf."
            ),
            BarrierDescriptionStyle.SIMPLIFIED: (
                "Eine feste Formulierung aus Verb und Substantiv, bei der das "
                "Verb kaum eigene Bedeutung hat."
            ),
        },
        suggested_improvement=(
            "Die Phrase kann oft durch ein einfaches Verb ersetzt werden."
        ),
    )
    MODAL_PHRASE = BarrierTemplate(
        title="Ersatzausdruck für Modalverb",
        category=GermanBarrierCategory.HIGH_LANGUAGE_LEVEL,
        descriptions={
            BarrierDescriptionStyle.STANDARD: (
                "Ein Satzbaustein, der eine Modalität mit einer längeren "
                "Phrase ausdrückt, obwohl ein einziges Wort besser "
                "verstanden wird."
            ),
            BarrierDescriptionStyle.SIMPLIFIED: (
                "Eine umständliche Formulierung für Möglichkeiten oder "
                "Pflichten, obwohl ein kurzes Modalverb genügt."
            ),
        },
        suggested_improvement=(
            "Ersetzen durch einfache Modalverben ('können', 'müssen', 'sollen',"
            " 'dürfen', 'mögen', 'möchten')."
        ),
    )
    # Category: Complex Verb Construct
    DECOMPOSED_VERB = BarrierTemplate(
        title="Unfestes Verb",
        category=GermanBarrierCategory.COMPLEX_VERB_CONSTRUCT,
        descriptions={
            BarrierDescriptionStyle.STANDARD: (
                "Ein Verb, das in zwei Teile aufgespaltet wurde. Der eine Teil "
                "ist ein Verb, das oft auch alleine verwendet werden kann und "
                "dann eine andere Bedeutung hat. Je mehr Wörter zwischen den "
                "zwei Teilen liegen, desto mehr wird das Arbeitsgedächtnis "
                "belastet."
            ),
            BarrierDescriptionStyle.SIMPLIFIED: (
                "Ein Verb, das in zwei Teile aufgespaltet wurde. Der eine Teil "
                "ist ein Verb, das oft auch alleine verwendet werden kann und "
                "dann eine andere Bedeutung hat. Je mehr Wörter zwischen den "
                "zwei Teilen liegen, desto mehr wird das Arbeitsgedächtnis "
                "belastet."
            ),
        },
        suggested_improvement=(
            "Unfestes Verb in einem Nebensatz zusammenführen oder mit einem "
            "anderen Verb ausdrücken."
        ),
    )
    PASSIVE_VOICE = BarrierTemplate(
        title="Passivstruktur",
        category=GermanBarrierCategory.COMPLEX_VERB_CONSTRUCT,
        descriptions={
            BarrierDescriptionStyle.STANDARD: (
                "Das Vollverb tritt in partizipierter Form mit einer "
                "konjugierten Form von 'werden' oder 'sein' auf. Je größer die "
                "Distanz zwischen den beiden Komponenten, desto negativer "
                "wirkt sich die Passiv-Struktur auf die Lesbarkeit des Textes "
                "aus."
            ),
            BarrierDescriptionStyle.SIMPLIFIED: (
                "Beim Passiv fehlt die handelnde Person, was das Verstehen "
                "erschwert. Fachsprachlich ist dies durchaus üblich und wird "
                "auch verstanden. Außerhalb des fachsprachlichen Kontextes "
                "(z.B. in Situationsbeschreibungen) sollten Passiv-Phrasen "
                "vermieden werden."
            ),
        },
        suggested_improvement=(
            "Handelnde Person einfügen oder zumindest ein 'man'."
        ),
    )
    # Category: Negation
    NEGATION_AFFIX = BarrierTemplate(
        title="Verneinung durch Vor- oder Nachsilbe",
        category=GermanBarrierCategory.NEGATION,
        descriptions={
            BarrierDescriptionStyle.STANDARD: (
                "Das Wort muss erst morphologisch in das eigentliche Morphem "
                "sowie das Verneinungs-Affix aufgebrochen werden, bevor die "
                "Bedeutung des Wortes verarbeitet werden kann."
            ),
            BarrierDescriptionStyle.SIMPLIFIED: (
                "Eine Verneinung steckt als Vor- oder Nachsilbe im Wort, was "
                "das Wort als Ganzes schwerer verständlich macht."
            ),
        },
        suggested_improvement=(
            "Verneinung als eigenes Wort darstellen (z.B. 'ohne Farbstoff' "
            "statt 'farbstofffrei')."
        ),
    )
    DOUBLE_NEGATION = BarrierTemplate(
        title="Doppelte Verneinung",
        category=GermanBarrierCategory.NEGATION,
        descriptions={
            BarrierDescriptionStyle.STANDARD: (
                "Zwei Verneinungen heben sich gegenseitig auf."
            ),
            BarrierDescriptionStyle.SIMPLIFIED: (
                "Zwei Verneinungen heben sich gegenseitig auf."
            ),
        },
        suggested_improvement=(
            "Umformen vom doppelten Negativ ins Positiv (z.B. 'mit Wasser' "
            "statt 'nicht ohne Wasser')."
        ),
    )
    # Category: Sentence Structure
    LONG_SENTENCE = BarrierTemplate(
        title="Langer Satz",
        category=GermanBarrierCategory.SENTENCE_STRUCTURE,
        descriptions={
            BarrierDescriptionStyle.STANDARD: (
                "Lange Sätze sind schwieriger zu verstehen als kurze Sätze. "
                "Ausnahme sind einfache Aufzählungen."
            ),
            BarrierDescriptionStyle.SIMPLIFIED: (
                "Lange Sätze sind schwieriger zu verstehen als kurze Sätze. "
                "Ausnahme sind einfache Aufzählungen."
            ),
        },
        suggested_improvement=(
            "Versuchen, maximal 15 Wörter (per DIN Norm 8281-1) pro Satz zu "
            "verwenden. Oft kann man lange Sätze auch in mehrere kurze Sätze "
            "zerlegen."
        ),
    )
    NUMERAL_WORD = BarrierTemplate(
        title="Zahlwort",
        category=GermanBarrierCategory.WORD_CHOICE,
        descriptions={
            BarrierDescriptionStyle.STANDARD: (
                "Ausgeschriebene Zahlen brechen den Lesefluss."
            ),
            BarrierDescriptionStyle.SIMPLIFIED: (
                "Ausgeschriebene Zahlen brechen den Lesefluss."
            ),
        },
        suggested_improvement="Zahlen als Ziffern schreiben.",
    )
