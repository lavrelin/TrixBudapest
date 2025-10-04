#!/bin/bash
# railway_init.sh - Инициализация БД на Railway

echo "🔄 Initializing database..."
python init_db.py

if [ $? -eq 0 ]; then
    echo "✅ Database initialized successfully"
    echo "🚀 Starting bot..."
    python main.py
else
    echo "❌ Database initialization failed"
    exit 1
fi
