\c appdb;

ALTER SCHEMA public OWNER TO appuser;

CREATE TABLE IF NOT EXISTS test_table (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE test_table OWNER TO appuser;

INSERT INTO test_table (name)
SELECT 'test1'
WHERE NOT EXISTS (SELECT 1 FROM test_table WHERE name = 'test1');

INSERT INTO test_table (name)
SELECT 'test2'
WHERE NOT EXISTS (SELECT 1 FROM test_table WHERE name = 'test2');