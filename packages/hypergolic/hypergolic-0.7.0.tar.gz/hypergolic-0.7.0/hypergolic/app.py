from anthropic import AsyncAnthropic

from hypergolic.agent_runner import AgentRunner
from hypergolic.config import HypergolicConfig
from hypergolic.conversation_manager import ConversationManager
from hypergolic.pricing import get_pricing
from hypergolic.prompts.resolvers import build_operator_system_prompt
from hypergolic.providers import build_provider_client
from hypergolic.session_context import SessionContext
from hypergolic.session_stats import SessionStats
from hypergolic.tui import TUI


class App:
    def __init__(self, session_context: SessionContext):
        self.session_context = session_context
        self.config = HypergolicConfig()
        self.client: AsyncAnthropic = build_provider_client(self.config)
        self.system_prompt = build_operator_system_prompt(session_context)
        self.stats = SessionStats()
        self.stats.pricing = get_pricing(self.config.provider.model)
        self.conversation = ConversationManager(self.stats)

        # Runner is created by TUI.__init__ and stored here for external access
        self.runner: AgentRunner | None = None

        self.tui = TUI(
            app=self,
            session_context=self.session_context,
            config=self.config,
            client=self.client,
            system_prompt=self.system_prompt,
            stats=self.stats,
            conversation=self.conversation,
        )

    def run(self) -> None:
        self.tui.run()
