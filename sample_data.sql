SET FOREIGN_KEY_CHECKS = 0;

-- ---------------------------
-- PERSONS (people used as customers, staff, artists, organizers)
-- ---------------------------
INSERT INTO persons (person_id, first_name, last_name, email, phone, date_of_birth, created_at) VALUES
(1, 'Alice', 'Müller', 'alice@example.com', '+49 30 1111111', '1992-04-12', '2025-08-01 09:00:00'),
(2, 'Bob', 'Schmidt', 'bob@example.com', '+49 89 2222222', '1988-07-03', '2025-08-02 10:00:00'),
(3, 'Charlie', 'Becker', 'charlie@example.com', '+49 221 3333333', '1995-01-20', '2025-08-03 11:00:00'),
(4, 'Diana', 'Fischer', 'diana@example.com', '+49 69 4444444', '1990-11-02', '2025-08-04 12:00:00'),
(5, 'Elias', 'Braun', 'elias@example.com', '+49 40 5555555', '1998-05-18', '2025-08-05 13:00:00'),
(6, 'Franz', 'Keller', 'franz@example.com', '+49 30 6666666', '1985-02-14', '2025-08-06 14:00:00'),
(7, 'Greta', 'Weber', 'greta.staff@example.com', '+49 89 7777777', '1982-09-09', '2025-08-07 08:00:00'),
(8, 'Hannah', 'Wolf', 'hannah.staff@example.com', '+49 69 8888888', '1987-03-23', '2025-08-08 08:30:00'),
(9, 'Chris', 'Martin', 'chris@coldplay.example', '+44 20 9999999', '1977-03-02', '2025-08-09 09:30:00'),
(10, 'Abel', 'Tesfaye', 'abel@weeknd.example', '+1 416 1234567', '1990-02-16', '2025-08-10 10:15:00'),
(11, 'Dan', 'Reynolds', 'dan@imaginedragons.example', '+1 702 7654321', '1987-07-14', '2025-08-11 11:45:00'),
(12, 'Lena', 'Neumann', 'lena@example.com', '+49 40 1010101', '1996-12-01', '2025-08-12 15:00:00');

-- ---------------------------
-- CUSTOMERS (references persons)
-- ---------------------------
INSERT INTO customers (person_id, loyalty_points) VALUES
(1, 120),
(2, 50),
(3, 10),
(4, 200),
(5, 0),
(6, 5),
(12, 15);

-- ---------------------------
-- STAFF (references persons)
-- ---------------------------
INSERT INTO staff (person_id, employee_number, hire_date, staff_role) VALUES
(7, 'EMP-001', '2018-05-01', 'Venue Manager'),
(8, 'EMP-002', '2019-07-15', 'Box Office');

-- ---------------------------
-- ARTISTS (references persons)
-- ---------------------------
INSERT INTO artists (person_id, stage_name, bio) VALUES
(9, 'Coldplay (rep)', 'Coldplay representative for the tour.'),
(10, 'The Weeknd (rep)', 'The Weeknd representative for the tour.'),
(11, 'Imagine Dragons (rep)', 'Imagine Dragons representative for the tour.');

-- ---------------------------
-- VENUES
-- ---------------------------
INSERT INTO venues (venue_id, v_name, v_address, city, country, capacity, created_at) VALUES
(1, 'Berlin Arena', 'CampusRing 1', 'Berlin', 'Germany', 5000, '2024-12-01 09:00:00'),
(2, 'Munich Dome', 'Leopoldstraße 45', 'Munich', 'Germany', 7000, '2024-12-02 09:00:00'),
(3, 'Hamburg Hall', 'Reeperbahn 22', 'Hamburg', 'Germany', 4500, '2024-12-03 09:00:00'),
(4, 'Cologne Center', 'Domstraße 10', 'Cologne', 'Germany', 6000, '2024-12-04 09:00:00'),
(5, 'Frankfurt Pavilion', 'Mainufer 5', 'Frankfurt', 'Germany', 8000, '2024-12-05 09:00:00');

-- ---------------------------
-- SEATS
-- ---------------------------
INSERT INTO seats (seat_id, venue_id, seat_section, row_label, seat_number, seat_label, is_accessible) VALUES
(1, 1, 'A', '1', '1', 'A-1', 0),
(2, 1, 'A', '1', '2', 'A-2', 0),
(3, 1, 'A', '1', '3', 'A-3', 0),
(4, 2, 'B', '5', '10', 'B-5-10', 0),
(5, 2, 'B', '5', '11', 'B-5-11', 0),
(6, 3, 'C', '10', '1', 'C-10-1', 1),
(7, 3, 'C', '10', '2', 'C-10-2', 0),
(8, 4, 'Main', '1', '1', 'Main-1-1', 0),
(9, 5, 'Front', 'A', '1', 'Front-A-1', 0);

