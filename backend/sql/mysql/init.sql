CREATE TABLE IF NOT EXISTS financial_actuals (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    company_code VARCHAR(64) NOT NULL,
    period_name CHAR(7) NOT NULL,
    account_code VARCHAR(64) NOT NULL,
    actual_amount DECIMAL(18,2) NOT NULL,
    UNIQUE KEY uq_financial_actual (company_code, period_name, account_code)
);

INSERT IGNORE INTO financial_actuals (company_code, period_name, account_code, actual_amount) VALUES
    ('FINTECH_PAY', '2026-01', 'REVENUE', 2080000.00),
    ('FINTECH_PAY', '2026-01', 'COGS', 760000.00),
    ('FINTECH_PAY', '2026-01', 'EBITDA', 482000.00);
