indenter:
	find apps -name "*.html" | xargs djhtml -t 2

ruff:
	ruff check --fix --show-fixes .
	ruff format .


lint: indenter ruff
