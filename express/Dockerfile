FROM node:20-slim
WORKDIR /app
RUN apt-get update -y && apt-get install -y openssl
COPY . .
RUN npm install --production
EXPOSE 3000
CMD ["node", "src/server.js"]
# Replace index.js with your main file if different
