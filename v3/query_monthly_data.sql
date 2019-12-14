SELECT ranked.ticker, ranked.snap_date
FROM(
  SELECT data.*, row_number() over(partition by data.ticker order by data.snap_date desc) as recent
  FROM {} as data
) as ranked
WHERE recent = 1;
