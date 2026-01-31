import json
import re
from typing import Union
from collections.abc import Iterable

class AdaptiveCardBuilder:
    """ Microsoft Adaptive Card Builder
        
        Parms:
        template_dict (dict): The actual template that you build in the adaptive card builder

        NOTICE - This class does not support iterables. Sorry.
        """
    def __init__(self, template_dict: dict):
        self.template_dict = template_dict
        self.params_mapper = {}
        self.non_exclusive_params_mapper = {}
        self._identify_params() # Get the parameters from the template
        self._identify_non_exclusive_params()

    def _identify_params(self) -> list:
        """ Identify the parameters in the template object """
        tj_str = json.dumps(self.template_dict)

        # find all instances of "${param_to_use}"
        raw_pattern = re.compile(r'(\"\$\{[a-zA-Z0-9_.]+\}\")')

        # strip the dollar sign and braces
        inner_value_pattern = re.compile(r'((?<=\{)[a-zA-Z0-9_.]+(?=\}))')

        raw_matches = set(raw_pattern.findall(tj_str))

        for match in raw_matches:
            inner_value = inner_value_pattern.search(match)[0]
            self.params_mapper.update({
                inner_value: match
            })

    def _identify_non_exclusive_params(self) -> list:
        """ Identify the parameters in the template that are not by itself
         
         ie: "Welcome to the team ${{employee.firstName}}"
           """
        tj_str = json.dumps(self.template_dict)

        # find all instances of "${param_to_use}"
        raw_pattern = re.compile(r'\$\{{[a-zA-Z0-9_.]+\}}')

        # strip the dollar sign and braces
        inner_value_pattern = re.compile(r'((?<=\{)[a-zA-Z0-9_.]+(?=\}))')

        raw_matches = set(raw_pattern.findall(tj_str))

        for match in raw_matches:
            inner_value = inner_value_pattern.search(match)[0]
            self.non_exclusive_params_mapper.update({
                inner_value: match
            })

    def _get_nested_params(self, parameters_dict: dict, missing_key_value: str, params: list) -> str:
        """ Iterate through complex objects to get a nested value in a dict
        
        Params:
            parameters_dict (dict): the source parameter data
            msising_key_value (str): the value to return if its missing
            params (list): the ordered list of parameters

        Returns a value (probably string)        
            """
        
        _ = parameters_dict.copy()
        for p in params:
            _ = _.get(p, None)
            if _ is None:
                return missing_key_value
        return _
    
    def get_teams_webhook_header(self, output_cards: Union[dict, iter]) -> dict:
        """ Gets the full header for a teams webhook request.
        
        output_cards (dict or list): Accepts a dict or a list of output_card data. If a list, 
        it will wrap all the cards in one request.
        """

        # The order is actually important here. A dict can be an iterable :/
        if isinstance(output_cards, dict):
            attachments = [self.get_teams_webhook_object(output_cards)]
        
        elif isinstance(output_cards, Iterable):
            attachments = [self.get_teams_webhook_object(at) for at in output_cards]

        else:
            raise ValueError(f"output_cards must be a dict or a list of dicts output cards is {type(output_cards)}")

        return {
            "type": "message",
            "attachments": attachments
            }
    
    def get_teams_webhook_object(self, output_card: dict) -> dict:
        """ This is not the full header. in a teams webhook you can technically send multiple cards in a message.
        This just gives the card object.

        Params:
            output_card (dict): The rendered card thats ready to go

        Returns a ready made card.
        
        """

        return {
                    "contentType": "application/vnd.microsoft.card.adaptive",
                    "contentUrl": None,
                    "content": output_card
                }

    def render_card(self, parameters_dict: dict=None, missing_key_value="N/A", include_header=True) -> dict:
        """ Takes a card template, and a dict of parameters to interpolate, and builds a card that can be published.
            Note: If you need to get just the AdaptiveCard and not the Teams header data (for posting to a webhook, pass include_header=False)
        Params:
            parameters_dict (dict): The output parameters to use
            missing_key_value (str): The value to pass if a key is missing
            include_header (bool): include the header data (For microsoft teams webhooks)
        """
        card_str = json.dumps(self.template_dict)

        if parameters_dict is None:
            parameters_dict = {}

        for parameter_value, template_key in self.params_mapper.items():
            parameter_levels = parameter_value.split('.')
            
            if len(parameter_levels) > 1:
                safe_result = json.dumps(self._get_nested_params(parameters_dict, missing_key_value, parameter_levels))
            else:
                safe_result = json.dumps(parameters_dict.get(parameter_value, missing_key_value))

            card_str = card_str.replace(template_key, safe_result)

        for parameter_value, template_key in self.non_exclusive_params_mapper.items():
            parameter_levels = parameter_value.split('.')
            
            if len(parameter_levels) > 1:
                safe_result = json.dumps(self._get_nested_params(parameters_dict, missing_key_value, parameter_levels))[1:-1]
            else:
                safe_result = json.dumps(parameters_dict.get(parameter_value, missing_key_value))[1:-1]

            card_str = card_str.replace(template_key, safe_result)

        card_dict = json.loads(card_str)

        if include_header:
            return self.get_teams_webhook_header(card_dict)

        return card_dict
