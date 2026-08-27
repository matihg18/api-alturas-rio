# ── Stage 1: build ──────────────────────────────────────────────────────────
FROM node:22-alpine AS builder

WORKDIR /app

# Instalar dependencias primero (capa cacheada mientras package.json no cambie)
COPY package.json package-lock.json ./
RUN npm ci --frozen-lockfile

# Copiar fuentes y compilar
COPY . .
ARG VITE_CARTO_API_KEY
ENV VITE_CARTO_API_KEY=${VITE_CARTO_API_KEY}
RUN npm run build


# ── Stage 2: serve ──────────────────────────────────────────────────────────
FROM nginx:1.27-alpine

# Copiar el bundle generado
COPY --from=builder /app/dist /usr/share/nginx/html

# Configuración de nginx (reemplaza la default)
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
