const express = require('express');
const cors = require('cors');
const { Pool } = require('pg');
const WebSocket = require('ws');
const http = require('http');

require('dotenv').config();

const app = express();
app.use(cors());
app.use(express.json());

const pool = new Pool({
  user: process.env.DB_USER || 'clinic_user',
  host: process.env.DB_HOST || '127.0.0.1',
  database: process.env.DB_NAME || 'clinic_db',
  password: process.env.DB_PASSWORD || 'clinic_password',
  port: process.env.DB_PORT || 5432,
});

let mockAppointments = [
  { id: 1, patient_name: 'John Doe', doctor_name: 'Dr. Rao', appointment_date: new Date().toISOString(), appointment_time: '10:00:00', status: 'booked' },
  { id: 2, patient_name: 'Jane Smith', doctor_name: 'Dr. Sharma', appointment_date: new Date().toISOString(), appointment_time: '14:30:00', status: 'booked' }
];

// REST Routes
app.get('/api/appointments', async (req, res) => {
  try {
    const result = await pool.query(`
      SELECT a.id, p.name as patient_name, d.name as doctor_name, a.appointment_date, a.appointment_time, a.status 
      FROM appointments a
      JOIN patients p ON a.patient_id = p.id
      JOIN doctors d ON a.doctor_id = d.id
      ORDER BY a.appointment_date, a.appointment_time
    `);
    res.json(result.rows);
  } catch (err) {
    console.warn('DB not available, returning dynamic mock data.');
    res.json(mockAppointments); 
  }
});

app.post('/api/appointments', (req, res) => {
  const newApt = { id: mockAppointments.length + 1, ...req.body };
  mockAppointments.push(newApt);
  console.log('Gateway: New demo appointment synced:', newApt);
  res.status(201).json(newApt);
});

// Create HTTP server
const server = http.createServer(app);

// Setup WebSocket server
const wss = new WebSocket.Server({ server });

wss.on('connection', (ws) => {
  console.log('Frontend client connected');
  let pythonWs = null;
  const messageBuffer = [];

  const connectToPython = () => {
    console.log('Gateway: Connecting to Python Backend at 127.0.0.1:8000...');
    pythonWs = new WebSocket('ws://127.0.0.1:8000/ws');

    pythonWs.on('open', () => {
      console.log('Gateway: Connected to Python Backend');
      // Flush any buffered messages
      while (messageBuffer.length > 0) {
        pythonWs.send(messageBuffer.shift());
      }
    });

    pythonWs.on('message', (data) => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(data.toString());
      }
    });

    pythonWs.on('error', (err) => {
      console.error('Gateway: Python WS error:', err.message);
    });

    pythonWs.on('close', () => {
      console.log('Gateway: Python WS closed');
      pythonWs = null;
    });
  };

  connectToPython();

  // Keep-alive heartbeat (every 30s)
  const heartbeat = setInterval(() => {
    if (ws.readyState === WebSocket.OPEN) {
      ws.ping(); // Standard WS ping
    }
  }, 30000);

  ws.on('message', (message) => {
    const msg = message.toString();
    if (pythonWs && pythonWs.readyState === WebSocket.OPEN) {
      pythonWs.send(msg);
    } else {
      // Buffer until Python WS ready
      messageBuffer.push(msg);
      if (!pythonWs) connectToPython();
    }
  });

  ws.onclose = () => {
    console.log('Frontend client disconnected');
    clearInterval(heartbeat);
    if (pythonWs && pythonWs.readyState === WebSocket.OPEN) {
      pythonWs.close();
    }
  };
});

const PORT = process.env.PORT || 3001;
server.listen(PORT, () => {
  console.log(`API Gateway running on port ${PORT}`);
});
