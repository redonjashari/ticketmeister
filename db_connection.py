import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    connection = pymysql.connect(
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        port=int(os.getenv('DB_PORT')),
        password=os.getenv('DB_PASS'),
        database=os.getenv('DB_NAME'),
    )
    connection.connect()
    return connection

# def prepare_tables():
#     connection = get_db_connection()

#     queries = """
#     CREATE TABLE IF NOT EXISTS persons (
#     person_id       INT AUTO_INCREMENT PRIMARY KEY,
#     first_name      VARCHAR(100) NOT NULL,
#     last_name       VARCHAR(100) NOT NULL,
#     email           VARCHAR(255) UNIQUE,
#     phone           VARCHAR(30),
#     date_of_birth   DATE,
#     created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
#     ) ENGINE=InnoDB;

#     CREATE TABLE IF NOT EXISTS customers (
#         person_id       INT PRIMARY KEY,
#         loyalty_points  INT DEFAULT 0,
#         CONSTRAINT fk_customers_person FOREIGN KEY (person_id) REFERENCES persons(person_id) ON DELETE CASCADE
#     ) ENGINE=InnoDB;

#     CREATE TABLE IF NOT EXISTS staff (
#         person_id       INT PRIMARY KEY,
#         employee_number VARCHAR(50) UNIQUE,
#         hire_date       DATE,
#         staff_role            VARCHAR(100),
#         CONSTRAINT fk_staff_person FOREIGN KEY (person_id) REFERENCES persons(person_id) ON DELETE CASCADE
#     ) ENGINE=InnoDB;

#     CREATE TABLE IF NOT EXISTS artists (
#         person_id       INT PRIMARY KEY,
#         stage_name      VARCHAR(200),
#         bio             TEXT,
#         CONSTRAINT fk_artists_person FOREIGN KEY (person_id) REFERENCES persons(person_id) ON DELETE CASCADE
#     ) ENGINE=InnoDB;

#     CREATE TABLE IF NOT EXISTS venues (
#         venue_id        INT AUTO_INCREMENT PRIMARY KEY,
#         v_name            VARCHAR(200) NOT NULL,
#         v_address         TEXT,
#         city            VARCHAR(100),
#         country         VARCHAR(100),
#         capacity        INT UNSIGNED,
#         created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
#         CONSTRAINT chk_venue_capacity CHECK (capacity IS NULL OR capacity >= 0)
#     ) ENGINE=InnoDB;

#     CREATE TABLE IF NOT EXISTS seats (
#         seat_id         INT AUTO_INCREMENT PRIMARY KEY,
#         venue_id        INT NOT NULL,
#         seat_section       VARCHAR(50),
#         row_label       VARCHAR(10),
#         seat_number     VARCHAR(10),
#         seat_label      VARCHAR(100),
#         is_accessible   TINYINT(1) DEFAULT 0,
#         CONSTRAINT uq_seat_venue_section_row_seat UNIQUE (venue_id, seat_section, row_label, seat_number),
#         CONSTRAINT fk_seats_venue FOREIGN KEY (venue_id) REFERENCES venues(venue_id) ON DELETE CASCADE
#     ) ENGINE=InnoDB;

#     CREATE TABLE IF NOT EXISTS events (
#         event_id        INT AUTO_INCREMENT PRIMARY KEY,
#         title           VARCHAR(255) NOT NULL,
#         e_description     TEXT,
#         venue_id        INT NOT NULL,
#         start_time      DATETIME NOT NULL,
#         end_time        DATETIME,
#         e_status          VARCHAR(20) NOT NULL DEFAULT 'scheduled',
#         CONSTRAINT fk_events_venue FOREIGN KEY (venue_id) REFERENCES venues(venue_id) ON DELETE RESTRICT,
#         CONSTRAINT chk_event_status CHECK (e_status IN ('scheduled','postponed','cancelled','finished')),
#         CONSTRAINT chk_event_times CHECK (end_time IS NULL OR end_time >= start_time)
#     ) ENGINE=InnoDB;


