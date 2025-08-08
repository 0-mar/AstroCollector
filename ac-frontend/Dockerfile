# Build Stage
FROM node:24.0.0-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Production Stage
FROM docker.io/nginx:stable-alpine AS production
COPY --from=build /app/dist /usr/share/nginx/html

# choose config file based on use
ARG PRODUCTION
COPY --from=build /app/nginx.local.conf /tmp/nginx.local.conf
COPY --from=build /app/nginx.prod.conf /tmp/nginx.prod.conf

# Choose based on ARG
RUN if [ "$PRODUCTION" = "true" ]; then \
      cp /tmp/nginx.prod.conf /etc/nginx/nginx.conf; \
    else \
      cp /tmp/nginx.local.conf /etc/nginx/nginx.conf; \
    fi

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
