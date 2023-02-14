# Feb 8
NARC: new way of mapping UD and NARC
- the original approach seemed to contain several bugs
    - sentence ord for NARC documents wasn't taken into account which resulted in unnecessary gaps
    - disambiguation of multiple mappings worked only for sentences that were not first or last in the document
    - STEP 6 dod work as expected
    - in general, documents with gaps were kept, which may be problematic as their cohesion can be damaged
- the new approach still goes through UD files and tries to find a mapping of UD sentences to sentences in NARC documents
    - it is more conservative in mapping
    - if a UD sentence starts a NARC document, it expects the following sentences to belong to the same document at the same positions
    - if there is a UD sentence, which has been left out from the NARC doc, it can skip it continue with the rest of the document
    - if a UD sentence is found in more than one document, it uses lookeahead to disambiguate
    - it can jump to a new NARC document even if the previous one has not been finished (there are remaining sentences) if the current UD sentence appears as first in the new document
        - some of the NARC documents contained a few additional sentences that were probably left out for UD
        - however, there are several cases, where a NARC document is split between dev/test or train/dev
        - we want to avoid such documents for the time being => using SKIP_DOCS
        - there is a Nynorsk document that starts with the sentence "Ja." and if this sentence is omitted in a NARC document, it switches to that "Ja." document as it's the first sentence
        - this is an unwanted behaviour that we fixed by manually skipping those UD sentences => using SKIP_SENT_ID
    - a few sentences differ in one word
        - for the time being, the complete documents containing such sentences are filtered out => using SKIP_DOCS
    - for a few cases in Nynorsk, the lookahead for disambiguation fails with no document to choose from
        - for the time being, the complete documents containing such sentences are filtered out => using SKIP_DOCS
- TODO: a better approach would probably be to iterate over NARC documents and search for mappings into the UD files

# Feb 11
Punctuation reworking in `json_to_conll`

# Feb 12
NARC: a better way to map NARC sents to UD parses
- goes over NARC documents
- removes NARC documents that contain a sentence for which there is no parse
- unique parses are aligned immediately
- if there are multiple parses for a single sentence (which may possibly appear several times in NARC)
    - assign a distance score to every sentence-parse candidate pair
    - distance score is based on already aligned sentences from the context and their UD sentids
    - find a minimum weight matching in the bipartite graph formed by sents and the corresponding parses
- so far, it never happens that there remain sents without any sentids assigned (checking by assert)
- in the end, delete the documents that consist of sentences coming from multiple UD splits (train/dev/test)
- TODO: the aligned sentences may differ a bit (in punctuation and tokenization in places with punctuation)
    - the following stage of merging should be adjusted to cope with that


# Feb 13
NARC: better merging of NARC and UD
- provided by merge_ud_narc.py
- no document or annotation is skipped in this stage
- taking advantage of the sentence mapping in the "build" stage
- simple heuristics to map tokens
    - unaligned punctuation is aligned to the previous or next token
    - a NARC token split into more is aligned to the last one
- using "preprocess_text" function which was moved from build_ud_narc_map.py to util.py

- forgotten: build_ud_narc_map.py uses scipy and numpy => added to requirements.txt

# Feb 14
NARC: less mentions/entities thrown away
- new way of aligning and merging NARC with UD allows us to delete less entities
    - on the other hand, the aligning process results in removal of several full documents
- the list of invalid entities replaced by list of invalid mentions and links
    - filtered out already during loading the original NARC's ann files
- we skip a mention only if there is another mention with the same full span
    - instead of the previous solution of skipping on the level of partial mention spans
