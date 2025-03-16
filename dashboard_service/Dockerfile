FROM node:18

WORKDIR /app

COPY package.json package-lock.json ./

RUN npm install

COPY . /app

EXPOSE 5173

# Run Vite with --host to bind to 0.0.0.0
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]