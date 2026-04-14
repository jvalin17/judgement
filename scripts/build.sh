#!/bin/bash
# Build the frontend for production.
cd "$(dirname "$0")/../frontend"
npm ci && npm run build
