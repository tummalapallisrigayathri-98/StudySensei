#!/usr/bin/env bash
docker build -t studysensi:latest .
docker run -p 8000:8000 studysensi:latest
