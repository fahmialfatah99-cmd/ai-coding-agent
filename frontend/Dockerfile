FROM node:18-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production \
    PORT=3000

COPY package.json package-lock.json* ./
RUN npm install

COPY . .
RUN npm run build

EXPOSE 3000

CMD ["npm", "start"]
