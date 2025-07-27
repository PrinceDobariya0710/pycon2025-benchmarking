FROM golang:1.23.0
WORKDIR /app
COPY . .
RUN go mod tidy
RUN go build -o app main.go
EXPOSE 8080
CMD ["./app"]