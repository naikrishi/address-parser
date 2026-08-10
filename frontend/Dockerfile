FROM node:20-alpine

WORKDIR /app

COPY ATTINTERNALROOTv2.crt /usr/local/share/ca-certificates/ATTINTERNALROOTv2.crt
ENV NODE_EXTRA_CA_CERTS=/usr/local/share/ca-certificates/ATTINTERNALROOTv2.crt \
	NPM_CONFIG_REGISTRY=https://registry.npmjs.org/ \
	NPM_CONFIG_USERCONFIG=/tmp/empty-npmrc \
	NPM_CONFIG_GLOBALCONFIG=/tmp/empty-global-npmrc \
	NPM_CONFIG_STRICT_SSL=false \
	npm_config_cafile=/usr/local/share/ca-certificates/ATTINTERNALROOTv2.crt

COPY package.json ./
RUN touch /tmp/empty-npmrc /tmp/empty-global-npmrc && npm install --userconfig=/tmp/empty-npmrc --globalconfig=/tmp/empty-global-npmrc --registry=https://registry.npmjs.org/ --strict-ssl=false --verbose

COPY . ./

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
