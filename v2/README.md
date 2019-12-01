# V2
I decided I was interested in splitting out the stock information from the main python file. It wasn't part of the core logic and it didn't make sense to have someone edit that file just to change which stocks to check.

I also took the opportunity to break out the email compose and email send functionality thinking that I might eventually want to reuse the email send function for error reporting.

## File Overview
| File | Description |
|------|-------------|
| main.py | Main code used to collect data and send email |
| requirements.txt | Packages needed to run the code |
| stocks.yaml | YAML file containing info on stocks to be checked |

## Setup
Google Cloud Function's Inline Editor option only allows for a `main.py` file and `requirements.txt` file. Google Cloud Functions doesn't pull from GitHub so instead I cloned the repo to Cloud Source repository. When creating a new Function, follow the steps in the main README but instead of selecting `Inline Code`, go with `Cloud Source repository`. Under repository, list the repository name (ex: `hot-potatoes` for the repo). Under branch name leave `master`. Under `Directory with source code` put the directory which contains the `main.py` file you want kicked off (in this case put `/v2/` in that field). Note, it seems Google Cloud Functions will only kick off a file named main.py. Function to execute will again by `kickoff`.

Of note, I was hoping this would also mean that code would be pulled at each run meaning that it would pick up any new changes commited to master since it was first deployed. This appears not to be the case. Once deployed, the code version associated with it is locked. This means that if you update your code and want it reflected at run time, you need to redeploy your Google Cloud Function. This is as simple as clicking `Edit` and then `Deploy` without actually changing anything.
