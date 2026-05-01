from agno.agent import Agent
from groq import Groq
from app.config import settings
from app.logger import logger
from app.websocket.manager import broadcast


class VarianceExplanationAgent(Agent):
    def __init__(self):
        super().__init__()
        self.name = "Variance Explanation Agent"

    async def run(self, actual: float, forecast: float, company_id: int = None):
        try:
            variance = actual - forecast
            pct = variance / forecast if forecast else 0

            prompt = f"""
Explain this financial variance.

Actual: {actual}
Forecast: {forecast}
Variance: {variance}
Percent: {pct}

Categorize the variance into:
- Price
- Volume
- Mix
- Timing

Provide a short board-ready explanation.
"""

            if not settings.GROQ_API_KEY:
                if forecast:
                    pct_abs = abs(pct)
                    if pct_abs >= 0.15:
                        category = "volume"
                    elif pct_abs >= 0.07:
                        category = "price"
                    else:
                        category = "timing"
                else:
                    category = "timing"
                direction = "favorable" if variance >= 0 else "unfavorable"
                explanation = f"{direction.capitalize()} variance driven primarily by {category} effects based on actuals vs forecast."
            else:
                client = Groq(api_key=settings.GROQ_API_KEY)
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": prompt}]
                )
                explanation = response.choices[0].message.content

            result = {
                "agent": self.name,
                "variance": variance,
                "percentage": pct,
                "explanation": explanation
            }

            try:
                await broadcast(result)
            except Exception as e:
                logger.warning(f"Variance WebSocket failed: {e}")

            return result

        except Exception as e:
            logger.exception(f"VarianceExplanationAgent failed: {e}")
            return {"agent": self.name, "error": str(e)}
