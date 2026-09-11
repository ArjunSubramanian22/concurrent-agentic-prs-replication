PYTHON ?= python3
export PYTHONPATH := $(CURDIR)/measurement:$(CURDIR)/semantic_conflicts/src:$(CURDIR)

.PHONY: check test audit measurement-check conflictbench-metrics mergegym-check semantic-test install clean

install:
	$(PYTHON) -m pip install -r requirements.txt
	$(PYTHON) -m pip install -e ".[dev]"

check: test audit conflictbench-metrics mergegym-check
	@echo "make check: offline tests + metrics + T3 regression + anonymity audit"

test: measurement-check semantic-test
	$(PYTHON) -m pytest tests -q

measurement-check:
	$(MAKE) -C measurement test PYTHON=$(PYTHON)

semantic-test:
	$(PYTHON) -m pytest semantic_conflicts/tests -q

conflictbench-metrics:
	$(MAKE) -C conflictbench metrics PYTHON=$(PYTHON)

mergegym-check:
	$(PYTHON) mergegym/scripts/t3_simulator.py --check

audit:
	bash scripts/anonymity_audit.sh

# Optional: full measurement tables/figures from committed extracts (no Hugging Face).
measurement:
	$(MAKE) -C measurement all PYTHON=$(PYTHON)

# Optional: Semantic Conflicts v1 rebuild (CPU, no network, several minutes).
semantic-rebuild:
	$(PYTHON) -m semantic_conflicts.pipeline deterministic

clean:
	rm -rf .pytest_cache .mplconfig mergegym/t3_sim_results.csv
	find . -name '__pycache__' -type d -prune -exec rm -rf {} +
