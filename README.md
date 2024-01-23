# NARC-NORNE-UD
Complete UD-based corpora merged with entity (NorNE) and coreference information (NARC). See the paper [here](https://arxiv.org/abs/2305.13527).

- Universal Dependencies
  - https://github.com/UniversalDependencies/UD_Norwegian-Bokmaal
  - https://github.com/UniversalDependencies/UD_Norwegian-Nynorsk
- NorNE - Norwegian Named Entities
  - https://github.com/ltgoslo/norne
- NARC - Norwegian Anaphora Resolution Corpus
  - https://github.com/ltgoslo/NARC


## Installation:

1. clone repo
2. cd `UD-NARC`
3. run `make`

- `make` consists of the following:
  1. `git submodule update --recursive --init`
  2. `python -m pip install -r requirements.txt`
  3. `python ud_narc/pipeline.py`

