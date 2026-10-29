-- question: Who are the 10 highest-spending customers?
-- notes: INNER JOIN Customer to Invoice. Every invoice has a customer (the foreign key is NOT NULL), so no rows are lost.
SELECT c.CustomerId,
       c.FirstName || ' ' || c.LastName AS customer,
       c.Country,
       COUNT(i.InvoiceId)               AS invoices,
       ROUND(SUM(i.Total), 2)           AS lifetime_spend
FROM Customer AS c
JOIN Invoice  AS i ON i.CustomerId = c.CustomerId
GROUP BY c.CustomerId, c.FirstName, c.LastName, c.Country
ORDER BY lifetime_spend DESC, c.CustomerId
LIMIT 10;
