-- Create additional databases (superset DB is created by POSTGRES_DB env var)
SELECT 'CREATE DATABASE db_source' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'db_source')\gexec
SELECT 'CREATE DATABASE db_target' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'db_target')\gexec

-- ============================================================
-- SOURCE DATABASE  (2023-2024 school year)
-- ============================================================
\connect db_source

CREATE TABLE IF NOT EXISTS students (
    id           SERIAL PRIMARY KEY,
    name         VARCHAR(100) NOT NULL,
    grade_level  INTEGER      NOT NULL,   -- 9=Freshman 10=Sophomore 11=Junior 12=Senior
    homeroom     VARCHAR(20)  NOT NULL,
    enrolled_on  DATE         NOT NULL,
    gpa          NUMERIC(3,2) NOT NULL
);

CREATE TABLE IF NOT EXISTS grades (
    id          SERIAL PRIMARY KEY,
    student_id  INTEGER      NOT NULL,
    subject     VARCHAR(50)  NOT NULL,
    quarter     VARCHAR(5)   NOT NULL,   -- Q1 Q2 Q3 Q4
    score       NUMERIC(5,2) NOT NULL,   -- 0–100
    exam_date   DATE         NOT NULL,
    passed      BOOLEAN      NOT NULL
);

CREATE TABLE IF NOT EXISTS attendance (
    id               SERIAL PRIMARY KEY,
    student_id       INTEGER     NOT NULL,
    attendance_date  DATE        NOT NULL,
    status           VARCHAR(20) NOT NULL,   -- present absent tardy excused
    day_type         VARCHAR(20) NOT NULL    -- regular exam_day field_trip snow_day holiday
);

-- ── Students (20 students, 2023-2024 cohort) ──────────────────
INSERT INTO students (name, grade_level, homeroom, enrolled_on, gpa) VALUES
  ('Alice Johnson',    12, 'Room 101', '2020-09-01', 3.85),
  ('Bob Martinez',     11, 'Room 102', '2021-09-01', 3.20),
  ('Carol White',      10, 'Room 103', '2022-09-01', 2.95),
  ('David Kim',         9, 'Room 104', '2023-09-01', 3.50),
  ('Emma Davis',       12, 'Room 101', '2020-09-01', 3.70),
  ('Frank Lee',        11, 'Room 102', '2021-09-01', 2.80),
  ('Grace Chen',       10, 'Room 103', '2022-09-01', 3.40),
  ('Henry Brown',       9, 'Room 104', '2023-09-01', 3.10),
  ('Isabella Garcia',  12, 'Room 101', '2020-09-01', 4.00),
  ('Jack Thompson',    11, 'Room 102', '2021-09-01', 3.60),
  ('Katie Rodriguez',  10, 'Room 103', '2022-09-01', 2.70),
  ('Liam Wilson',       9, 'Room 104', '2023-09-01', 3.30),
  ('Mia Anderson',     12, 'Room 101', '2020-09-01', 3.90),
  ('Noah Taylor',      11, 'Room 102', '2021-09-01', 3.15),
  ('Olivia Jackson',   10, 'Room 103', '2022-09-01', 3.55),
  ('Peter Harris',      9, 'Room 104', '2023-09-01', 2.90),
  ('Quinn Martin',     12, 'Room 101', '2020-09-01', 3.45),
  ('Rachel Lopez',     11, 'Room 102', '2021-09-01', 3.75),
  ('Sam Clark',        10, 'Room 103', '2022-09-01', 3.00),
  ('Tina Lewis',        9, 'Room 104', '2023-09-01', 3.65);

