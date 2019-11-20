# BigQuery Setup

I originally thought it would be easy to determine which day Yahoo Finance would update (ex: first business day of the month) but it didn't seem so straightforward. Instead, I decided I could add memory to the system using Google BigQuery. This way I could check if today's price was different from yesterday's price. If it was, I would send the email. This would also allow me to see historical data if I wanted to look at it later.

I chose BigQuery because it's included in the always free tier.

I started initial set up using my local command line. This proved a bit trickier than expected so here are my notes:

1) set up authentication so you can access your project from your local following these instructions: https://cloud.google.com/docs/authentication/getting-started

2) pip install google-cloud-bigquery
