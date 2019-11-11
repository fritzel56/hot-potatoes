# Hot Potatoes
This work was inspired by [this article](https://www.theglobeandmail.com/investing/markets/etfs/article-hot-vs-passive-potato-portfolios-which-delivers-the-best-return/) which described a hot potato portfolio.
## Potato Portfolios
The name is inspired by the idea of the couch potato portfolio. This is an investing approach widely discussed online which encourages in investing in index tracking ETFs and holding for the long term. By contrast, the hot potato approach suggested that we should take the same ETF basket (in this case suggested as Canadian stocks, Canadian bonds, US stocks, and internation stocks) and, each month, invest all money in the ETF which had the highest total return over the last 12 months.
## Problem Statement
The idea seemed interesting but I thought there was a decent chance that I might forget to collect the needed info at the end of every month. The purpose of this code is to collect 1-year total returns from Yahoo Finance.
## Implementation
The project was in part an excuse to play with cloud infrastructure. Google Cloud was largely used to implement the project. Google Cloud is nice because they have an always free tier.
### Compute
Cloud Functions was used to run the code I used the smallest memory allocation and and HTTP trigger (using Google Scheduler -- see below). At the bottom of the setup page you can select _Environment variables, networking, timeouts and more_. I added environment variables for sensitive variables. Specifically, to run this code, you need to set environment variables for:
* contact_email: the email to send updates from and to
* contact_name: the name the emails should be addressed to
* api_key: your API key for Mailjet (see Emailing below)
* api_secret: your API secret for Mailjet (see Emailing below)
### Scheduling
Cloud Scheduler was used to kick off the job. It uses an HTTP target which is then used as the trigger for the Cloud Function.
### Emailing

## Visual How To With Inline text

This section aims to walk someone who has a google project but is unfamiliar with the google cloud environment through getting this project up and running.

### Cloud Functions

Start by creating a google cloud function. From the console home page, search for function and click on *Cloud Functions*

![Finding Functions](https://github.com/fritzel56/hot-potatoes/blob/implementation/images/go-to-cloud-functions.png)

Next, click *Create Function*.

![Create Function](https://github.com/fritzel56/hot-potatoes/blob/implementation/images/click-create-function.png)

This will bring up the main page to create a cloud function. (1) choose a name. (2) choose python 3.7 under runtime. (3) copy the code from hot_potato.py into the main.py text box. (4) copy the text from requirement.py in this repo into the requirement.py text box (image below). (5) put kickoff into the *Function to execute* box. (6) click Environment variables, networking, timeouts, and more to bring up more options.

![Create Function v1](https://github.com/fritzel56/hot-potatoes/blob/implementation/images/create-function.png)

And here is a view of the requirements.txt set up.

![Create Function v1](https://github.com/fritzel56/hot-potatoes/blob/implementation/images/requirements.png)

Scroll down until you see the *Environment* section and then click *Add Variable*.

![Add Variables](https://github.com/fritzel56/hot-potatoes/blob/implementation/images/add-variable.png)

Create four new variables: 
* contact_email: the email to send updates from and to
* contact_name: the name the emails should be addressed to
* api_key: your API key for Mailjet (see Emailing below)
* api_secret: your API secret for Mailjet (see Emailing below)

and finally, click *Create*.

![Create](https://github.com/fritzel56/hot-potatoes/blob/implementation/images/fill-variables-and-create.png)

At this point, we have a working function that will be triggered whenever the URL specified is visited. Next we add to add a scheduling function which will that URL end point at a regular frequency.
