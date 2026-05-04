# --- STAGE 1: Base (Abhängigkeiten) ---
FROM node:20-alpine AS base
WORKDIR /app
COPY package*.json ./
RUN npm install

# --- STAGE 2: Development (Für deinen PC / Lokales Arbeiten) ---
FROM base AS development
COPY . .
EXPOSE 5173
# Hier bleibt dein gewohnter Dev-Befehl
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

# --- STAGE 3: Build (Kompilieren der App) ---
FROM base AS build
COPY . .
# Erzeugt den 'dist' Ordner mit optimiertem JS/HTML
RUN npm run build

# --- STAGE 4: Production ---
FROM nginx:stable-alpine AS production

# Kopiere unsere eigene Nginx-Konfiguration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Kopiere die gebauten Dateien aus Stage 3
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]