VERSION := $(shell poetry version -s)

build:
	docker build . -t josselingirault/f1manager-companion:$(VERSION) -t josselingirault/f1manager-companion:latest

push:
	docker push josselingirault/f1manager-companion:$(VERSION)
	docker push josselingirault/f1manager-companion:latest
