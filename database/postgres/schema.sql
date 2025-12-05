/* users table */
create table users (
    user_id serial primary key,
    email varchar(255) unique not null,
    password varchar(255) not null,
    first_name varchar(100),
    last_name varchar(100),
    created_at timestamp default current_timestamp
);

/* inventory table */
create table inventory (
    sku varchar(100) primary key,
    mongo_product_id varchar(100) not null,
    stock_level int default 0 check (stock_level >= 0),
    price decimal(10, 2) not null,
    last_updated timestamp default current_timestamp
);

/* orders table */
create table orders (
    order_id serial primary key,
    user_id int references users(user_id),
    status varchar(50) not null,
    tax_amount decimal(10, 2) default 0.00,
    shipping_cost decimal(10, 2) default 0.00,
    total_amount decimal(10, 2) default 0.00,
    created_at timestamp default current_timestamp
);

/* order items table */
create table order_items (
    order_item_id serial primary key,
    order_id int references orders(order_id) on delete cascade,
    sku varchar(100) references inventory(sku),
    mongo_product_id varchar(100), 
    quantity int not null,
    unit_price_at_purchase decimal(10, 2) not null
);

/* payments table */
create table payments (
    payment_id serial primary key,
    order_id int references orders(order_id),
    amount decimal(10, 2) not null,
    provider varchar(50), /* stripe, paypal */
    status varchar(50), /* success, failed */
    transaction_date timestamp default current_timestamp
);

/* shipments table */
create table shipments (
    shipment_id serial primary key,
    order_id int references orders(order_id),
    tracking_number varchar(100),
    carrier varchar(50),
    shipping_method varchar(50),
    ship_date timestamp,
    estimated_arrival timestamp,
    delivery_address text
);

/* returns table */
create table returns (
    return_id serial primary key,
    order_id int references orders(order_id),
    sku varchar(100) references inventory(sku),
    quantity int not null default 1,
    reason text,
    refund_amount decimal(10, 2),
    status varchar(50)
);