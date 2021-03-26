from pathlib import Path
from collections import defaultdict
import pylexibank
from clldutils.misc import slug
import attr
from openpyxl import load_workbook


DATAFILE = "journal.pone.0128448.s001.xlsx"

# this is to fix cognates when cells with multiple forms have the incorrect
# number of cognates, e.g.
# na-mu/naŋ	1 -- this is split to two forms "na-mu" and "naŋ", but we don't know
# what cognate set 1 refers to without checking the data. This dictionary remaps
# these entries so that the cognate sets line up with the correct lexical forms
# so we have:
#   "na-mu/naŋ": "1 & #",
#  ...which means that "na-mu" is cognate set 1, while "naŋ" has no cognate

FIXED_COGNATES = {
    # tree
    "na-mu/naŋ": "1 & #",
    "na-mu/naŋ-gu": "1 & #",
    "na-mu/naŋ-kʰi": "1 & #",
    "naŋ-kʰi/na-mu": "# & 1",
    "na-mu/naŋ-gi": "1 & #",
    "naŋ-gu/na-mu": "# & 1",
    # below
    "mi-te/a-re": "1 & 2",  # typo in original?
    # hair
    "thǝ-ri/thǝ-rǝk": "2 & 2",
    # yawn
    "ha-pɨi-om/ha-ø-jom": "1 & 1",
    # sea
    "pa-da/pa-ral": "1 & 1",
    # old
    "jet/nət": "1 & 1",
}

@attr.s
class CustomConcept(pylexibank.Concept):
    Korean_Gloss = attr.ib(default=None)
    Number = attr.ib(default=None)



def read_data(filename):

    excel = load_workbook(filename, read_only=True)
    sheet = excel["Raw data"]

    for row_id, row in enumerate(sheet.rows):
        if row_id in (0, 2):
            continue  # skip these
        elif row_id == 1:
            # construct a lookup table of <word> -> col indexes
            # each word should have two indexes, the first will be the
            # lexeme, the second will be the cognate.
            words = defaultdict(list)
            for i, h in enumerate(row):
                if i == 0:
                    continue  # skip the language column
                words[h.value.strip()].append(i)
        elif row_id > 17:
            break  # no more data
        else:
            for word in words:
                lang = row[0].value.strip()
                gloss = row[words[word][0]]
                cognate = row[words[word][1]]

                if gloss.value.strip() == "#":
                    continue  # skip empty records

                src = None

                # Two hundred and forty six (246) basic vocabulary items [19,20] were extracted
                # from each of 14 living and one (1) ancient Koreanic variants using multiple
                # sources: (i) a large field collection made by Shimpei Ogura [21],
                # (ii) a modern dictionary of Koreanic variants that combine lexi- cons from
                # several different references [22], and (iii) an etymological glossary
                # of Middle Korean that contains lexicons sampled from over 240 historical
                # documents [23].
                #
                # -- Interpreting this as:
                #    - all Middle Korean are from r23:
                #          Nam K. Kyohak koe sacen (A Middle Korean dictionary). Seoul: Kyohaksa; 2014
                #    - all underlined forms in excel sheet are from r22:
                #          Nanmal ohwi chongbo chori yonguso. Urimal pangen sacen (A dictionary of Korean
                #          dialects). Seoul: Nanmal ohwi chongbo chori yonguso; 2010.
                #    - everything else is from r21
                #          Ogura S. Chosengo hogen no kenkyu (A study of Korean dialects). Tokyo:
                #          Iwanami Shoten; 1944.
                # Underlined items were extracted from Nanmal Ohwi Chongbo Chori Yonguso
                # Middle Korean was extracted from GW Nam's collection
                if lang == "Middle Korean":
                    src = "Nam2014"
                elif gloss.font.underline:
                    src = "Nanmal2010"
                else:
                    src = "Ogura1944"

                yield (lang, word, gloss.value.strip(), cognate.value, src)


class Dataset(pylexibank.Dataset):
    dir = Path(__file__).parent
    id = "leekoreanic"
    concept_class = CustomConcept

    # define the way in which forms should be handled
    form_spec = pylexibank.FormSpec(
        brackets={"(": ")"},  # characters that function as brackets
        separators=";/,",  # characters that split forms e.g. "a, b".
        missing_data=("?", "-", "#"),  # characters that denote missing data.
        strip_inside_brackets=True,  # do you want data removed in brackets or not?
    )

    def cmd_download(self, args):
        self.raw_dir.download("https://doi.org/10.1371/journal.pone.0128448.s001", DATAFILE)

    def cmd_makecldf(self, args):
        """
        Convert the raw data to a CLDF dataset.
        """
        args.writer.add_sources()

        
        concepts = {}
        for concept in self.conceptlists[0].concepts.values():
            idx = concept.number+'_'+slug(concept.english)
            args.writer.add_concept(ID=idx, Name=concept.english,
                    Concepticon_ID=concept.concepticon_id, 
                    Concepticon_Gloss=concept.concepticon_gloss,
                    Korean_Gloss=concept.attributes["korean"]
                    )
            concepts[concept.english] = idx

        languages = args.writer.add_languages(lookup_factory=lambda l: l["Name"])

        for lang, word, gloss, cognate, src in read_data(self.raw_dir / DATAFILE):
            lex = args.writer.add_forms_from_value(
                Language_ID=languages[lang], Parameter_ID=concepts[word], Value=gloss, Source=[src]
            )

            # sort out cognates
            cognate = FIXED_COGNATES.get(gloss, cognate)
            try:
                cognate = [c.strip() for c in cognate.split("&")]
            except AttributeError:
                cognate = [cognate]

            # handle the cases where a lexeme is given multiple cognates
            if len(lex) < len(cognate):
                cognate = [";".join(cognate)]
            else:
                cognate = [str(c) for c in cognate]

            for l, cog in zip(lex, cognate):
                if cog == "#":
                    continue
                for c in cog.split(";"):  # expand multiple cognates
                    args.writer.add_cognate(
                        lexeme=l,
                        Cognateset_ID="%s-%d" % (concepts[word], int(c)),
                        Source=["Lee2015"],
                    )