-- ── Grades (50 records across 4 quarters) ────────────────────
INSERT INTO grades (student_id, subject, quarter, score, exam_date, passed) VALUES
  -- Q1  (mid-October 2023)
  (1,  'Math',             'Q1',  92, '2023-10-15', true),
  (1,  'English',          'Q1',  88, '2023-10-16', true),
  (1,  'Science',          'Q1',  95, '2023-10-17', true),
  (2,  'Math',             'Q1',  78, '2023-10-15', true),
  (2,  'History',          'Q1',  82, '2023-10-16', true),
  (3,  'Art',              'Q1',  91, '2023-10-15', true),
  (3,  'Computer Science', 'Q1',  85, '2023-10-16', true),
  (4,  'Math',             'Q1',  74, '2023-10-15', true),
  (5,  'English',          'Q1',  96, '2023-10-16', true),
  (5,  'Science',          'Q1',  90, '2023-10-17', true),
  (6,  'History',          'Q1',  65, '2023-10-15', false),
  (7,  'Math',             'Q1',  88, '2023-10-15', true),
  (8,  'Computer Science', 'Q1',  79, '2023-10-16', true),
  (9,  'Math',             'Q1', 100, '2023-10-15', true),
  (9,  'Science',          'Q1',  98, '2023-10-17', true),
  -- Q2  (mid-January 2024)
  (1,  'Math',             'Q2',  94, '2024-01-12', true),
  (2,  'Math',             'Q2',  80, '2024-01-12', true),
  (3,  'Art',              'Q2',  93, '2024-01-12', true),
  (4,  'Math',             'Q2',  71, '2024-01-12', true),
  (5,  'English',          'Q2',  92, '2024-01-13', true),
  (6,  'History',          'Q2',  58, '2024-01-12', false),
  (7,  'Math',             'Q2',  91, '2024-01-12', true),
  (8,  'Computer Science', 'Q2',  83, '2024-01-13', true),
  (9,  'Math',             'Q2',  99, '2024-01-12', true),
  (10, 'English',          'Q2',  87, '2024-01-13', true),
  (11, 'Science',          'Q2',  76, '2024-01-14', true),
  (12, 'PE',               'Q2',  88, '2024-01-14', true),
  -- Q3  (mid-March 2024)
  (1,  'Math',             'Q3',  90, '2024-03-15', true),
  (2,  'History',          'Q3',  77, '2024-03-16', true),
  (5,  'Science',          'Q3',  94, '2024-03-17', true),
  (9,  'Math',             'Q3',  97, '2024-03-15', true),
  (13, 'English',          'Q3',  93, '2024-03-16', true),
  (14, 'Computer Science', 'Q3',  81, '2024-03-17', true),
  (15, 'Art',              'Q3',  89, '2024-03-15', true),
  (16, 'Math',             'Q3',  68, '2024-03-15', true),
  (17, 'English',          'Q3',  86, '2024-03-16', true),
  (18, 'Science',          'Q3',  92, '2024-03-17', true),
  -- Q4  (late May 2024)
  (1,  'Math',             'Q4',  96, '2024-05-20', true),
  (9,  'Math',             'Q4', 100, '2024-05-20', true),
  (13, 'English',          'Q4',  95, '2024-05-21', true),
  (19, 'PE',               'Q4',  82, '2024-05-22', true),
  (20, 'Computer Science', 'Q4',  90, '2024-05-22', true),
  (5,  'Science',          'Q4',  91, '2024-05-23', true),
  (7,  'Math',             'Q4',  87, '2024-05-20', true),
  (10, 'History',          'Q4',  79, '2024-05-21', true),
  (3,  'Art',              'Q4',  94, '2024-05-22', true),
  (6,  'History',          'Q4',  72, '2024-05-21', true),
  (4,  'Math',             'Q4',  75, '2024-05-20', true),
  (8,  'Computer Science', 'Q4',  86, '2024-05-22', true),
  (11, 'Science',          'Q4',  81, '2024-05-23', true);

-- ── Attendance (36 records) ───────────────────────────────────
INSERT INTO attendance (student_id, attendance_date, status, day_type) VALUES
  -- Regular September start
  (1,  '2023-09-05', 'present',  'regular'),
  (2,  '2023-09-05', 'present',  'regular'),
  (3,  '2023-09-05', 'absent',   'regular'),
  (4,  '2023-09-05', 'present',  'regular'),
  (5,  '2023-09-05', 'tardy',    'regular'),
  -- Q1 exam week
  (1,  '2023-10-15', 'present',  'exam_day'),
  (2,  '2023-10-15', 'present',  'exam_day'),
  (3,  '2023-10-15', 'absent',   'exam_day'),
  (6,  '2023-10-15', 'present',  'exam_day'),
  (9,  '2023-10-15', 'present',  'exam_day'),
  -- Snow day in November
  (1,  '2023-11-14', 'present',  'snow_day'),
  (5,  '2023-11-14', 'present',  'snow_day'),
  (7,  '2023-11-14', 'absent',   'snow_day'),
  -- Q2 exam week
  (1,  '2024-01-12', 'present',  'exam_day'),
  (9,  '2024-01-12', 'present',  'exam_day'),
  (12, '2024-01-12', 'tardy',    'exam_day'),
  (6,  '2024-01-12', 'absent',   'exam_day'),
  (4,  '2024-01-12', 'present',  'exam_day'),
  -- Field trip February
  (1,  '2024-02-19', 'present',  'field_trip'),
  (4,  '2024-02-19', 'present',  'field_trip'),
  (8,  '2024-02-19', 'present',  'field_trip'),
  (11, '2024-02-19', 'excused',  'field_trip'),
  -- Q3 exam week
  (1,  '2024-03-15', 'present',  'exam_day'),
  (5,  '2024-03-15', 'present',  'exam_day'),
  (9,  '2024-03-15', 'present',  'exam_day'),
  (3,  '2024-03-15', 'tardy',    'exam_day'),
  (15, '2024-03-15', 'present',  'exam_day'),
  -- Spring break make-up / regular
  (1,  '2024-04-08', 'present',  'regular'),
  (7,  '2024-04-08', 'present',  'regular'),
  (11, '2024-04-08', 'excused',  'regular'),
  -- Q4 final exam week
  (1,  '2024-05-20', 'present',  'exam_day'),
  (9,  '2024-05-20', 'present',  'exam_day'),
  (13, '2024-05-20', 'present',  'exam_day'),
  (6,  '2024-05-20', 'absent',   'exam_day'),
  (20, '2024-05-20', 'present',  'exam_day'),
  (5,  '2024-05-23', 'present',  'exam_day');


