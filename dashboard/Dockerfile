# ── Stage 1: build ──────────────────────────────────────────────────────────
FROM node:22-alpine AS builder

WORKDIR /app

# Instalar dependencias primero (capa cacheada mientras package.json no cambie)
COPY package.json package-lock.json ./
RUN npm ci --frozen-lockfile

# Copiar fuentes y compilar
COPY . .
RUN npm run build


# ── Stage 2: serve ──────────────────────────────────────────────────────────
FROM nginx:1.27-alpine

RUN apk add --no-cache openssl

RUN mkdir -p /etc/nginx/certs && \
    openssl req -x509 -nodes -newkey rsa:2048 -sha256 -days 365 \
      -keyout /etc/nginx/certs/localhost.key \
      -out /etc/nginx/certs/localhost.crt \
      -subj "/CN=localhost" \
      -addext "subjectAltName=DNS:localhost,IP:127.0.0.1"

# Copiar el bundle generado
COPY --from=builder /app/dist /usr/share/nginx/html

# Configuración de nginx (reemplaza la default)
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80 443

CMD ["nginx", "-g", "daemon off;"]
