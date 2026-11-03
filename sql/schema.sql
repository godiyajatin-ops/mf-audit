BEGIN;

-- Benchmark dimension
CREATE TABLE IF NOT EXISTS dim_benchmark (
    benchmark_id INT PRIMARY KEY,
    name TEXT NOT NULL
);

-- Scheme dimension
CREATE TABLE IF NOT EXISTS dim_scheme (
    scheme_code INT PRIMARY KEY,
    scheme_name TEXT NOT NULL,
    amc TEXT NOT NULL,
    category TEXT NOT NULL,
    plan TEXT NOT NULL,
    option TEXT NOT NULL,
    pair_id INT NOT NULL,
    is_passive BOOLEAN NOT NULL,
    benchmark_id INT NOT NULL REFERENCES dim_benchmark(benchmark_id),
    inception DATE
);

-- Daily mutual fund NAV
CREATE TABLE IF NOT EXISTS fact_nav (
    scheme_code INT REFERENCES dim_scheme(scheme_code),
    nav_date DATE NOT NULL,
    nav NUMERIC(14,4) NOT NULL,
    PRIMARY KEY (scheme_code, nav_date)
);

-- Daily benchmark TRI
CREATE TABLE IF NOT EXISTS fact_benchmark_tri (
    benchmark_id INT REFERENCES dim_benchmark(benchmark_id),
    tri_date DATE NOT NULL,
    tri NUMERIC(16,4) NOT NULL,
    PRIMARY KEY (benchmark_id, tri_date)
);

-- Risk-free rate
CREATE TABLE IF NOT EXISTS fact_rf (
    rf_date DATE PRIMARY KEY,
    annual_rate NUMERIC(8,5) NOT NULL
);

-- Alpha results, populated in later stages
CREATE TABLE IF NOT EXISTS res_alpha (
    scheme_code INT,
    window_label TEXT,
    alpha_ann NUMERIC,
    beta NUMERIC,
    se_nw NUMERIC,
    p_value NUMERIC,
    p_bh NUMERIC,
    r2 NUMERIC,
    n_obs INT,
    PRIMARY KEY (scheme_code, window_label)
);

-- Document metadata, used in Stage B
CREATE TABLE IF NOT EXISTS dim_document (
    doc_id INT PRIMARY KEY,
    amc TEXT,
    doc_type TEXT,
    doc_date DATE,
    url TEXT,
    sha256 TEXT
);

-- Document chunks, used in Stage B
CREATE TABLE IF NOT EXISTS doc_chunk (
    chunk_id INT PRIMARY KEY,
    doc_id INT REFERENCES dim_document(doc_id),
    page INT,
    section TEXT,
    scheme_code INT,
    text TEXT
);

-- Read-only access for the existing reporting role
GRANT USAGE ON SCHEMA public TO mf_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO mf_readonly;

-- Future tables created by mf will also be readable
ALTER DEFAULT PRIVILEGES FOR ROLE mf IN SCHEMA public
GRANT SELECT ON TABLES TO mf_readonly;

COMMIT;
