-- question: Who reports to whom, and how many direct reports does each manager have?
-- notes: A self-join: Employee joined to itself on ReportsTo. The top of the tree has ReportsTo NULL, so the manager side must be a LEFT JOIN or that person disappears.
SELECT e.EmployeeId,
       e.FirstName || ' ' || e.LastName                AS employee,
       COALESCE(m.FirstName || ' ' || m.LastName, '(none: top of the tree)') AS manager,
       (SELECT COUNT(*) FROM Employee AS r WHERE r.ReportsTo = e.EmployeeId) AS direct_reports
FROM Employee AS e
LEFT JOIN Employee AS m ON m.EmployeeId = e.ReportsTo
ORDER BY e.EmployeeId;