-- ============================================================
-- TARGET DATABASE  (2024-2025 school year — new cohort)
-- ============================================================
\connect db_target

CREATE TABLE IF NOT EXISTS students (
    id           SERIAL PRIMARY KEY,
    name         VARCHAR(100) NOT NULL,
    grade_level  INTEGER      NOT NULL,
    homeroom     VARCHAR(20)  NOT NULL,
    enrolled_on  DATE         NOT NULL,
    gpa          NUMERIC(3,2) NOT NULL
);

CREATE TABLE IF NOT EXISTS grades (
    id          SERIAL PRIMARY KEY,
    student_id  INTEGER      NOT NULL,
    subject     VARCHAR(50)  NOT NULL,
    quarter     VARCHAR(5)   NOT NULL,
    score       NUMERIC(5,2) NOT NULL,
    exam_date   DATE         NOT NULL,
    passed      BOOLEAN      NOT NULL
);

CREATE TABLE IF NOT EXISTS attendance (
    id               SERIAL PRIMARY KEY,
    student_id       INTEGER     NOT NULL,
    attendance_date  DATE        NOT NULL,
    status           VARCHAR(20) NOT NULL,
    day_type         VARCHAR(20) NOT NULL
);

-- ── Students (6 students, 2024-2025 cohort) ──────────────────
INSERT INTO students (name, grade_level, homeroom, enrolled_on, gpa) VALUES
  ('Zoe Parker',    12, 'Room 201', '2021-09-01', 3.95),
  ('Aiden Scott',   11, 'Room 202', '2022-09-01', 3.40),
  ('Bella Turner',  10, 'Room 203', '2023-09-01', 2.85),
  ('Carlos Perez',   9, 'Room 204', '2024-09-01', 3.20),
  ('Diana Foster',  12, 'Room 201', '2021-09-01', 3.60),
  ('Ethan Barnes',  11, 'Room 202', '2022-09-01', 2.75);

-- ── Grades (15 records, Q1–Q3 so far) ────────────────────────
INSERT INTO grades (student_id, subject, quarter, score, exam_date, passed) VALUES
  (1, 'Math',             'Q1',  97, '2024-10-14', true),
  (1, 'English',          'Q1',  91, '2024-10-15', true),
  (2, 'History',          'Q1',  85, '2024-10-14', true),
  (3, 'Science',          'Q1',  78, '2024-10-15', true),
  (4, 'Computer Science', 'Q1',  88, '2024-10-16', true),
  (5, 'Math',             'Q1',  82, '2024-10-14', true),
  (6, 'Art',              'Q1',  60, '2024-10-14', false),
  (1, 'Math',             'Q2',  99, '2025-01-13', true),
  (2, 'History',          'Q2',  80, '2025-01-13', true),
  (3, 'PE',               'Q2',  92, '2025-01-14', true),
  (4, 'Math',             'Q2',  75, '2025-01-13', true),
  (5, 'English',          'Q2',  88, '2025-01-14', true),
  (6, 'Science',          'Q2',  55, '2025-01-13', false),
  (1, 'Science',          'Q3',  95, '2025-03-18', true),
  (2, 'Computer Science', 'Q3',  83, '2025-03-19', true);

-- ── Attendance (10 records) ───────────────────────────────────
INSERT INTO attendance (student_id, attendance_date, status, day_type) VALUES
  (1, '2024-09-03', 'present', 'regular'),
  (2, '2024-09-03', 'tardy',   'regular'),
  (3, '2024-09-03', 'present', 'regular'),
  (4, '2024-09-03', 'absent',  'regular'),
  (1, '2024-10-14', 'present', 'exam_day'),
  (2, '2024-10-14', 'present', 'exam_day'),
  (6, '2024-10-14', 'absent',  'exam_day'),
  (1, '2025-01-13', 'present', 'exam_day'),
  (5, '2025-01-13', 'present', 'exam_day'),
  (6, '2025-01-13', 'absent',  'exam_day');
