## Building Teams Adaptive Cards using Webhooks

### Getting Started:

- Example Usage

- **Note** - If the variable is not expected to be by itself, use `${{variable_name}}` (two braces). Example is `"Thanks for ordering ${{first_name}}"`

- **Note** - If the variable is by itself, use `${variable_name}`. Example is `"${item_price}"`

```python

import requests
from utilita.net.microsofthelper import teams

in_webhook_url = "https://prod-136.westeurope.logic.azure.com:443/workflows/[...]"

in_json = {
    "type": "AdaptiveCard",
    "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
    "version": "1.5",
    "body": [
        {
            "type": "TextBlock",
            "text": "Thanks for ordering ${{customer.firstname}} ${{customer.lastname}}!",
            "wrap": True,
            "style": "heading"
        },
        {
            "type": "TextBlock",
            "text": "**Your Order:**",
            "wrap": True
        },
        {
            "type": "FactSet",
            "facts": "${listItems2}"
        }
    ]
}

in_params = {
    "customer": {
        "firstname": "John",
        "lastname": "Smith"
    },
    "listItems2": [
        {"title": "Big Mac", "value": "$5.00"},
        {"title": "Fries", "value": "$2.00"},
        {"title": "Large Coke", "value": "$1.00"}
    ]
}

ac = teams.AdaptiveCardBuilder(template_dict=in_json)

webhook_request = ac.render_card(in_params)

r = requests.post(in_webhook_url, json=webhook_request)

print(r) # expect <Response [202]>

```