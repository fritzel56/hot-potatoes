# V2
I decided I was interested in splitting out the stock information from the main python file. It wasn't part of the core logic and it didn't make sense to have someone edit the core file just to change which stocks to check.

I also took the opportunity to break out the email compose and email send functionality thinking that I might want to reuse the email send function for error reporting. Error reporting has now been added.

I also added memory by writing results to Google BigQuery (see `bigquery_setup` for an overview of how to set up the table). This means that emails no longer send daily but only when the total 1 year return values update. Note, in order for this to work, you need to add new environment variables: PROJECT_ID, DATASET, and TABLENAME.

## File Overview
| File | Description |
|------|-------------|
| bigquery_setup | Code used to do one time BigQuery setup (creating new dataset and table). |
| main.py | Main code used to collect data and send email. |
| query_monthly_data.sql | Query to pull latest returns by ETF from BiqQuery table. |
| requirements.txt | Packages needed to run the code. |
| stocks.yaml | YAML file containing info on stocks to be checked. Edit this file to track your stocks of interest. |

## Setup
Google Cloud Function's Inline Editor option only allows for a `main.py` file and `requirements.txt` file. Google Cloud Functions also doesn't pull from GitHub so instead I cloned the repo to Cloud Source repository. When creating a new Function, follow the steps in the main README but instead of selecting `Inline Code`, go with `Cloud Source repository`. Under repository, list the repository name (ex: `hot-potatoes`) for the repo. Under branch name leave `master`. Under `Directory with source code` put the directory which contains the `main.py` file you want kicked off (in this case put `/v2/` in that field). Note, it seems Google Cloud Functions will only kick off a file named main.py. Function to execute will again be `kickoff`.

Of note, I was hoping this would also mean that code would be pulled at each run meaning that it would pick up any new changes committed to master since it was first deployed. This appears not to be the case. Once deployed, the code version associated with it is locked. This means that if you update your code and want it reflected at run time, you need to redeploy your Google Cloud Function. This is as simple as clicking `Edit` and then `Deploy` without actually changing any of the settings.

To customize to track your stocks of interest, you should only have to edit the `stocks.yaml` file.
