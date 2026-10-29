-- question: How much revenue does each support representative's customer base generate?
-- notes: Employee -> Customer -> Invoice. LEFT JOINs keep employees with no customers (managers) in the output with zero instead of dropping them.
SELECT e.EmployeeId,
       e.FirstName || ' ' || e.LastName AS employee,
       e.Title,
       COUNT(DISTINCT c.CustomerId)      AS customers,
       COUNT(i.InvoiceId)                AS invoices,
       ROUND(COALESCE(SUM(i.Total), 0), 2) AS revenue
FROM Employee AS e
LEFT JOIN Customer AS c ON c.SupportRepId = e.EmployeeId
LEFT JOIN Invoice  AS i ON i.CustomerId   = c.CustomerId
GROUP BY e.EmployeeId
ORDER BY revenue DESC, e.EmployeeId;
