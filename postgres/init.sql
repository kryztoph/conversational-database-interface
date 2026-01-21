-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Chat history table for storing conversation context
CREATE TABLE IF NOT EXISTS chat_history (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_session_id ON chat_history(session_id);
CREATE INDEX IF NOT EXISTS idx_timestamp ON chat_history(timestamp);

-- Documents table for RAG with vector embeddings
CREATE TABLE IF NOT EXISTS documents (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    metadata JSONB,
    embedding vector(384),  -- Adjust dimension based on your embedding model
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_embedding ON documents USING ivfflat (embedding vector_cosine_ops);

-- Sample e-commerce schema for demonstration

-- Customers table
CREATE TABLE IF NOT EXISTS customers (
    customer_id SERIAL PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(20),
    registration_date DATE DEFAULT CURRENT_DATE,
    total_spent DECIMAL(10, 2) DEFAULT 0.00
);

-- Products table
CREATE TABLE IF NOT EXISTS products (
    product_id SERIAL PRIMARY KEY,
    product_name VARCHAR(255) NOT NULL,
    category VARCHAR(100),
    price DECIMAL(10, 2) NOT NULL,
    stock_quantity INTEGER DEFAULT 0,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Orders table
CREATE TABLE IF NOT EXISTS orders (
    order_id SERIAL PRIMARY KEY,
    customer_id INTEGER REFERENCES customers(customer_id),
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_amount DECIMAL(10, 2) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    shipping_address TEXT
);

-- Order items table
CREATE TABLE IF NOT EXISTS order_items (
    order_item_id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(order_id),
    product_id INTEGER REFERENCES products(product_id),
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL,
    subtotal DECIMAL(10, 2) NOT NULL
);

-- Insert sample customers
INSERT INTO customers (first_name, last_name, email, phone, registration_date, total_spent) VALUES
('John', 'Doe', 'john.doe@example.com', '555-0101', '2024-01-15', 1250.00),
('Jane', 'Smith', 'jane.smith@example.com', '555-0102', '2024-02-20', 890.50),
('Bob', 'Johnson', 'bob.johnson@example.com', '555-0103', '2024-03-10', 2340.75),
('Alice', 'Williams', 'alice.williams@example.com', '555-0104', '2024-04-05', 560.00),
('Charlie', 'Brown', 'charlie.brown@example.com', '555-0105', '2024-05-12', 1120.25);

-- Insert sample products
INSERT INTO products (product_name, category, price, stock_quantity, description) VALUES
('Laptop Pro 15"', 'Electronics', 1299.99, 25, 'High-performance laptop with 16GB RAM and 512GB SSD'),
('Wireless Mouse', 'Electronics', 29.99, 150, 'Ergonomic wireless mouse with USB receiver'),
('Mechanical Keyboard', 'Electronics', 89.99, 75, 'RGB mechanical keyboard with Cherry MX switches'),
('USB-C Hub', 'Electronics', 49.99, 100, '7-in-1 USB-C hub with HDMI and USB 3.0 ports'),
('Laptop Stand', 'Accessories', 39.99, 60, 'Adjustable aluminum laptop stand'),
('Office Chair', 'Furniture', 299.99, 30, 'Ergonomic office chair with lumbar support'),
('Standing Desk', 'Furniture', 499.99, 15, 'Electric height-adjustable standing desk'),
('Desk Lamp', 'Accessories', 34.99, 80, 'LED desk lamp with adjustable brightness'),
('Monitor 27"', 'Electronics', 349.99, 40, '4K IPS monitor with HDR support'),
('Webcam HD', 'Electronics', 79.99, 55, '1080p webcam with built-in microphone');

-- Insert sample orders
INSERT INTO orders (customer_id, order_date, total_amount, status, shipping_address) VALUES
(1, '2024-06-01 10:30:00', 1329.98, 'delivered', '123 Main St, Springfield, IL 62701'),
(2, '2024-06-05 14:15:00', 439.98, 'delivered', '456 Oak Ave, Portland, OR 97201'),
(3, '2024-06-10 09:45:00', 849.97, 'shipped', '789 Pine Rd, Austin, TX 78701'),
(4, '2024-06-15 16:20:00', 559.98, 'processing', '321 Elm St, Seattle, WA 98101'),
(1, '2024-06-20 11:00:00', 89.99, 'delivered', '123 Main St, Springfield, IL 62701');

-- Insert sample order items
INSERT INTO order_items (order_id, product_id, quantity, unit_price, subtotal) VALUES
-- Order 1
(1, 1, 1, 1299.99, 1299.99),
(1, 2, 1, 29.99, 29.99),
-- Order 2
(2, 6, 1, 299.99, 299.99),
(2, 8, 4, 34.99, 139.96),
-- Order 3
(3, 7, 1, 499.99, 499.99),
(3, 9, 1, 349.99, 349.99),
-- Order 4
(4, 1, 1, 1299.99, 1299.99),
(4, 3, 1, 89.99, 89.99),
(4, 4, 1, 49.99, 49.99),
(4, 5, 1, 39.99, 39.99),
(4, 10, 1, 79.99, 79.99),
-- Order 5
(5, 3, 1, 89.99, 89.99);

-- Insert sample documents for RAG
INSERT INTO documents (content, metadata) VALUES
('Our company offers a 30-day return policy on all products. Items must be unused and in original packaging.', '{"type": "policy", "category": "returns"}'),
('Standard shipping takes 5-7 business days. Express shipping is available for 2-3 day delivery.', '{"type": "policy", "category": "shipping"}'),
('Customer support is available Monday-Friday 9AM-5PM EST. You can reach us at support@example.com or 1-800-SUPPORT.', '{"type": "info", "category": "support"}'),
('All electronics come with a 1-year manufacturer warranty. Extended warranties are available for purchase.', '{"type": "policy", "category": "warranty"}'),
('We accept Visa, Mastercard, American Express, PayPal, and Apple Pay. All transactions are encrypted and secure.', '{"type": "info", "category": "payment"}'),
('Our best-selling products include the Laptop Pro 15", Standing Desk, and Office Chair. These items are frequently purchased together.', '{"type": "info", "category": "products"}'),
('To track your order, visit our website and enter your order number and email address in the tracking section.', '{"type": "info", "category": "orders"}'),
('We offer bulk discounts for orders of 10 or more units of the same product. Contact sales@example.com for a quote.', '{"type": "policy", "category": "pricing"}');

-- Create useful views
CREATE VIEW customer_order_summary AS
SELECT
    c.customer_id,
    c.first_name,
    c.last_name,
    c.email,
    COUNT(DISTINCT o.order_id) as total_orders,
    SUM(o.total_amount) as total_spent,
    MAX(o.order_date) as last_order_date
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id
GROUP BY c.customer_id, c.first_name, c.last_name, c.email;

CREATE VIEW product_sales_summary AS
SELECT
    p.product_id,
    p.product_name,
    p.category,
    p.price,
    p.stock_quantity,
    COALESCE(SUM(oi.quantity), 0) as total_sold,
    COALESCE(SUM(oi.subtotal), 0) as total_revenue
FROM products p
LEFT JOIN order_items oi ON p.product_id = oi.product_id
GROUP BY p.product_id, p.product_name, p.category, p.price, p.stock_quantity;

-- Grant necessary permissions (if needed)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO cgiuser;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO cgiuser;
