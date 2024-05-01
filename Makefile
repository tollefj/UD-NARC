all: update install convert

update:
	git submodule update --recursive --init

install:
	python -m pip install -r requirements.txt

convert:
	python ud_narc/pipeline.py

align-treebank:
	python ud_narc/pipeline_treebank_update.py

clean:
	rm -rf output/

udapi:
	################## BOKMAAL ################
	cat output/aligned/no-narc_bokmaal/narc_bokmaal_train.conllu | udapy corefud.PrintMentions | tail -1
	cat output/aligned/no-narc_bokmaal/narc_bokmaal_test.conllu | udapy corefud.PrintMentions | tail -1
	cat output/aligned/no-narc_bokmaal/narc_bokmaal_dev.conllu | udapy corefud.PrintMentions | tail -1
	################## NYNORSK ################
	cat output/aligned/no-narc_nynorsk/narc_nynorsk_train.conllu| udapy corefud.PrintMentions | tail -1
	cat output/aligned/no-narc_nynorsk/narc_nynorsk_test.conllu| udapy corefud.PrintMentions | tail -1
	cat output/aligned/no-narc_nynorsk/narc_nynorsk_dev.conllu| udapy corefud.PrintMentions | tail -1

udapi_stats:
	################## BOKMAAL ################
	cat output/aligned/no-narc_bokmaal/narc_bokmaal_train.conllu | udapy corefud.Stats
	cat output/aligned/no-narc_bokmaal/narc_bokmaal_test.conllu | udapy corefud.Stats
	cat output/aligned/no-narc_bokmaal/narc_bokmaal_dev.conllu | udapy corefud.Stats
	################## NYNORSK ################
	cat output/aligned/no-narc_nynorsk/narc_nynorsk_train.conllu| udapy corefud.Stats
	cat output/aligned/no-narc_nynorsk/narc_nynorsk_test.conllu| udapy corefud.Stats
	cat output/aligned/no-narc_nynorsk/narc_nynorsk_dev.conllu| udapy corefud.Stats
