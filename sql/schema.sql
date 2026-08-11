-- Schema gerado automaticamente a partir dos CSVs de origem
-- Gerado em: 2026-08-11T14:16:49.542117
-- Banco de destino: PostgreSQL

DROP TABLE IF EXISTS addresses;
CREATE TABLE addresses (
    id INTEGER NOT NULL,
    customer_id INTEGER NOT NULL,
    address_type VARCHAR(255) NOT NULL,
    postal_code VARCHAR(255) NOT NULL,
    street VARCHAR(255) NOT NULL,
    number INTEGER NOT NULL,
    complement VARCHAR(255),
    district VARCHAR(255) NOT NULL,
    city VARCHAR(255) NOT NULL,
    state VARCHAR(255) NOT NULL,
    country VARCHAR(255) NOT NULL,
    is_primary BOOLEAN NOT NULL,
    PRIMARY KEY (id)
);

DROP TABLE IF EXISTS attributes;
CREATE TABLE attributes (
    id INTEGER NOT NULL,
    name VARCHAR(255) NOT NULL,
    data_type VARCHAR(255) NOT NULL,
    PRIMARY KEY (id)
);

DROP TABLE IF EXISTS brands;
CREATE TABLE brands (
    id INTEGER NOT NULL,
    name VARCHAR(255) NOT NULL,
    country VARCHAR(255),
    is_active BOOLEAN NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    PRIMARY KEY (id)
);

DROP TABLE IF EXISTS categories;
CREATE TABLE categories (
    id INTEGER NOT NULL,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) NOT NULL,
    parent_category_id INTEGER,
    is_active BOOLEAN NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    PRIMARY KEY (id)
);

DROP TABLE IF EXISTS customers;
CREATE TABLE customers (
    id INTEGER NOT NULL,
    person_type VARCHAR(255) NOT NULL,
    legal_name VARCHAR(255) NOT NULL,
    trade_name VARCHAR(255),
    tax_id VARCHAR(255) NOT NULL,
    state_registration VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(255),
    is_active BOOLEAN NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    PRIMARY KEY (id)
);

DROP TABLE IF EXISTS employees;
CREATE TABLE employees (
    id INTEGER NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    cpf VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    role VARCHAR(255) NOT NULL,
    primary_location_id INTEGER NOT NULL,
    hire_date DATE NOT NULL,
    termination_date DATE,
    is_active BOOLEAN NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    PRIMARY KEY (id)
);

DROP TABLE IF EXISTS fiscal_invoices;
CREATE TABLE fiscal_invoices (
    id INTEGER NOT NULL,
    order_id INTEGER NOT NULL,
    nfe_number VARCHAR(255) NOT NULL,
    nfe_access_key VARCHAR(255) NOT NULL,
    series INTEGER NOT NULL,
    issued_at TIMESTAMP NOT NULL,
    status VARCHAR(255) NOT NULL,
    total_amount NUMERIC(18,4) NOT NULL,
    xml_storage_uri VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    PRIMARY KEY (id)
);

DROP TABLE IF EXISTS goods_receipt_items;
CREATE TABLE goods_receipt_items (
    id INTEGER NOT NULL,
    goods_receipt_id INTEGER NOT NULL,
    purchase_order_item_id INTEGER NOT NULL,
    quantity_received NUMERIC(18,4) NOT NULL,
    PRIMARY KEY (id)
);

DROP TABLE IF EXISTS goods_receipts;
CREATE TABLE goods_receipts (
    id INTEGER NOT NULL,
    purchase_order_id INTEGER NOT NULL,
    received_by_employee_id INTEGER NOT NULL,
    received_at TIMESTAMP NOT NULL,
    notes VARCHAR(255),
    created_at TIMESTAMP NOT NULL,
    PRIMARY KEY (id)
);

DROP TABLE IF EXISTS locations;
CREATE TABLE locations (
    id INTEGER NOT NULL,
    name VARCHAR(255) NOT NULL,
    location_type VARCHAR(255) NOT NULL,
    postal_code VARCHAR(255) NOT NULL,
    street VARCHAR(255) NOT NULL,
    number INTEGER NOT NULL,
    complement VARCHAR(255),
    district VARCHAR(255) NOT NULL,
    city VARCHAR(255) NOT NULL,
    state VARCHAR(255) NOT NULL,
    country VARCHAR(255) NOT NULL,
    is_active BOOLEAN NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    PRIMARY KEY (id)
);

DROP TABLE IF EXISTS order_items;
CREATE TABLE order_items (
    id INTEGER NOT NULL,
    order_id INTEGER NOT NULL,
    product_variant_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price NUMERIC(18,4) NOT NULL,
    icms_rate NUMERIC(18,4) NOT NULL,
    ipi_rate NUMERIC(18,4) NOT NULL,
    line_total NUMERIC(18,4) NOT NULL,
    PRIMARY KEY (id)
);

DROP TABLE IF EXISTS orders;
CREATE TABLE orders (
    id INTEGER NOT NULL,
    order_number VARCHAR(255) NOT NULL,
    channel VARCHAR(255) NOT NULL,
    customer_id INTEGER NOT NULL,
    salesperson_id INTEGER,
    location_id INTEGER NOT NULL,
    status VARCHAR(255) NOT NULL,
    subtotal NUMERIC(18,4) NOT NULL,
    discount_amount NUMERIC(18,4) NOT NULL,
    total NUMERIC(18,4) NOT NULL,
    placed_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    PRIMARY KEY (id)
);

