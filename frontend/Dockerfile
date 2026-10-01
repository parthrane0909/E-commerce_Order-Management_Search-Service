# ---------------------------------------------------------------------------
# Multi-stage Dockerfile for the Meridian frontend.
#   base  -> shared workdir + manifest copy
#   dev   -> npm install + vite dev server (used by docker-compose target: dev)
#   build -> npm install + production bundle
#   prod  -> nginx serving the built dist with SPA fallback + /api proxy
# ---------------------------------------------------------------------------

FROM node:20-alpine AS base
WORKDIR /app
ENV CI=1
COPY package.json package-lock.json* ./

FROM base AS dev
RUN npm install
COPY . .
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]

FROM base AS build
ARG VITE_API_BASE_URL=
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
RUN npm install
COPY . .
RUN npm run build

FROM nginx:1.27-alpine AS prod
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
