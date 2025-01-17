FROM ubuntu:latest
LABEL authors="matve"

ENTRYPOINT ["top", "-b"]