FROM node:20-alpine

WORKDIR /app

# Enable pnpm
RUN corepack enable && corepack prepare pnpm@latest --activate

# Copy dependency files first for better layer caching
COPY package.json pnpm-workspace.yaml* ./

# Install dependencies (use --no-frozen-lockfile if lock file doesn't exist)
RUN pnpm install

# Copy application code
COPY . .

EXPOSE 3000

CMD ["pnpm", "dev", "--port", "3000", "--hostname", "0.0.0.0"]
