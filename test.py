
def test_valid(cldf_dataset, cldf_logger):
    assert cldf_dataset.validate(log=cldf_logger)


# Two hundred and forty six (246) basic vocabulary items [19,20] were extracted from 
# each of 14 living and one (1) ancient Koreanic variants u

def test_forms(cldf_dataset, cldf_logger):
    assert len(list(cldf_dataset['FormTable'])) == 2365
    assert len([
        f for f in cldf_dataset['FormTable'] if f['Value'] == 'naŋ-kʰi'
    ]) == 2
    assert len([
        f for f in cldf_dataset['FormTable'] if f['Value'] == 'na-mu'
    ]) == 11


def test_languages(cldf_dataset, cldf_logger):
    assert len(list(cldf_dataset['LanguageTable'])) == 15


def test_sources(cldf_dataset, cldf_logger):
    assert len(cldf_dataset.sources) == 4


def test_parameters(cldf_dataset, cldf_logger):
    assert len(list(cldf_dataset['ParameterTable'])) == 246


# "The result was a 15 by 383 matrix"
def test_cognates(cldf_dataset, cldf_logger):
    cogsets = {c['Cognateset_ID'] for c in cldf_dataset['CognateTable']}
    assert len(cogsets) == 383
