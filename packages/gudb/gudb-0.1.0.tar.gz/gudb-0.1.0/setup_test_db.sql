-- AI-DB-Sentinel Test Database Setup
-- Run this in your PostgreSQL database to create test data

-- Create orders table
CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    status VARCHAR(50) NOT NULL,
    total_amount DECIMAL(10, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert sample data (1000 rows for testing)
INSERT INTO orders (customer_id, status, total_amount)
SELECT 
    (random() * 1000)::integer as customer_id,
    CASE (random() * 3)::integer
        WHEN 0 THEN 'pending'
        WHEN 1 THEN 'processing'
        WHEN 2 THEN 'completed'
        ELSE 'cancelled'
    END as status,
    (random() * 1000)::decimal(10,2) as total_amount
FROM generate_series(1, 1000);

-- Verify data
SELECT COUNT(*) as total_orders, status, COUNT(*) as count_by_status
FROM orders
GROUP BY status;

-- Test the slow query
SELECT * FROM orders WHERE status = 'pending';

-- This query will be slow without an index!
-- The AI will recommend adding an index like:
-- CREATE INDEX idx_orders_status ON orders(status);
