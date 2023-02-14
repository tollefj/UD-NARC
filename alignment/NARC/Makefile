all: convert

convert:
	python pipeline.py

clean:
	rm -rf NARC/annotations_conll*
	rm -rf NARC/annotations_jsonlines*
	rm -rf NARC/UD_SPLITS*
	rm -rf NARC/UD_NARC*
	rm -rf output*
	rm -rf no-narc*

udapi:
	################## BOKMAAL ################
	cat no-narc_bokmaal/narc_bokmaal_train.conllu | udapy corefud.PrintMentions | tail -1
	cat no-narc_bokmaal/narc_bokmaal_test.conllu | udapy corefud.PrintMentions | tail -1
	cat no-narc_bokmaal/narc_bokmaal_dev.conllu | udapy corefud.PrintMentions | tail -1
	################## NYNORSK ################
	cat no-narc_nynorsk/narc_nynorsk_train.conllu| udapy corefud.PrintMentions | tail -1
	cat no-narc_nynorsk/narc_nynorsk_test.conllu| udapy corefud.PrintMentions | tail -1
	cat no-narc_nynorsk/narc_nynorsk_dev.conllu| udapy corefud.PrintMentions | tail -1
