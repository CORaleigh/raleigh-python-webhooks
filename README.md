# Python Webhook for Api.ai
This is a webhook created for use with Api.ai for building the City of Raleigh's Actions on Google.  This project is building a Google Assistant service for use on Google Home and supported Android Phones.

More info about Api.ai webhooks could be found here:
[Api.ai Webhook](https://docs.api.ai/docs/webhook)

# Deploy to:
[![Deploy to Heroku](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy)

# What does the service do?
This service can report what district you are in (CAC, City Council, Police), when your trash/recycling/yard waste day is, if you need to take your recycling out this week, and about upcoming events in the next week.

The service packs the result in the Api.ai webhook-compatible response JSON and returns it to Api.ai.

# Recent Updates
* when you specify you address for one question, you do not need to repeat it for the next
  * this was done by creating a context called address, then setting the default value for the street-address parameter to #address.street-address
  
# Future Ideas
* for CAC, return when and where the CAC meetings are
* return bio information for City Council person


