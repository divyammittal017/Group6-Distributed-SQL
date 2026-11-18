CREATE DATABASE IF NOT EXISTS distributed_lab;
USE distributed_lab;

CREATE TABLE IF NOT EXISTS accounts (
    id INT PRIMARY KEY,
    balance DECIMAL(12, 2) NOT NULL
);

-- Seed 10,000 synthetic accounts. Safe to run again after clearing the table.
UPSERT INTO accounts (id, balance)
SELECT i, 1000.00
FROM generate_series(1, 10000) AS g(i);
