-- question: Which 10 artists bring in the most revenue?
-- notes: Four-table join chain InvoiceLine -> Track -> Album -> Artist. Album.ArtistId is NOT NULL, but Track.AlbumId is nullable; tracks without an album would be excluded by the inner join. (In this database none are, which a test confirms by reconciling to total revenue.)
SELECT ar.Name                                AS artist,
       COUNT(DISTINCT t.TrackId)              AS tracks_sold,
       ROUND(SUM(il.UnitPrice * il.Quantity), 2) AS revenue
FROM InvoiceLine AS il
JOIN Track  AS t  ON t.TrackId  = il.TrackId
JOIN Album  AS al ON al.AlbumId = t.AlbumId
JOIN Artist AS ar ON ar.ArtistId = al.ArtistId
GROUP BY ar.ArtistId, ar.Name
ORDER BY revenue DESC, artist
LIMIT 10;