#     -- Events ISA
#     CREATE TABLE IF NOT EXISTS concert_events (
#         event_id        INT NOT NULL,
#         genre           VARCHAR(100),
#         is_outdoor      TINYINT(1) DEFAULT 0,
#         headliner_id    INT NULL,
#         PRIMARY KEY (event_id),
#         CONSTRAINT fk_concerts_event FOREIGN KEY (event_id) REFERENCES events(event_id) ON DELETE CASCADE,
#         CONSTRAINT fk_concerts_headliner FOREIGN KEY (headliner_id) REFERENCES artists(person_id) ON DELETE SET NULL
#     ) ENGINE=InnoDB;

#     CREATE TABLE IF NOT EXISTS festival (
#         event_id        INT NOT NULL,
#         festival_name      VARCHAR(100),
#         PRIMARY KEY (event_id),
#         CONSTRAINT fk_festival_event FOREIGN KEY (event_id) REFERENCES events(event_id) ON DELETE CASCADE
#     ) ENGINE=InnoDB;


#     -- Tickets for the events
#     CREATE TABLE IF NOT EXISTS tickets (
#         ticket_id       INT AUTO_INCREMENT PRIMARY KEY,
#         event_id        INT NOT NULL,
#         seat_id         INT NULL,
#         person_id       INT NULL,
#         face_value      DECIMAL(10,2) NOT NULL DEFAULT 0.00,
#         currency        CHAR(3) DEFAULT 'EUR',
#         ticket_status          VARCHAR(20) NOT NULL DEFAULT 'available',
#         issued_at       DATETIME,
#         created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
#         CONSTRAINT uq_event_seat UNIQUE (event_id, seat_id),
#         CONSTRAINT fk_tickets_event FOREIGN KEY (event_id) REFERENCES events(event_id) ON DELETE CASCADE,
#         CONSTRAINT fk_tickets_seat FOREIGN KEY (seat_id) REFERENCES seats(seat_id) ON DELETE RESTRICT,
#         CONSTRAINT fk_tickets_person FOREIGN KEY (person_id) REFERENCES persons(person_id) ON DELETE SET NULL,
#         CONSTRAINT chk_ticket_status CHECK (ticket_status IN ('available','reserved','sold','cancelled'))
#     ) ENGINE=InnoDB;

#     -- Tickets ISA
#     CREATE TABLE IF NOT EXISTS regular_tickets (
#         ticket_id       INT PRIMARY KEY,
#         refundable      TINYINT(1) DEFAULT 0,
#         refund_deadline DATETIME,
#         CONSTRAINT fk_regular_ticket FOREIGN KEY (ticket_id) REFERENCES tickets(ticket_id) ON DELETE CASCADE
#     ) ENGINE=InnoDB;

#     CREATE TABLE IF NOT EXISTS vip_tickets (
#         ticket_id       INT PRIMARY KEY,
#         perks            TEXT,
#         lounge_access    TINYINT(1) DEFAULT 1,
#         vip_level        VARCHAR(50),
#         CONSTRAINT fk_vip_ticket FOREIGN KEY (ticket_id) REFERENCES tickets(ticket_id) ON DELETE CASCADE
#     ) ENGINE=InnoDB;


#     -- Purchases & payments
#     CREATE TABLE IF NOT EXISTS purchases (
#         purchase_id     INT AUTO_INCREMENT PRIMARY KEY,
#         customer_id     INT NOT NULL,
#         purchase_time   DATETIME DEFAULT CURRENT_TIMESTAMP,
#         total_amount    DECIMAL(12,2) NOT NULL,
#         purch_status          VARCHAR(20) DEFAULT 'pending',
#         CONSTRAINT fk_purchases_customer FOREIGN KEY (customer_id) REFERENCES customers(person_id) ON DELETE RESTRICT,
#         CONSTRAINT chk_purchase_status CHECK (purch_status IN ('pending','completed','refunded','cancelled')),
#         CONSTRAINT chk_total_amount_nonnegative CHECK (total_amount >= 0)
#     ) ENGINE=InnoDB;

