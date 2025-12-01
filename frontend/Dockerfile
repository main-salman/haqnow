# Fast frontend image - just copies pre-built dist
# Build time: ~5 seconds
FROM nginx:alpine

# Copy pre-built frontend (built locally, not in Docker)
COPY dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
