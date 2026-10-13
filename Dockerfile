# 1. Utiliser une version légère de Python
FROM python:3.10-slim

# 2. Installer les logiciels système requis (Tesseract et Poppler)
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# 3. Créer un dossier de travail sur le serveur
WORKDIR /app

# 4. Copier la "liste de courses" et installer les modules
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copier tout votre code Python
COPY . .

# 6. Exposer le port réseau et lancer l'API
EXPOSE 8000
CMD ["uvicorn", "api_extraction:app", "--host", "0.0.0.0", "--port", "8000"]