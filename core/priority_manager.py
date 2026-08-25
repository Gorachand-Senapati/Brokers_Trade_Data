class PriorityManager:

    def __init__(self, priority):
        self.priority = [
            provider.lower()
            for provider in priority
        ]

    def get_priority(self, provider):
        provider = provider.lower()

        if provider not in self.priority:
            return float("inf")

        return self.priority.index(provider)

    def should_accept(self, tick, active_providers):
        provider = tick.provider.lower()

        if provider not in active_providers:
            return False

        # Find the highest-priority active provider
        for priority_provider in self.priority:
            if priority_provider in active_providers:
                return provider == priority_provider

        return False