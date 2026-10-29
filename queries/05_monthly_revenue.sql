-- question: How does revenue move month by month?
-- notes: strftime turns the invoice timestamp into a year-month bucket. Months without invoices do not appear (there is no calendar table), so gaps must be read as zero.
SELECT strftime('%Y-%m', InvoiceDate) AS month,
       COUNT(*)                       AS invoices,
       ROUND(SUM(Total), 2)           AS revenue
FROM Invoice
GROUP BY month
ORDER BY month;
