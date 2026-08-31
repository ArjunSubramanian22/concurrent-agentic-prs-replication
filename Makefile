PYTHON ?= $(wildcard .venv/bin/python)
ifeq ($(PYTHON),)
PYTHON := python3
endif
export PYTHONPATH := $(CURDIR)

.PHONY: all data env analysis figures paper replay collect test legacy wp1 wp2 wp3 wp4 wp5 clean

all: data env analysis figures
	@echo "make all: data + analysis + figures (no live GitHub, no TeX)"

env:
	$(PYTHON) scripts/record_env.py

data:
	$(PYTHON) scripts/vendor_snapshot.py

wp1: data
	$(PYTHON) analysis/wp1_coactivity.py

wp2: wp1
	$(PYTHON) analysis/wp2_sample.py

legacy:
	$(PYTHON) analysis/wp_legacy.py

analysis: wp1 wp2 legacy
	$(PYTHON) analysis/wp3_confound.py || echo "WP3 skipped or incomplete (see stdout)"
	$(PYTHON) analysis/wp4_human_baseline.py || echo "WP4 skipped or incomplete (see stdout)"
	$(PYTHON) analysis/wp5_build_test.py || true
	$(PYTHON) analysis/wp6_predict.py || true
	$(PYTHON) analysis/emit_tables.py
	$(PYTHON) analysis/emit_macros.py
	$(PYTHON) analysis/emit_claims_status.py

figures: analysis
	$(PYTHON) analysis/figures.py

paper: figures
	cd paper && latexmk -pdf -interaction=nonstopmode main.tex

replay:
	$(PYTHON) analysis/replay.py

collect:
	$(PYTHON) analysis/collect_github.py

test:
	$(PYTHON) -m pytest tests -q

clean:
	rm -f paper/main.aux paper/main.log paper/main.out paper/main.pdf
