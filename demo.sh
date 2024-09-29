#!/bin/bash
docker compose -f docker-compose.demo.yml up --build -d
docker compose logs -f
