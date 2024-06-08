mkdir -p data
docker compose down -v --remove-orphans
docker compose pull
docker compose up -d