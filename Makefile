# 🔴 Make sure that you've activated you environment


.PHONY: check
check:
	black ./ && isort ./src && flake8 ./

