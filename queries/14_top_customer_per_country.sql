-- question: Who is the biggest-spending customer in each country with more than one customer?
-- notes: RANK() (not ROW_NUMBER) is used on purpose: if two customers tie for first in a country both are returned instead of one being dropped arbitrarily. COUNT() OVER a partition supplies the country's customer count without a second aggregation. Spend is rounded to cents before ranking because summed floating-point values can differ in the last bit between engines and silently break a tie (this was caught by the DuckDB portability test).
WITH customer_spend AS (
    SELECT c.CustomerId,
           c.FirstName || ' ' || c.LastName AS customer,
           c.Country,
           ROUND(SUM(i.Total), 2) AS spend
    FROM Customer AS c
    JOIN Invoice  AS i ON i.CustomerId = c.CustomerId
    GROUP BY c.CustomerId, c.FirstName, c.LastName, c.Country
),
ranked AS (
    SELECT Country, customer, spend,
           RANK()  OVER (PARTITION BY Country ORDER BY spend DESC) AS spend_rank,
           COUNT(*) OVER (PARTITION BY Country)                    AS customers_in_country
    FROM customer_spend
)
SELECT Country, customer, spend, customers_in_country
FROM ranked
WHERE spend_rank = 1 AND customers_in_country > 1
ORDER BY customers_in_country DESC, Country, customer;
