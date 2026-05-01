from sqlalchemy.orm import Session
from app.models.initiative import Initiative


def get_initiatives(db: Session):

    rows = db.query(Initiative).all()

    results = []

    for i in rows:

        roi = 0

        if i.investment > 0:
            roi = i.revenue_impact / i.investment

        results.append({
            "id": i.id,
            "name": i.name,
            "investment": i.investment,
            "revenue_impact": i.revenue_impact,
            "roi": roi
        })

    return results