-- ---------------------------
-- EVENTS
-- ---------------------------
INSERT INTO events (event_id, title, e_description, venue_id, start_time, end_time, e_status) VALUES
(1, 'Coldplay Live in Berlin', 'Coldplay — Music of the Spheres tour with full production.', 1, '2025-11-10 19:30:00', '2025-11-10 22:30:00', 'scheduled'),
(2, 'The Weeknd World Tour', 'After Hours Til Dawn Tour - the biggest R&B show of the year.', 2, '2025-12-01 20:00:00', '2025-12-01 23:00:00', 'scheduled'),
(3, 'Imagine Dragons Night', 'A night of rock hits and spectacular lighting.', 3, '2025-10-15 19:00:00', '2025-10-15 22:00:00', 'scheduled'),
(4, 'Indie Evening', 'Local indie bands and support acts.', 1, '2025-10-18 18:30:00', '2025-10-18 21:00:00', 'scheduled'),
(5, 'Acoustic Sessions with Ed', 'Intimate acoustic set and Q&A.', 5, '2025-12-10 19:30:00', '2025-12-10 22:00:00', 'scheduled'),
(6, 'Charity Concert', 'City charity concert with multiple artists.', 4, '2025-11-05 18:00:00', '2025-11-05 21:30:00', 'scheduled');

-- ---------------------------
-- CONCERT_EVENTS (ISA table referencing events)
-- ---------------------------
INSERT INTO concert_events (event_id, genre, is_outdoor, headliner_id) VALUES
(1, 'Pop Rock', 0, 9),
(2, 'R&B/Pop', 0, 10),
(3, 'Alternative Rock', 0, 11),
(4, 'Indie', 0, NULL),
(5, 'Acoustic/Pop', 0, NULL),
(6, 'Mixed', 1, NULL);

-- ---------------------------
-- TICKETS (some seat-specific, some general admission)
-- ---------------------------
INSERT INTO tickets (ticket_id, event_id, seat_id, person_id, face_value, currency, ticket_status, issued_at, created_at) VALUES
(1, 1, 1, NULL, 80.00, 'EUR', 'sold', '2025-09-15 09:00:00', '2025-09-15 09:00:00'),
(2, 1, 2, NULL, 150.00, 'EUR', 'sold', '2025-09-15 09:00:00', '2025-09-15 09:00:00'),
(3, 2, 4, NULL, 90.00, 'EUR', 'sold', '2025-09-20 09:00:00', '2025-09-20 09:00:00'),
(4, 2, 5, NULL, 160.00, 'EUR', 'sold', '2025-09-25 09:00:00', '2025-09-25 09:00:00'),
(5, 3, 6, NULL, 70.00, 'EUR', 'sold', '2025-09-10 09:00:00', '2025-09-10 09:00:00'),
(6, 3, 7, NULL, 120.00, 'EUR', 'sold', '2025-09-11 09:00:00', '2025-09-11 09:00:00'),
(7, 4, NULL, NULL, 25.00, 'EUR', 'sold', '2025-09-14 09:00:00', '2025-09-14 09:00:00'), -- general admission
(8, 4, NULL, NULL, 40.00, 'EUR', 'sold', '2025-09-14 09:00:00', '2025-09-14 09:00:00'),
(9, 5, 9, NULL, 95.00, 'EUR', 'sold', '2025-09-20 09:00:00', '2025-09-20 09:00:00'),
(10, 5, NULL, NULL, 170.00, 'EUR', 'sold', '2025-09-25 09:00:00', '2025-09-25 09:00:00'),
(11, 6, 8, NULL, 50.00, 'EUR', 'sold', '2025-09-25 09:00:00', '2025-09-25 09:00:00'),
(12, 1, NULL, NULL, 85.00, 'EUR', 'available', NULL, '2025-09-30 09:00:00');

-- ---------------------------
-- REGULAR_TICKETS (subtype) and VIP_TICKETS
-- ---------------------------
INSERT INTO regular_tickets (ticket_id, refundable, refund_deadline) VALUES
(1, 1, '2025-11-01 23:59:59'),
(3, 1, '2025-11-15 23:59:59'),
(5, 0, NULL),
(7, 1, '2025-10-10 23:59:59');

INSERT INTO vip_tickets (ticket_id, perks, lounge_access, vip_level) VALUES
(2, 'Backstage pass, Priority entry', 1, 'Gold'),
(4, 'Meet & Greet, VIP lounge', 1, 'Platinum'),
(6, 'VIP seating, Drink voucher', 1, 'Gold'),
(10, 'Front row + acoustic lounge', 1, 'Diamond');

