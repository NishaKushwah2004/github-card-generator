FROM nginx:alpine

# Copy the index.html to a temporary location
COPY index.html /etc/nginx/templates/index.html.template

# Use the default nginx docker entrypoint to perform substitution
# Nginx images 1.19+ automatically run envsubst on files in /etc/nginx/templates/*.template
# and output them to /etc/nginx/conf.d/ or wherever specified.
# However, to be explicit as requested:

CMD ["/bin/sh", "-c", "envsubst '${BACKEND_URL}' < /etc/nginx/templates/index.html.template > /usr/share/nginx/html/index.html && sed -i \"s/listen\\s\\+80;/listen ${PORT:-80};/\" /etc/nginx/conf.d/default.conf && exec nginx -g 'daemon off;'"]
