-- Synthetic demo data only. No real patients.
CREATE TABLE patients (
    patient_id   TEXT PRIMARY KEY,
    display_name TEXT NOT NULL
);

CREATE TABLE medications (
    med_id       INTEGER PRIMARY KEY,
    patient_id   TEXT NOT NULL REFERENCES patients(patient_id),
    name         TEXT NOT NULL,
    dose         TEXT NOT NULL,
    times        TEXT NOT NULL   -- comma-separated HH:MM
);

CREATE TABLE intake_log (
    log_id       INTEGER PRIMARY KEY,
    med_id       INTEGER NOT NULL REFERENCES medications(med_id),
    scheduled_at TEXT NOT NULL,  -- ISO date + time
    taken        INTEGER NOT NULL -- 1 = taken, 0 = missed
);

INSERT INTO patients VALUES
  ('P001', 'Demo Patient A'),
  ('P002', 'Demo Patient B');

INSERT INTO medications VALUES
  (1, 'P001', 'Metformin',   '500 mg', '08:00,20:00'),
  (2, 'P001', 'Atorvastatin','20 mg',  '21:00'),
  (3, 'P002', 'Levothyroxine','50 mcg','07:00');

-- P001: 7 days, Metformin twice daily, Atorvastatin once daily
INSERT INTO intake_log (med_id, scheduled_at, taken) VALUES
  (1,'2026-09-24 08:00',1),(1,'2026-09-24 20:00',1),(2,'2026-09-24 21:00',1),
  (1,'2026-09-25 08:00',1),(1,'2026-09-25 20:00',0),(2,'2026-09-25 21:00',1),
  (1,'2026-09-26 08:00',1),(1,'2026-09-26 20:00',1),(2,'2026-09-26 21:00',0),
  (1,'2026-09-27 08:00',0),(1,'2026-09-27 20:00',1),(2,'2026-09-27 21:00',1),
  (1,'2026-09-28 08:00',1),(1,'2026-09-28 20:00',1),(2,'2026-09-28 21:00',1),
  (1,'2026-09-29 08:00',1),(1,'2026-09-29 20:00',0),(2,'2026-09-29 21:00',1),
  (1,'2026-09-30 08:00',1),(1,'2026-09-30 20:00',1),(2,'2026-09-30 21:00',1);

-- P002: 7 days, once daily, all taken
INSERT INTO intake_log (med_id, scheduled_at, taken) VALUES
  (3,'2026-09-24 07:00',1),(3,'2026-09-25 07:00',1),(3,'2026-09-26 07:00',1),
  (3,'2026-09-27 07:00',1),(3,'2026-09-28 07:00',1),(3,'2026-09-29 07:00',1),
  (3,'2026-09-30 07:00',1);
