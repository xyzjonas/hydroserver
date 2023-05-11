#!/bin/sh

ROOT_DIR=/usr/share/nginx/html

# Replace env vars in JavaScript files
echo "Replacing env constants in JS"
for file in $ROOT_DIR/js/app.*.js* $ROOT_DIR/index.html;
do
  echo "Processing $file ... -> $API_URL";
  #sed -i "s|BASE_URL:\"\/\"|BASE_URL:\"${API_URL}\"|g" $file
  sed -i "s|http:\/\/localhost:3000|${API_URL}|g" $file
done

echo "Starting Nginx"
nginx -g 'daemon off;'