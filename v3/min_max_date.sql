SELECT MIN(max_dt) AS min_max_dt
FROM(
  SELECT ticker, max(snap_date) AS max_dt
  FROM {}
  GROUP BY 1
) as maxes;
