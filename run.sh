mkdir -p data
docker compose down -v --remove-orphans --timeout 60
docker compose pull
docker compose up -d