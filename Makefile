.PHONY: check test

check:
	@echo "Checking Code-Manor integrity..."
	node -c bin/code-manor.js
	bash -n bin/run_maid_loop.sh
	node -e "JSON.parse(require('fs').readFileSync('package.json')); JSON.parse(require('fs').readFileSync('routing.json')); JSON.parse(require('fs').readFileSync('plugin.json'));"
	@if [ -f tools/dashboard/app.py ]; then python3 -m py_compile tools/dashboard/app.py; fi
	@echo "All Code-Manor checks passed."

test:
	@echo "Running tests..."
