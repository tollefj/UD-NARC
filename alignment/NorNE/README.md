# Misalignment example

## NORNE:
```conllu
# sent_id =  016964
# text = Det virker som fotball er det siste profesjonelle miljø hvor du ikke kan komme ut av skapet stolt. (...
1	Det	det	PRON	_	Gender=Neut|Number=Sing|Person=3|PronType=Prs	2	expl	_	name=O
2	virker	virke	VERB	_	Mood=Ind|Tense=Pres|VerbForm=Fin	0	root	_	name=O
3	som	som	PRON	_	PronType=Rel	9	obj	_	name=O
4	fotball	fotball	NOUN	_	Definite=Ind|Gender=Masc|Number=Sing	9	nsubj	_	name=O
5	er	være	AUX	_	Mood=Ind|Tense=Pres|VerbForm=Fin	9	cop	_	name=O
6	det	det	DET	_	Gender=Neut|Number=Sing|PronType=Dem	9	det	_	name=O
7	siste	sist	ADJ	_	Definite=Def|Degree=Pos|Number=Sing	9	amod	_	name=O
8	profesjonelle	profesjonell	ADJ	_	Definite=Def|Degree=Pos|Number=Sing	9	amod	_	name=O
9	miljø	miljø	NOUN	_	Definite=Ind|Gender=Neut|Number=Sing	2	xcomp	_	name=O
10	hvor	hvor	ADV	_	_	14	advmod	_	name=O
11	du	du	PRON	_	Animacy=Hum|Case=Nom|Number=Sing|Person=2|PronType=Prs	14	nsubj	_	name=O
12	ikke	ikke	PART	_	Polarity=Neg	14	advmod	_	name=O
13	kan	kunne	AUX	_	Mood=Ind|Tense=Pres|VerbForm=Fin	14	aux	_	name=O
14	komme	komme	VERB	_	VerbForm=Inf	9	acl	_	name=O
15	ut	ut	ADP	_	_	17	case	_	name=O
16	av	av	ADP	_	_	17	case	_	name=O
17	skapet	skap	NOUN	_	Definite=Def|Gender=Neut|Number=Sing	14	obl	_	name=O
18	stolt.	stolt.	X	_	_	11	acl	_	name=O
19	(	$(	PUNCT	_	_	2	punct	_	SpaceAfter=No|name=O
20	...	$...	PUNCT	_	_	2	punct	_	SpaceAfter=No|name=O

# sent_id =  016965
# text = ).
1	)	$)	PUNCT	_	_	0	root	_	SpaceAfter=No|name=O
2	.	$.	PUNCT	_	_	1	punct	_	name=O
```
## UD:
```conllu
# sent_id = 016964
# text = Det virker som fotball er det siste profesjonelle miljø hvor du ikke kan komme ut av skapet stolt. (...).
1	Det	det	PRON	_	Gender=Neut|Number=Sing|Person=3|PronType=Prs	2	expl	_	_
2	virker	virke	VERB	_	Mood=Ind|Tense=Pres|VerbForm=Fin	0	root	_	_
3	som	som	PRON	_	PronType=Rel	9	obj	_	_
4	fotball	fotball	NOUN	_	Definite=Ind|Gender=Masc|Number=Sing	9	nsubj	_	_
5	er	være	AUX	_	Mood=Ind|Tense=Pres|VerbForm=Fin	9	cop	_	_
6	det	det	DET	_	Gender=Neut|Number=Sing|PronType=Dem	9	det	_	_
7	siste	sist	ADJ	_	Definite=Def|Degree=Pos|Number=Sing	9	amod	_	_
8	profesjonelle	profesjonell	ADJ	_	Definite=Def|Degree=Pos|Number=Sing	9	amod	_	_
9	miljø	miljø	NOUN	_	Definite=Ind|Gender=Neut|Number=Sing	2	xcomp	_	_
10	hvor	hvor	ADV	_	_	14	advmod	_	_
11	du	du	PRON	_	Animacy=Hum|Case=Nom|Number=Sing|Person=2|PronType=Prs	14	nsubj	_	_
12	ikke	ikke	PART	_	Polarity=Neg	14	advmod	_	_
13	kan	kunne	AUX	_	Mood=Ind|Tense=Pres|VerbForm=Fin	14	aux	_	_
14	komme	komme	VERB	_	VerbForm=Inf	9	acl	_	_
15	ut	ut	ADP	_	_	17	case	_	_
16	av	av	ADP	_	_	17	case	_	_
17	skapet	skap	NOUN	_	Definite=Def|Gender=Neut|Number=Sing	14	obl	_	_
18	stolt.	stolt.	X	_	_	11	acl	_	_
19	(	$(	PUNCT	_	_	20	punct	_	SpaceAfter=No
20	...	$...	PUNCT	_	_	2	punct	_	SpaceAfter=No
21	)	$)	PUNCT	_	_	20	punct	_	SpaceAfter=No
22	.	$.	PUNCT	_	_	2	punct	_	_
```