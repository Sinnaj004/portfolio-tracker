# --- STAGE 1: Base ---
FROM node:20-alpine AS base
WORKDIR /app
COPY package*.json ./
RUN npm install

# --- STAGE 2: Development ---
FROM base AS development
COPY . .
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

# --- STAGE 3: Build (HIER SIND DIE ÄNDERUNGEN) ---
FROM base AS build
# 1. Deklariere, dass wir ein Argument namens VITE_API_URL erwarten
ARG VITE_API_URL

# 2. Mache dieses Argument als Umgebungsvariable für den Build-Prozess verfügbar
ENV VITE_API_URL=$VITE_API_URL

COPY . .
# Jetzt wird beim Build die URL korrekt in den JS-Code geschrieben
RUN npm run build

# --- STAGE 4: Production ---
FROM nginx:stable-alpine AS production
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]