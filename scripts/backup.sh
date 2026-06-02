#!/bin/bash  
set -e
# скрипт создания бэков
BACKUP_DIR="/var/backups/telecom"  # Директория для бэкапов
TIMESTAMP=$(date +%F-%H%M%S)   # время для имени бэка 

mkdir -p $BACKUP_DIR # Создаём директорию если нет

echo "Creating PostgreSQL backup..."
docker exec telecom-system-db-1 pg_dump -U telecom telecom | gzip > $BACKUP_DIR/db-$TIMESTAMP.sql.gz # Делаем pg_dump (экспорт БД) и сжимаем gzip
                                                                                                    # docker exec = выполнить команду в контейнере
find $BACKUP_DIR -name "*.gz" -mtime +7 -delete # Удаляем бэкапы старше 7 дней (find -mtime +7 = более 7 дней)

echo "Backup completed: $BACKUP_DIR/db-$TIMESTAMP.sql.gz"
