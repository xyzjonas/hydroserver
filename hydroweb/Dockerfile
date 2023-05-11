FROM node:16 as build
ENV API_URL = app:8080

WORKDIR /app

COPY package-lock.json package.json ./
RUN npm install
COPY . .

RUN npm run build


FROM nginx:latest as run

COPY --from=build /app/dist/ /usr/share/nginx/html/
COPY ./docker-entrypoint.sh /entrypoint.sh

EXPOSE 80
ENTRYPOINT ["/entrypoint.sh"]
