CREATE DATABASE appdb;

CREATE USER appuser WITH ENCRYPTED PASSWORD 'apppass';

GRANT ALL PRIVILEGES ON DATABASE appdb TO appuser;

\c appdb;

ALTER SCHEMA public OWNER TO appuser;

CREATE TABLE test_table (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE test_table OWNER TO appuser;

INSERT INTO test_table (name) VALUES ('test1'), ('test2');