merge {} as base
using {} as load
ON load.ticker = base.ticker
  and load.snap_date = base.snap_date
WHEN NOT MATCHED THEN
  INSERT(ticker, snap_date, amount)
  VALUES(ticker, snap_date, amount);
