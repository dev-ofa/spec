.PHONY: install fmt tidy lint test build run

install:
	go install golang.org/x/tools/cmd/goimports@latest
	go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest

fmt:
	gofmt -w .
	goimports -w .

tidy:
	go mod tidy

lint:
	golangci-lint run ./...

test:
	go test ./...

build:
	go build ./...

run:
	go run ./cmd/...
