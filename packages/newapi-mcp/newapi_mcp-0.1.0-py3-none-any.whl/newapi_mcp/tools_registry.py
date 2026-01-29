"""Tools registry for New API MCP."""

from .channels import ChannelTools
from .client import NewAPIClient
from .logs import LogTools
from .model_search import ModelSearchTools
from .models_mgmt import ModelTools
from .pricing import PricingTools
from .token_management import TokenManagementTools
from .tokens import TokenTools
from .users import UserTools


class ToolsRegistry:
    """Central registry for all API tools."""

    def __init__(self, client: NewAPIClient):
        """Initialize all tools with the provided client."""
        self.pricing = PricingTools(client)
        self.users = UserTools(client)
        self.tokens = TokenTools(client)
        self.channels = ChannelTools(client)
        self.models = ModelTools(client)
        self.logs = LogTools(client)
        self.model_search = ModelSearchTools(client)
        self.token_management = TokenManagementTools(client)
