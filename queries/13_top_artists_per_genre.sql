-- question: Who are the top 2 artists in each of the five biggest genres?
-- notes: Top-N per group: ROW_NUMBER() restarts for every genre (PARTITION BY) and the outer query keeps rows 1 and 2. Ties are broken by artist name so the result is stable. Artists rather than tracks are ranked on purpose: no track in this database sold more than twice, so a per-track ranking would be a wall of ties. The five genres come from a second CTE.
WITH artist_genre_revenue AS (
    SELECT g.GenreId, g.Name AS genre, ar.ArtistId, ar.Name AS artist,
           SUM(il.UnitPrice * il.Quantity) AS revenue
    FROM InvoiceLine AS il
    JOIN Track  AS t  ON t.TrackId  = il.TrackId
    JOIN Genre  AS g  ON g.GenreId  = t.GenreId
    JOIN Album  AS al ON al.AlbumId = t.AlbumId
    JOIN Artist AS ar ON ar.ArtistId = al.ArtistId
    GROUP BY g.GenreId, g.Name, ar.ArtistId, ar.Name
),
top_genres AS (
    SELECT GenreId
    FROM artist_genre_revenue
    GROUP BY GenreId
    ORDER BY SUM(revenue) DESC, GenreId
    LIMIT 5
),
numbered AS (
    SELECT genre, artist, revenue,
           ROW_NUMBER() OVER (PARTITION BY GenreId ORDER BY revenue DESC, artist) AS rn
    FROM artist_genre_revenue
    WHERE GenreId IN (SELECT GenreId FROM top_genres)
)
SELECT genre, rn AS rank_in_genre, artist, ROUND(revenue, 2) AS revenue
FROM numbered
WHERE rn <= 2
ORDER BY genre, rn;
