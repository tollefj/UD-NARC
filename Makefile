all: convert

convert:
	python pipeline.py

clean:
	rm -rf data/narc-merged/annotations_*
	rm -rf data/narc-merged/UD*
	rm -rf data/narc-merged/OUTPUT

udapi:
	################## BOKMAAL ################
	cat data/narc-merged/OUTPUT/no-narc_bokmaal/narc_bokmaal_train.conllu | udapy corefud.PrintMentions | tail -1
	cat data/narc-merged/OUTPUT/no-narc_bokmaal/narc_bokmaal_test.conllu | udapy corefud.PrintMentions | tail -1
	cat data/narc-merged/OUTPUT/no-narc_bokmaal/narc_bokmaal_dev.conllu | udapy corefud.PrintMentions | tail -1
	################## NYNORSK ################
	cat data/narc-merged/OUTPUT/no-narc_nynorsk/narc_nynorsk_train.conllu| udapy corefud.PrintMentions | tail -1
	cat data/narc-merged/OUTPUT/no-narc_nynorsk/narc_nynorsk_test.conllu| udapy corefud.PrintMentions | tail -1
	cat data/narc-merged/OUTPUT/no-narc_nynorsk/narc_nynorsk_dev.conllu| udapy corefud.PrintMentions | tail -1

udapi_stats:
	################## BOKMAAL ################
	cat data/narc-merged/OUTPUT/no-narc_bokmaal/narc_bokmaal_train.conllu | udapy corefud.Stats
	cat data/narc-merged/OUTPUT/no-narc_bokmaal/narc_bokmaal_test.conllu | udapy corefud.Stats
	cat data/narc-merged/OUTPUT/no-narc_bokmaal/narc_bokmaal_dev.conllu | udapy corefud.Stats
	################## NYNORSK ################
	cat data/narc-merged/OUTPUT/no-narc_nynorsk/narc_nynorsk_train.conllu| udapy corefud.Stats
	cat data/narc-merged/OUTPUT/no-narc_nynorsk/narc_nynorsk_test.conllu| udapy corefud.Stats
	cat data/narc-merged/OUTPUT/no-narc_nynorsk/narc_nynorsk_dev.conllu| udapy corefud.Stats