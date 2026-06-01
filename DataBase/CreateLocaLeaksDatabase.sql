-- =========================
-- Table: Landlord
-- =========================
CREATE TABLE landlord (
    id SERIAL PRIMARY KEY,           -- Unique ID for each landlord, auto-incremented
    name VARCHAR(255) NOT NULL,      -- Landlord's name, cannot be empty
    contact_info TEXT                -- Optional contact details (email, phone, etc.)
);

-- =========================
-- Table: Student
-- =========================
CREATE TABLE student (
    id SERIAL PRIMARY KEY,           -- Unique ID for each student
    name VARCHAR(255) NOT NULL,      -- Student's name, required
    email VARCHAR(255) UNIQUE NOT NULL,  -- Student email, must be unique and not empty
    password_hash VARCHAR(255) NOT NULL, -- Hashed password for security
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP -- Automatically records account creation time
);

-- =========================
-- Table: Apartment
-- =========================
CREATE TABLE apartment (
    id SERIAL PRIMARY KEY,           -- Unique ID for each apartment
    google_place_id VARCHAR(255),    -- Optional Google Places ID
    landlord_id INT NOT NULL REFERENCES landlord(id) ON DELETE CASCADE, 
        -- Foreign key: links to a landlord, cannot be null
        -- If landlord is deleted, all their apartments are automatically deleted
    number VARCHAR(50),              -- Apartment number
    floor INT,                        -- Floor number
    bedrooms INT CHECK (bedrooms >= 0), -- Number of bedrooms, must be >= 0
    bathrooms INT CHECK (bathrooms >= 0), -- Number of bathrooms, must be >= 0
    size_sqm NUMERIC(6,2),           -- Apartment size in square meters (up to 9999.99)
    rent NUMERIC(10,2),              -- Rent amount (up to 99,999,999.99)
    features TEXT                     -- Optional text description of features (balcony, elevator, etc.)
);

-- =========================
-- Table: ApartmentReview
-- =========================
CREATE TABLE apartment_review (
    id SERIAL PRIMARY KEY,           -- Unique ID for each apartment review
    apartment_id INT NOT NULL REFERENCES apartment(id) ON DELETE CASCADE, 
        -- Links review to apartment
    student_id INT NOT NULL REFERENCES student(id) ON DELETE CASCADE, 
        -- Links review to the student who wrote it
    cleanliness INT CHECK (cleanliness BETWEEN 1 AND 10), 
        -- Rating 1–10
    amenities INT CHECK (amenities BETWEEN 1 AND 10), 
    noise INT CHECK (noise BETWEEN 1 AND 10), 
    safety INT CHECK (safety BETWEEN 1 AND 10), 
    value_for_money INT CHECK (value_for_money BETWEEN 1 AND 10), 
    overall INT CHECK (overall BETWEEN 1 AND 10), 
        -- Overall rating, 1–10
    comment TEXT,                    -- Optional written review
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP -- Automatically record when review was made
);

-- =========================
-- Table: LandlordReview
-- =========================
CREATE TABLE landlord_review (
    id SERIAL PRIMARY KEY,           -- Unique ID for each landlord review
    landlord_id INT NOT NULL REFERENCES landlord(id) ON DELETE CASCADE, 
        -- Links review to landlord
    student_id INT NOT NULL REFERENCES student(id) ON DELETE CASCADE, 
        -- Links review to the student who wrote it
    responsiveness INT CHECK (responsiveness BETWEEN 1 AND 10),
    maintenance INT CHECK (maintenance BETWEEN 1 AND 10),
    communication INT CHECK (communication BETWEEN 1 AND 10),
    fairness INT CHECK (fairness BETWEEN 1 AND 10),
    overall INT CHECK (overall BETWEEN 1 AND 10),
        -- Overall rating 1–10
    comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =========================
-- Table: ApartmentReviewAverage
-- =========================
CREATE TABLE apartment_review_average (
    apartment_id INT PRIMARY KEY REFERENCES apartment(id) ON DELETE CASCADE, 
        -- Each apartment has one row storing averages
    average_cleanliness NUMERIC(4,2), -- Average cleanliness rating (1–10)
    average_amenities NUMERIC(4,2),   -- Average amenities rating
    average_noise NUMERIC(4,2),       -- Average noise rating
    average_safety NUMERIC(4,2),      -- Average safety rating
    average_value NUMERIC(4,2),       -- Average value-for-money rating
    overall_average NUMERIC(4,2),     -- Overall average rating
    review_count INT DEFAULT 0         -- Number of reviews used to compute averages
);

-- =========================
-- Table: LandlordReviewAverage
-- =========================
CREATE TABLE landlord_review_average (
    landlord_id INT PRIMARY KEY REFERENCES landlord(id) ON DELETE CASCADE, 
        -- Each landlord has one row storing averages
    average_responsiveness NUMERIC(4,2), -- Average responsiveness rating
    average_maintenance NUMERIC(4,2),    -- Average maintenance rating
    average_communication NUMERIC(4,2),  -- Average communication rating
    average_fairness NUMERIC(4,2),       -- Average fairness rating
    overall_average NUMERIC(4,2),        -- Overall average rating
    review_count INT DEFAULT 0            -- Number of reviews
);