# Use a slim Python image
FROM python:3.11-slim as builder

# Set working directory
WORKDIR /app

# Install build dependencies
RUN pip install --no-cache-dir hatchling

# Copy project files
COPY . .

# Build the package
RUN pip install .

# Final stage
FROM python:3.11-slim

WORKDIR /app

# Copy the installed package from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin/jeomaechu /usr/local/bin/jeomaechu
COPY --from=builder /usr/local/bin/j /usr/local/bin/j

# Set the entrypoint to the CLI
ENTRYPOINT ["jeomaechu"]

# Default command matches help
CMD ["--help"]
