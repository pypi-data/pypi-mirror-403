#!/usr/bin/env node
const { spawn } = require('child_process');

// Use uvx to run the PyPI package
// uvx handles venv creation and dependency resolution automatically
const proc = spawn('uvx', ['zendesk-mcp-server'], {
  stdio: 'inherit',
  env: process.env
});

proc.on('error', (err) => {
  console.error('Failed to start Zendesk MCP:', err.message);
  console.error('Ensure Python 3.12+ and uv are installed (brew install uv)');
  process.exit(1);
});

proc.on('exit', (code) => process.exit(code || 0));