#     CREATE TABLE IF NOT EXISTS payments (
#         payment_id      INT AUTO_INCREMENT PRIMARY KEY,
#         purchase_id     INT NOT NULL,
#         amount          DECIMAL(12,2) NOT NULL,
#         method          VARCHAR(50) NOT NULL,
#         transaction_ref VARCHAR(255),
#         paid_at         DATETIME DEFAULT CURRENT_TIMESTAMP,
#         payment_status          VARCHAR(20) DEFAULT 'ok',
#         CONSTRAINT fk_payments_purchase FOREIGN KEY (purchase_id) REFERENCES purchases(purchase_id) ON DELETE CASCADE,
#         CONSTRAINT chk_payment_status CHECK (payment_status IN ('ok','failed','pending','refunded')),
#         CONSTRAINT chk_payment_amount_nonnegative CHECK (amount >= 0)
#     ) ENGINE=InnoDB;


#     -- Purchase items
#     CREATE TABLE IF NOT EXISTS purchase_items (
#         purchase_item_id INT AUTO_INCREMENT PRIMARY KEY,
#         purchase_id      INT NOT NULL,
#         ticket_id        INT NOT NULL,
#         price_paid       DECIMAL(10,2) NOT NULL,
#         CONSTRAINT fk_purchase_items_purchase FOREIGN KEY (purchase_id) REFERENCES purchases(purchase_id) ON DELETE CASCADE,
#         CONSTRAINT fk_purchase_items_ticket FOREIGN KEY (ticket_id) REFERENCES tickets(ticket_id) ON DELETE RESTRICT,
#         CONSTRAINT uq_purchase_items_ticket UNIQUE (ticket_id),
#         CONSTRAINT chk_price_paid_nonnegative CHECK (price_paid >= 0)
#     ) ENGINE=InnoDB;


#     -- Performances
#     CREATE TABLE IF NOT EXISTS performances (
#         performance_id  INT AUTO_INCREMENT PRIMARY KEY,
#         artist_id       INT NOT NULL,
#         event_id        INT NOT NULL,
#         set_order       INT,
#         is_headliner    TINYINT(1) DEFAULT 0,
#         performance_role            VARCHAR(100),
#         CONSTRAINT fk_performances_artist FOREIGN KEY (artist_id) REFERENCES artists(person_id) ON DELETE CASCADE,
#         CONSTRAINT fk_performances_event FOREIGN KEY (event_id) REFERENCES events(event_id) ON DELETE CASCADE,
#         CONSTRAINT uq_artist_event_setorder UNIQUE (artist_id, event_id, set_order)
#     ) ENGINE=InnoDB;


#     -- Event organizers
#     CREATE TABLE IF NOT EXISTS event_organizers (
#         event_organizer_id INT AUTO_INCREMENT PRIMARY KEY,
#         event_id           INT NOT NULL,
#         person_id          INT NOT NULL,
#         person_role               VARCHAR(100),
#         assigned_at        DATETIME DEFAULT CURRENT_TIMESTAMP,
#         CONSTRAINT fk_event_organizers_event FOREIGN KEY (event_id) REFERENCES events(event_id) ON DELETE CASCADE,
#         CONSTRAINT fk_event_organizers_person FOREIGN KEY (person_id) REFERENCES persons(person_id) ON DELETE CASCADE,
#         CONSTRAINT uq_event_person UNIQUE (event_id, person_id)
#     ) ENGINE=InnoDB;
#     """

#     try:
#         cursor = connection.cursor()
#         for query in queries.strip().split(';'):
#             if query.strip():
#                 cursor.execute(query)
#         connection.commit()
#         print("Tables prepared successfully.")
#     except Exception as e:
#         print(f"An error occurred while preparing tables: {e}")
#     finally:
#         cursor.close()
#         connection.close()

# prepare_tables()
