mkdir -p data
mkdir -p logs
docker-compose down -v --remove-orphans
docker-compose up -d