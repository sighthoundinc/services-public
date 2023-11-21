# Use Node.js image
FROM node:16

# Set the working directory
WORKDIR /app

# Copy package files and install dependencies
COPY src/package*.json ./
RUN npm install

# Copy local code to the container
COPY src /app

# Build the Svelte app
RUN npm run build

# Start the application
CMD ["npm", "run", "preview"]