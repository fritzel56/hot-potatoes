# Hot Potatoes
This work was inspired by [this article](https://www.theglobeandmail.com/investing/markets/etfs/article-hot-vs-passive-potato-portfolios-which-delivers-the-best-return/) which described a hot potato portfolio.

### Table of Contents
**[Potato Portfolios](#potato-portfolios)**<br>
**[File Overview](#file-overview)**<br>
**[Problem Statement](#problem-statement)**<br>
**[Implementation Summary](#implementation-summary)**<br>
**[Visual How To](#visual-how-to)**<br>

## Potato Portfolios
The name is inspired by the idea of the couch potato portfolio. This is an investing approach widely discussed online which encourages in investing in index tracking ETFs and holding for the long term. By contrast, the hot potato approach suggested that we should take the same ETF basket (in this case suggested as Canadian stocks, Canadian bonds, US stocks, and internation stocks) and, each month, invest all money in the ETF which had the highest total return over the last 12 months.
## File Overview
| File | Description |
|------|-------------|
| images | Folder containing images for this document |
| return_investigation | Folder containing resources used to confirm that I understood what 1-year Monthly total return was |
| hot_potato.py | Main code used to collect data and send email |
| requirements.txt | Packages needed to run the code |

## Problem Statement
The idea of the hot potato portfolio seemed interesting but I thought there was a decent chance that I might forget to collect the needed info at the end of every month. The purpose of this code is to collect 1-year total returns from Yahoo Finance using python.
## Implementation Summary
The project was in part an excuse to play with cloud infrastructure. Google Cloud was largely used to implement the project. Google Cloud is nice because they have an always free tier. I originally wanted to pull the data from Vanguard directly but the way they structured their website makes it quite hard to scrape. I chose to go with Yahoo Finance as it also has 1-year Monthly Total Return and is much easier to scrape. See the visual how to for full details on setup.
### Compute
Cloud Functions was used to run the code. The serverless model makes here as the job requires so little time/resources to run and runs so infrequently. It's kicked off using an HTTP trigger which is hit from Google Scheduler.
### Scheduling
Cloud Scheduler is used to kick off the job. It hits the HTTP target associated with the Google Cloud Function Job.
### Emailing
In this example, I chose to use Mailjet. Mostly I was interested in seeing how working with a third party mail service would work. No specific reason for choosing Mailjet other than that they have an always free tier.

## Visual How To
This section aims to walk someone with minimal expertize through getting this project up and running.

### Mailjet Setup
To use Mailjet, set up a new account and choose the Developer option on their first landing page.

![Developer option](https://raw.githubusercontent.com/fritzel56/hot-potatoes/master/images/mailjet-developer-option.png)

On the next page, keep the default for API and click continue.

![Select API](https://raw.githubusercontent.com/fritzel56/hot-potatoes/master/images/mailjet-select-api.png)

Choose python for your programming language and feel free to read the code. Most importantly though, you'll need to copy and paste the api_key/api_secret info to get the emails working in the Cloud Function section below.

![API Secrent and Key](https://raw.githubusercontent.com/fritzel56/hot-potatoes/master/images/api-secret-and-key.png)

Having done this, you're ready to move on to getting the code onto Google Functions.

### Cloud Functions

Start by creating a Google Cloud Function. From the console home page, search for function and click on *Cloud Functions*

![Finding Functions](https://raw.githubusercontent.com/fritzel56/hot-potatoes/master/images/go-to-cloud-functions.png)

Next, click *Create Function*.

![Create Function](https://raw.githubusercontent.com/fritzel56/hot-potatoes/master/images/click-create-function.png)

This will bring up the main page to create a cloud function. (1) choose a name. (2) choose python 3.7 under runtime. (3) copy the code from hot_potato.py into the main.py text box. (4) copy the text from requirement.py in this repo into the requirement.py text box (image below). (5) put kickoff into the *Function to execute* box. (6) click *Environment variables, networking, timeouts, and more* to bring up more options.

![Create Function v1](https://raw.githubusercontent.com/fritzel56/hot-potatoes/master/images/create-function.png)

And here is a view of the requirements.txt set up.

![Create Function v1](https://raw.githubusercontent.com/fritzel56/hot-potatoes/master/images/requirements.png)

Scroll down until you see the *Environment* section and then click *Add Variable*.

![Add Variables](https://raw.githubusercontent.com/fritzel56/hot-potatoes/master/images/add-variable.png)

Create four new variables:
* contact_email: the email to send updates from and to
* contact_name: the name the emails should be addressed to
* api_key: your API key for Mailjet (see Emailing section above)
* api_secret: your API secret for Mailjet (see Emailing section above)

and finally, click *Create*.

![Create](https://raw.githubusercontent.com/fritzel56/hot-potatoes/master/images/fill-variables-and-create.png)

At this point, we have a working function that will be triggered whenever the URL specified is visited. Next we add to add a scheduling function which will hit that URL end point at a regular frequency. You should be able to trigger your function manually as follows: from the functions home page, click on your function.

![Click to Function](https://raw.githubusercontent.com/fritzel56/hot-potatoes/master/images/click-to-function.png)

Select the *Trigger* tab and then click on the URL.

![Trigger Function](https://raw.githubusercontent.com/fritzel56/hot-potatoes/master/images/manual-trigger.png)

This will open a new page which should eventually load a simple *OK* message and you should receive your email shortly.

![OK Result](https://raw.githubusercontent.com/fritzel56/hot-potatoes/master/images/ok-result.png)

### Scheduler

In order to get the job to run automatically, we need a scheduler. To do this, we're going to use Cloud Scheduler. Head on over there:

![Go to Scheduler](https://raw.githubusercontent.com/fritzel56/hot-potatoes/master/images/go-to-scheduler.png)

Click *Create Job* to get a new job set up.

![Create Scheduler Job](https://raw.githubusercontent.com/fritzel56/hot-potatoes/master/images/create-scheduler-job.png)

And set up the job as follows. The configuration below will kick off the job daily at 5 PM Eastern. Paste the URL tied to your function into the URL box (see the information on triggering your job manually above if you need to find your URL).

![Set up Scheduler](https://raw.githubusercontent.com/fritzel56/hot-potatoes/master/images/scheduler-set-up.png)

Note the results will only update once a month. I still have the job running daily as I don't fully understand Yahoo Finance's update frequency yet. Once I do, I'll update it to only send the email once a  month.
