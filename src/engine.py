from .inspector import KamarInspector


class KamarEngine:
    def __init__(self, inspector=None):
        self.inspector = inspector or KamarInspector()

    def process(self, payload):
        result = self.inspector.inspect(payload)
        return {
            "agent": "KAMAR-META-AGENT",
            "version": "2.3-RC",
            **result
        }
