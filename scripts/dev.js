const { spawn } = require('child_process');
const path = require('path');

const isWin = process.platform === 'win32';
const backendCwd = path.join(__dirname, '..', 'backend');
const uvicornPath = isWin
  ? path.join(backendCwd, '.venv', 'Scripts', 'uvicorn.exe')
  : path.join(backendCwd, '.venv', 'bin', 'uvicorn');

console.log('\x1b[36m%s\x1b[0m', '🚀 Launching TalentMind AI Frontend & Backend concurrently...');

// Start the Backend service on port 8000
const backend = spawn(uvicornPath, ['app.main:app', '--host', '0.0.0.0', '--port', '8000', '--reload'], {
  cwd: backendCwd,
  shell: true
});

// Start the Next.js Frontend service
const frontend = spawn('npx', ['next', 'dev'], {
  cwd: path.join(__dirname, '..'),
  shell: true
});

// Prefix logs with colors for easy reading
function prefixOutput(stream, prefix, color) {
  if (!stream) return;
  stream.on('data', (data) => {
    const lines = data.toString().split('\n');
    lines.forEach((line) => {
      if (line.trim()) {
        console.log(`${color}${prefix}\x1b[0m | ${line}`);
      }
    });
  });
}

prefixOutput(backend.stdout, '[Backend]', '\x1b[32m'); // Green
prefixOutput(backend.stderr, '[Backend]', '\x1b[33m'); // Yellow
prefixOutput(frontend.stdout, '[Frontend]', '\x1b[34m'); // Blue
prefixOutput(frontend.stderr, '[Frontend]', '\x1b[31m'); // Red

let cleanedUp = false;
function killAll() {
  if (cleanedUp) return;
  cleanedUp = true;
  console.log('\x1b[31m%s\x1b[0m', '\n🛑 Stopping all services (Frontend & Backend)...');
  backend.kill();
  frontend.kill();
  process.exit();
}

process.on('SIGINT', killAll);
process.on('SIGTERM', killAll);
process.on('exit', killAll);

backend.on('close', (code) => {
  console.log(`Backend process exited with code ${code}`);
  killAll();
});

frontend.on('close', (code) => {
  console.log(`Frontend process exited with code ${code}`);
  killAll();
});
