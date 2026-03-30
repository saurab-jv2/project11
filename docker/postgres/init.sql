-- connect to the DB created by POSTGRES_DB
\c appdb;

-- ensure correct ownership
ALTER SCHEMA public OWNER TO appuser;

-- create table
CREATE TABLE IF NOT EXISTS test_table (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- set owner
ALTER TABLE test_table OWNER TO appuser;

-- insert sample data (avoid duplicates)
INSERT INTO test_table (name)
SELECT 'test1'
WHERE NOT EXISTS (SELECT 1 FROM test_table WHERE name = 'test1');

INSERT INTO test_table (name)
SELECT 'test2'
WHERE NOT EXISTS (SELECT 1 FROM test_table WHERE name = 'test2');