# -----------------------
# STAGE 1: Angular Build
# -----------------------
FROM node:20-alpine AS build

ARG API_URL
ENV API_URL_ENV=${API_URL}

WORKDIR /app

# Copy only dependency files first (better build caching)
COPY package*.json ./

RUN npm install

# Copy remaining app files
COPY . .

# Inject API URL
RUN sed -i "s|apiUrl: 'http://backend:5000'|apiUrl: '${API_URL_ENV}'|" src/environments/environment.docker.ts

# Build Angular optimized for Docker target
RUN npm run build -- --configuration docker --base-href=/ --optimization=false


# -----------------------
# STAGE 2: Production Server
# -----------------------
FROM nginx:alpine

# Optional custom NGINX config (enables SPA routing)
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built app from previous stage
COPY --from=build /app/dist/agria-ui/browser /usr/share/nginx/html

EXPOSE 80

# Nginx default CMD will serve the app
