ARG RUNTIME_IMAGE=christopheraburns/mcp-factory-runtime:0.1.1
FROM ${RUNTIME_IMAGE}
USER root
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --cache /tmp/npm-cache && chown -R cdsw:cdsw /app
COPY . .
USER cdsw
ENV npm_config_cache=/tmp/npm-cache-user
CMD ["npm", "run", "dev"]
