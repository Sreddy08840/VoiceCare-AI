CREATE TABLE IF NOT EXISTS patients (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    phone_number VARCHAR(50) UNIQUE NOT NULL,
    preferred_language VARCHAR(50) DEFAULT 'English',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS doctors (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    department VARCHAR(255) NOT NULL
);

CREATE TABLE IF NOT EXISTS appointments (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER REFERENCES patients(id),
    doctor_id INTEGER REFERENCES doctors(id),
    appointment_date DATE NOT NULL,
    appointment_time TIME NOT NULL,
    status VARCHAR(50) DEFAULT 'booked',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert mock data
INSERT INTO doctors (name, department) VALUES ('Dr. Rao', 'Cardiology') ON CONFLICT DO NOTHING;
INSERT INTO doctors (name, department) VALUES ('Dr. Meena', 'Neurology') ON CONFLICT DO NOTHING;
INSERT INTO doctors (name, department) VALUES ('Dr. Patel', 'General Medicine') ON CONFLICT DO NOTHING;

INSERT INTO patients (name, phone_number, preferred_language) VALUES ('John Doe', '+1234567890', 'English') ON CONFLICT DO NOTHING;
