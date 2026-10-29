-- question: How many genres does it take to reach 80% of revenue?
-- notes: A Pareto table. Genres are ordered by revenue and a running SUM() OVER divides by the grand total to give the cumulative share. The ROWS frame is explicit: the default RANGE frame would treat genres with equal revenue as one block and jump the running total. The answer is the first row at or above 80%.
WITH genre_revenue AS (
    SELECT g.Name AS genre, SUM(il.UnitPrice * il.Quantity) AS revenue
    FROM InvoiceLine AS il
    JOIN Track AS t ON t.TrackId = il.TrackId
    JOIN Genre AS g ON g.GenreId = t.GenreId
    GROUP BY g.GenreId, g.Name
)
SELECT genre,
       ROUND(revenue, 2) AS revenue,
       ROUND(100.0 * SUM(revenue) OVER (ORDER BY revenue DESC, genre
                                        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)
             / SUM(revenue) OVER (), 1) AS cumulative_pct
FROM genre_revenue
ORDER BY revenue DESC, genre;