-- ---------------------------
-- PURCHASES
-- ---------------------------
INSERT INTO purchases (purchase_id, customer_id, purchase_time, total_amount, purch_status) VALUES
(1, 1, '2025-09-15 09:05:00', 80.00, 'completed'),
(2, 1, '2025-09-15 09:06:00', 150.00, 'completed'),
(3, 2, '2025-09-20 10:00:00', 90.00, 'completed'),
(4, 3, '2025-09-25 11:00:00', 160.00, 'completed'),
(5, 4, '2025-09-10 12:00:00', 70.00, 'completed'),
(6, 5, '2025-09-11 13:00:00', 120.00, 'completed'),
(7, 6, '2025-09-14 14:00:00', 25.00, 'completed'),
(8, 7, '2025-09-14 14:05:00', 40.00, 'completed'),
(9, 12, '2025-09-20 15:00:00', 95.00, 'completed'),
(10, 12, '2025-09-25 16:00:00', 170.00, 'completed'),
(11, 2, '2025-09-25 16:30:00', 50.00, 'completed'),
(12, 1, '2025-09-29 10:00:00', 85.00, 'pending'),
(13, 3, '2025-09-28 10:30:00', 60.00, 'pending');

-- ---------------------------
-- PAYMENTS
-- ---------------------------
INSERT INTO payments (payment_id, purchase_id, amount, method, transaction_ref, paid_at, payment_status) VALUES
(1, 1, 80.00, 'Credit Card', 'TX-0001', '2025-09-15 09:05:10', 'ok'),
(2, 2, 150.00, 'Credit Card', 'TX-0002', '2025-09-15 09:06:10', 'ok'),
(3, 3, 90.00, 'PayPal', 'TX-0003', '2025-09-20 10:02:00', 'ok'),
(4, 4, 160.00, 'Credit Card', 'TX-0004', '2025-09-25 11:03:00', 'ok'),
(5, 5, 70.00, 'Debit Card', 'TX-0005', '2025-09-10 12:05:00', 'ok'),
(6, 6, 120.00, 'Credit Card', 'TX-0006', '2025-09-11 13:03:00', 'ok'),
(7, 7, 25.00, 'Credit Card', 'TX-0007', '2025-09-14 14:02:00', 'ok'),
(8, 8, 40.00, 'PayPal', 'TX-0008', '2025-09-14 14:06:00', 'ok'),
(9, 9, 95.00, 'Credit Card', 'TX-0009', '2025-09-20 15:01:00', 'ok'),
(10, 10, 170.00, 'PayPal', 'TX-0010', '2025-09-25 16:01:00', 'ok'),
(11, 11, 50.00, 'Credit Card', 'TX-0011', '2025-09-25 16:31:00', 'ok'),
(12, 12, 85.00, 'Credit Card', 'TX-0012', '2025-09-29 10:05:00', 'pending'),
(13, 13, 60.00, 'Debit Card', 'TX-0013', '2025-09-28 10:35:00', 'pending');

-- ---------------------------
-- PURCHASE_ITEMS (links purchases to tickets)
-- ---------------------------
INSERT INTO purchase_items (purchase_item_id, purchase_id, ticket_id, price_paid) VALUES
(1, 1, 1, 80.00),
(2, 2, 2, 150.00),
(3, 3, 3, 90.00),
(4, 4, 4, 160.00),
(5, 5, 5, 70.00),
(6, 6, 6, 120.00),
(7, 7, 7, 25.00),
(8, 8, 8, 40.00),
(9, 9, 9, 95.00),
(10, 10, 10, 170.00),
(11, 11, 11, 50.00),
(12, 12, 12, 85.00),
(13, 13, 13, 60.00);

-- ---------------------------
-- PERFORMANCES (artists performing at events)
-- ---------------------------
INSERT INTO performances (performance_id, artist_id, event_id, set_order, is_headliner, performance_role) VALUES
(1, 9, 1, 1, 1, 'Headliner'),
(2, 10, 2, 1, 1, 'Headliner'),
(3, 11, 3, 1, 1, 'Headliner'),
(4, 9, 4, 2, 0, 'Support'),
(5, 11, 6, 1, 0, 'Guest');

-- ---------------------------
-- EVENT_ORGANIZERS (staff assigned to events)
-- ---------------------------
INSERT INTO event_organizers (event_organizer_id, event_id, person_id, person_role, assigned_at) VALUES
(1, 1, 7, 'Venue Manager', '2025-08-01 09:15:00'),
(2, 2, 8, 'Box Office Lead', '2025-08-02 09:20:00'),
(3, 3, 7, 'Logistics', '2025-08-03 09:25:00'),
(4, 6, 8, 'Coordinator', '2025-08-04 09:30:00');

SET FOREIGN_KEY_CHECKS = 1;
