# --- STAGE 1: Build the Angular application ---
FROM node:20-alpine AS build

# 1. Set working directory
WORKDIR /app

# 2. Copy ALL files needed for the build.
# We copy everything first to ensure environment.docker.ts is present.
COPY . .

# 3. Install dependencies
# We run npm install *after* copying package.json (which is included in COPY . .), 
# to ensure it can read the package-lock.json if present.
RUN npm install

# 4. Inject the API URL into the environment file (FIXED POSITION)
# The file now exists at /app/src/environments/environment.docker.ts
RUN sed -i "s|apiUrl: 'http://backend:5000'|apiUrl: '${API_URL}'|" ./src/environments/environment.docker.ts

# 5. Build the Angular app
# This command runs inside /app, which contains node_modules and angular.json/package.json
RUN npm run build -- --configuration docker --base-href=/ --optimization=false

# --- STAGE 2: Serve the application with Nginx (for production) ---
# Use a very light Nginx image to serve the compiled static files
FROM nginx:alpine

# Copy the custom Nginx config (optional, but good practice for Angular routing)
# If you don't have an nginx.conf, skip this line and the next line
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy the built Angular files from the build stage to the Nginx static directory
COPY --from=build /app/dist/agria-ui/browser /usr/share/nginx/html

# Angular runs on 4200 during development, but Nginx default is 80
EXPOSE 80

# The default Nginx CMD serves the static content