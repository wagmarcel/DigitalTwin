FROM node:16
ADD alerta alerta
ADD debeziumBridge debeziumBridge
ADD ngsildUpdates ngsildUpdates
ADD package.json package.json
ADD package-lock.json package-lock.json
ADD lib/ lib
add config/ config
ADD test test
ADD .eslintrc.json .eslintrc.json
WORKDIR /
RUN npm install && npm run lint && npm run test

ENV NODE_ENV=production
USER 9999
