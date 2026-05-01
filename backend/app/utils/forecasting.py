from prophet import Prophet
import pandas as pd


def rolling_forecast(df: pd.DataFrame, months: int = 12):

    df = df.sort_values("ds")

    model = Prophet(
        yearly_seasonality=True,
        weekly_seasonality=False,
        daily_seasonality=False
    )

    model.fit(df)

    future = model.make_future_dataframe(
        periods=months,
        freq="MS"
    )

    forecast = model.predict(future)

    return forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]]


def forecast_expense(df: pd.DataFrame, months: int = 12):

    return rolling_forecast(df, months)


def forecast_revenue(df: pd.DataFrame, months: int = 12):

    return rolling_forecast(df, months)


def incorporate_actuals(df: pd.DataFrame, new_actuals: pd.DataFrame):

    df = pd.concat([df, new_actuals])
    df = df.drop_duplicates(subset=["ds"])
    df = df.sort_values("ds")

    return rolling_forecast(df)