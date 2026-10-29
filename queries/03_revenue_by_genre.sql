-- question: Which genres earn the most, and how much revenue has no genre?
-- notes: Genre is a nullable foreign key on Track, so an INNER JOIN to Genre would silently drop untagged tracks. LEFT JOIN plus COALESCE keeps them visible as 'Unknown'. (In this database every track has a genre, so 'Unknown' never appears, but the schema allows it.)
SELECT COALESCE(g.Name, 'Unknown')            AS genre,
       SUM(il.Quantity)                       AS units_sold,
       ROUND(SUM(il.UnitPrice * il.Quantity), 2) AS revenue
FROM InvoiceLine AS il
JOIN Track       AS t ON t.TrackId = il.TrackId
LEFT JOIN Genre  AS g ON g.GenreId = t.GenreId
GROUP BY genre
ORDER BY revenue DESC, genre
LIMIT 10;