DROP TABLE IF EXISTS payments;
CREATE TABLE payments (
    id INTEGER NOT NULL,
    order_id INTEGER NOT NULL,
    method VARCHAR(255) NOT NULL,
    installments INTEGER NOT NULL,
    amount NUMERIC(18,4) NOT NULL,
    status VARCHAR(255) NOT NULL,
    paid_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    PRIMARY KEY (id)
);

DROP TABLE IF EXISTS product_suppliers;
CREATE TABLE product_suppliers (
    product_variant_id INTEGER NOT NULL,
    supplier_id INTEGER NOT NULL,
    supplier_sku VARCHAR(255),
    last_quoted_cost NUMERIC(18,4) NOT NULL,
    lead_time_days INTEGER NOT NULL,
    is_preferred BOOLEAN NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);

DROP TABLE IF EXISTS product_variants;
CREATE TABLE product_variants (
    id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    sku VARCHAR(255) NOT NULL,
    barcode_ean VARCHAR(255),
    sale_price NUMERIC(18,4) NOT NULL,
    cost_price NUMERIC(18,4) NOT NULL,
    weight_kg NUMERIC(18,4) NOT NULL,
    icms_rate NUMERIC(18,4) NOT NULL,
    ipi_rate NUMERIC(18,4) NOT NULL,
    is_active BOOLEAN NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    PRIMARY KEY (id)
);

DROP TABLE IF EXISTS products;
CREATE TABLE products (
    id INTEGER NOT NULL,
    name VARCHAR(255) NOT NULL,
    description VARCHAR(255),
    brand_id INTEGER NOT NULL,
    category_id INTEGER NOT NULL,
    ncm_code INTEGER NOT NULL,
    unit_of_measure VARCHAR(255) NOT NULL,
    is_active BOOLEAN NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    PRIMARY KEY (id)
);

DROP TABLE IF EXISTS purchase_order_items;
CREATE TABLE purchase_order_items (
    id INTEGER NOT NULL,
    purchase_order_id INTEGER NOT NULL,
    product_variant_id INTEGER NOT NULL,
    quantity_ordered INTEGER NOT NULL,
    unit_cost NUMERIC(18,4) NOT NULL,
    line_total NUMERIC(18,4) NOT NULL,
    PRIMARY KEY (id)
);

DROP TABLE IF EXISTS purchase_orders;
CREATE TABLE purchase_orders (
    id INTEGER NOT NULL,
    po_number VARCHAR(255) NOT NULL,
    supplier_id INTEGER NOT NULL,
    buyer_id INTEGER NOT NULL,
    destination_location_id INTEGER NOT NULL,
    status VARCHAR(255) NOT NULL,
    currency VARCHAR(255) NOT NULL,
    subtotal NUMERIC(18,4) NOT NULL,
    total NUMERIC(18,4) NOT NULL,
    placed_at TIMESTAMP NOT NULL,
    expected_delivery_at DATE,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    PRIMARY KEY (id)
);

DROP TABLE IF EXISTS return_items;
CREATE TABLE return_items (
    id INTEGER NOT NULL,
    return_id INTEGER NOT NULL,
    order_item_id INTEGER NOT NULL,
    quantity NUMERIC(18,4) NOT NULL,
    action VARCHAR(255) NOT NULL,
    exchange_variant_id INTEGER,
    unit_refund_amount NUMERIC(18,4) NOT NULL,
    PRIMARY KEY (id)
);

DROP TABLE IF EXISTS returns;
CREATE TABLE returns (
    id INTEGER NOT NULL,
    return_number VARCHAR(255) NOT NULL,
    order_id INTEGER NOT NULL,
    customer_id INTEGER NOT NULL,
    received_at_location_id INTEGER NOT NULL,
    status VARCHAR(255) NOT NULL,
    reason VARCHAR(255),
    total_refund_amount NUMERIC(18,4) NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    PRIMARY KEY (id)
);

DROP TABLE IF EXISTS stock_levels;
CREATE TABLE stock_levels (
    product_variant_id INTEGER NOT NULL,
    location_id INTEGER NOT NULL,
    quantity_on_hand NUMERIC(18,4) NOT NULL,
    reorder_point TEXT,
    updated_at TIMESTAMP NOT NULL
);

DROP TABLE IF EXISTS stock_movements;
CREATE TABLE stock_movements (
    id INTEGER NOT NULL,
    product_variant_id INTEGER NOT NULL,
    location_id INTEGER NOT NULL,
    movement_type VARCHAR(255) NOT NULL,
    quantity NUMERIC(18,4) NOT NULL,
    reference_table VARCHAR(255),
    reference_id INTEGER,
    employee_id INTEGER,
    notes VARCHAR(255),
    occurred_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP NOT NULL,
    PRIMARY KEY (id)
);

DROP TABLE IF EXISTS suppliers;
CREATE TABLE suppliers (
    id INTEGER NOT NULL,
    legal_name VARCHAR(255) NOT NULL,
    trade_name VARCHAR(255),
    country VARCHAR(255) NOT NULL,
    tax_id VARCHAR(255) NOT NULL,
    tax_id_type VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    phone VARCHAR(255) NOT NULL,
    contact_name VARCHAR(255) NOT NULL,
    is_active BOOLEAN NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    PRIMARY KEY (id)
);

DROP TABLE IF EXISTS variant_attribute_values;
CREATE TABLE variant_attribute_values (
    product_variant_id INTEGER NOT NULL,
    attribute_id INTEGER NOT NULL,
    value VARCHAR(255) NOT NULL
);
