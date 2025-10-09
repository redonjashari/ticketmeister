/*  For each event, show the total tickets sold and total revenue; 
only include events that sold more than 50 tickets. */
SELECT e.event_id,
       e.title,
       COUNT(DISTINCT t.ticket_id) AS tickets_sold,
       COALESCE(SUM(pay.amount), 0) AS total_revenue
FROM events e
JOIN tickets t ON t.event_id = e.event_id
JOIN purchase_items pi ON pi.ticket_id = t.ticket_id
JOIN purchases pu ON pu.purchase_id = pi.purchase_id
JOIN payments pay ON pay.purchase_id = pu.purchase_id
GROUP BY e.event_id, e.title
HAVING COUNT(DISTINCT t.ticket_id) > 50
ORDER BY total_revenue DESC;


/* For each upcoming event, show venue capacity,
tickets allocated, tickets sold, and remaining seats (capacity − sold). */ 
SELECT e.event_id,
       e.title,
       v.venue_id,
       v.capacity,
       COUNT(DISTINCT t.ticket_id) AS tickets_allocated,
       COALESCE(COUNT(DISTINCT pi.ticket_id), 0) AS tickets_sold,
       (v.capacity - COALESCE(COUNT(DISTINCT pi.ticket_id), 0)) AS seats_remaining
FROM events e
JOIN venues v ON e.venue_id = v.venue_id
LEFT JOIN tickets t ON t.event_id = e.event_id
LEFT JOIN purchase_items pi ON pi.ticket_id = t.ticket_id
WHERE e.start_time >= CURDATE()
GROUP BY e.event_id, e.title, v.venue_id, v.capacity
ORDER BY e.start_time;


-- Total events, tickets sold, and average ticket price in the last year
SELECT 
    COUNT(DISTINCT e.event_id) AS events_count,
    COUNT(DISTINCT pi.purchase_id) AS tickets_sold,
    AVG(t.face_value) AS avg_ticket_price
FROM events e
LEFT JOIN tickets t ON t.event_id = e.event_id
LEFT JOIN purchase_items pi ON pi.ticket_id = t.ticket_id
WHERE e.start_time >= DATE_SUB(CURDATE(), INTERVAL 1 YEAR);


-- Early sold tickets (sold > 20 days before event)
SELECT e.event_id,
       e.title,
       SUM(CASE WHEN DATEDIFF(e.start_time, pu.purchase_time) > 20 THEN 1 ELSE 0 END) AS early_sold,
       COUNT(DISTINCT pi.purchase_id) AS total_sold,
       (SUM(CASE WHEN DATEDIFF(e.start_time, pu.purchase_time) > 20 THEN 1 ELSE 0 END) / 
        NULLIF(COUNT(DISTINCT pi.purchase_id),0)) AS early_ratio
FROM events e
JOIN tickets t ON t.event_id = e.event_id
JOIN purchase_items pi ON pi.ticket_id = t.ticket_id
JOIN purchases pu ON pu.purchase_id = pi.purchase_id
GROUP BY e.event_id, e.title
HAVING early_ratio > 0.5;


-- List the top 10 customers by total spending in the last year
SELECT c.person_id AS customer_person_id,
       CONCAT(pers.first_name, ' ', pers.last_name) AS customer_name,
       COUNT(DISTINCT pu.purchase_id) AS purchases_count,
       COALESCE(SUM(pay.amount), 0) AS total_spent
FROM customers c
JOIN persons pers ON pers.person_id = c.person_id
JOIN purchases pu ON pu.customer_id = c.person_id
JOIN payments pay ON pay.purchase_id = pu.purchase_id
WHERE pay.paid_at >= DATE_SUB(CURDATE(), INTERVAL 12 MONTH)
GROUP BY c.person_id, customer_name
ORDER BY total_spent DESC
LIMIT 10;


-- For each artist, show the number of events they are scheduled to perform at this year.
SELECT a.person_id AS artist_person_id,
       COALESCE(a.stage_name, CONCAT(per.first_name, ' ', per.last_name)) AS artist_name,
       COUNT(DISTINCT e.event_id) AS events_this_year
FROM artists a
JOIN performances pf ON pf.artist_id = a.person_id
JOIN events e ON e.event_id = pf.event_id
LEFT JOIN persons per ON per.person_id = a.person_id
WHERE YEAR(e.start_time) = YEAR(CURDATE())
GROUP BY a.person_id, artist_name
ORDER BY events_this_year DESC;


-- Show the top 10 upcoming or current events with the highest number of tickets sold.
SELECT e.event_id,
       e.title AS event_title,
       e.start_time,
       v.v_name AS venue_name,
       COUNT(DISTINCT pi.purchase_id) AS tickets_sold
FROM events e
JOIN venues v ON e.venue_id = v.venue_id
JOIN tickets t ON e.event_id = t.event_id
JOIN purchase_items pi ON pi.ticket_id = t.ticket_id
WHERE e.start_time >= CURDATE()
GROUP BY e.event_id, e.title, e.start_time, v.v_name
ORDER BY tickets_sold DESC
LIMIT 10;


--Bottom 10 upcoming events by percent of venue capacity sold
SELECT e.event_id,
       e.title,
       e.start_time AS event_time,
       v.v_name AS venue,
       v.capacity,
       COALESCE(COUNT(DISTINCT pi.ticket_id),0) AS sold,
       ROUND(100.0 * COALESCE(COUNT(DISTINCT pi.ticket_id),0) / NULLIF(v.capacity,0),2) AS pct_sold
FROM events e
JOIN venues v ON v.venue_id = e.venue_id
LEFT JOIN tickets t ON t.event_id = e.event_id
LEFT JOIN purchase_items pi ON pi.ticket_id = t.ticket_id
WHERE e.start_time >= CURDATE()
GROUP BY e.event_id, e.title, e.start_time, v.v_name, v.capacity
ORDER BY pct_sold ASC
LIMIT 10;


--Top 5 events by total revenue in the last year
SELECT 
    e.event_id,
    e.title,
    COUNT(DISTINCT pi.purchase_id) AS tickets_sold,
    SUM(pi.price_paid) AS total_revenue
FROM events e
JOIN tickets t ON t.event_id = e.event_id
JOIN purchase_items pi ON pi.ticket_id = t.ticket_id
WHERE e.start_time >= DATE_SUB(CURDATE(), INTERVAL 1 YEAR)
GROUP BY e.event_id, e.title
ORDER BY total_revenue DESC
LIMIT 5;







