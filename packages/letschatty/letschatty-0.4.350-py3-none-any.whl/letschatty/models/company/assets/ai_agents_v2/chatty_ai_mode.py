from enum import StrEnum

class ChattyAIMode(StrEnum):
    """AI mode for the AI agent"""
    AUTONOMOUS = "autonomous"
    SUGGESTIONS = "suggestions"
    COPILOT = "copilot"
    OFF = "off"

    @classmethod
    def is_implemented(cls, mode: 'ChattyAIMode') -> bool:
        return mode in [cls.AUTONOMOUS, cls.SUGGESTIONS, cls.OFF]

    @classmethod
    def get_description(cls, mode: 'ChattyAIMode') -> str:
        return {
            cls.AUTONOMOUS: "El agente de IA tendrá la autonomía de conversar en tiempo real con el usuario, respetando sus instrucciones y las reglas establecidas.",
            cls.SUGGESTIONS: "El agente de IA sugerirá sólo hará sugerencias de respuestas y seguimientos, pero no enviará mensajes ni interactuará de forma directa con el usuario.",
            cls.COPILOT: "El agente de IA responderá automáticamente cuando tenga alta confianza y la consulta esté dentro del alcance; si no, sugerirá o escalará para revisión humana.",
            cls.OFF: "El agente de IA estará inactivo. No responderá al usuario ni hará sugerencias."
        }[mode]

    @classmethod
    def get_context_for_mode(cls, mode: 'ChattyAIMode') -> str:
        intro = "Your mode is set to " + mode.value + ". Here are the rules you need to follow:"
        mode_description = {
            cls.AUTONOMOUS: "Only answer based on the context and rules provided. Do not improvise or make up information. If you can't handle the question, escalate to a human.",
            cls.SUGGESTIONS: "You're only going to be making suggestions, all your messages will be reviewd by a human and you should add the reasoning to your chain of thought. If the user message is not worth answering, you can use the 'skip' action in your output. If the user message is worth answering, you NEED to use the 'suggest' action in your output. ",
            cls.COPILOT: "You're in COPILOT mode. Use your confidence to decide the action: send when the request is within scope and you are confident, suggest when you're unsure or a human touch is needed (complex negotiation, frustration, high-value, or missing info), and escalate if it's required by control triggers. Always include a confidence score (0-100).",
            cls.OFF: ""
        }[mode]
        return intro + "\n\n" + mode_description
