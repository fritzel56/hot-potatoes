SELECT ranked.etf, ranked.return
FROM(
  SELECT data.*, row_number() over(partition by data.etf order by data.pull_timestamp desc) as recent
  FROM {} as data
) as ranked
WHERE recent = 1;
