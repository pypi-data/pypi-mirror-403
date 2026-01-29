
from typing import List, Any, Optional
from centra_sdk.models.connector.v1.operations.config import ConfigOpts
from centra_sdk.models.connector.v1.operations.config import DynamicConfigOptionValuesRequest, DynamicConfigOptionValuesResponse


class OptionValuesHandler:
    def __init__(self):
        self.providers = {}

    def register_handler(self, handler: 'OptionValuesHandler'):
        self.providers[handler.unique_classifier] = handler

    def get_option_values(self, request: DynamicConfigOptionValuesRequest) -> List[Any]:
        raise NotImplementedError("This method should be implemented by subclasses.")

    @property
    def unique_classifier(self) -> str:
        raise NotImplementedError("This property should be implemented by subclasses.")

    def handle(self, request: DynamicConfigOptionValuesRequest) -> DynamicConfigOptionValuesResponse:
        if request.unique_classifier not in self.providers:
            raise ValueError(f"No handler registered for option: {request.unique_classifier}")
        values = self.providers[request.unique_classifier].get_option_values(request)
        filtered_options = self.filter_options(values, request.offset, request.limit, request.search)
        return DynamicConfigOptionValuesResponse(
            total_count=len(values),
            data=filtered_options
        )

    def verify_handlers_registered(self, schema: List[ConfigOpts]):
        for field in schema:
            if field.dynamic_format and field.name not in self.providers:
                raise ValueError(f"No options values handler registered for dynamic option: {field.name}")

    @staticmethod
    def filter_options(options: List[Any], offset: int, limit: int, search: Optional[str] = None) -> List[Any]:
        filtered_options = []
        while len(filtered_options) < limit and offset < len(options):
            option = options[offset]
            if not search or (search.lower() in option.lower()):
                filtered_options.append(option)
            offset += 1
        return filtered_options
