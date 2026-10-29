-- question: How big is each playlist, and how long does it play?
-- notes: Playlist -> PlaylistTrack -> Track. Milliseconds are converted to hours at the end. The LEFT JOIN keeps empty playlists (0 tracks) visible.
SELECT p.PlaylistId,
       p.Name                                       AS playlist,
       COUNT(t.TrackId)                             AS tracks,
       ROUND(COALESCE(SUM(t.Milliseconds), 0) / 3600000.0, 1) AS hours
FROM Playlist AS p
LEFT JOIN PlaylistTrack AS pt ON pt.PlaylistId = p.PlaylistId
LEFT JOIN Track         AS t  ON t.TrackId     = pt.TrackId
GROUP BY p.PlaylistId, p.Name
ORDER BY tracks DESC, p.PlaylistId;
