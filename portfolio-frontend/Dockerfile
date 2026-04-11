# Nutzen wir Node als Basis
FROM node:20-slim

WORKDIR /app

# Nur die Package-Dateien kopieren für schnelleres Caching
COPY package*.json ./
RUN npm install

# Restlichen Code kopieren
COPY . .

# Vite Standard-Port
EXPOSE 5173

# Vite muss im Network-Modus starten, damit Docker es nach außen reicht
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]