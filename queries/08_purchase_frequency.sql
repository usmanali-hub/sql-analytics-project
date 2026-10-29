-- question: How many customers have placed 1, 2, 3... invoices?
-- notes: Aggregate of an aggregate: count invoices per customer in a subquery, then count customers per invoice count. A customer with no invoices would appear as 0 because of the LEFT JOIN.
SELECT invoice_count,
       COUNT(*) AS customers
FROM (
    SELECT c.CustomerId, COUNT(i.InvoiceId) AS invoice_count
    FROM Customer AS c
    LEFT JOIN Invoice AS i ON i.CustomerId = c.CustomerId
    GROUP BY c.CustomerId
)
GROUP BY invoice_count
ORDER BY invoice_count;
