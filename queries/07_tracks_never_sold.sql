-- question: How many tracks have never been bought, by genre?
-- notes: An anti-join: LEFT JOIN to InvoiceLine and keep rows where no match was found (il.InvoiceLineId IS NULL). COUNT(DISTINCT) is not needed because only unmatched tracks survive the filter.
SELECT COALESCE(g.Name, 'Unknown')  AS genre,
       COUNT(*)                     AS unsold_tracks
FROM Track AS t
LEFT JOIN InvoiceLine AS il ON il.TrackId = t.TrackId
LEFT JOIN Genre       AS g  ON g.GenreId  = t.GenreId
WHERE il.InvoiceLineId IS NULL
GROUP BY genre
ORDER BY unsold_tracks DESC, genre
LIMIT 10;
