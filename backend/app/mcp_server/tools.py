MCP_TOOLS = [
    {
        "name": "get_company_financials",
        "description": "Read company financial history from the PostgreSQL warehouse.",
        "required_role": "Viewer",
    },
    {
        "name": "run_forecast",
        "description": "Run revenue or expense forecasting for a company.",
        "required_role": "Finance Analyst",
    },
    {
        "name": "generate_board_pack",
        "description": "Generate CFO board-pack report artifacts.",
        "required_role": "CFO",
    },
    {
        "name": "run_scenario",
        "description": "Run base, upside, and downside FP&A scenario simulations.",
        "required_role": "Finance Analyst",
    },
    {
        "name": "get_kpi_risks",
        "description": "Fetch red/yellow KPI risk signals for a company.",
        "required_role": "Viewer",
    },
    {
        "name": "create_budget_recommendation",
        "description": "Create a budget action recommendation with audit logging.",
        "required_role": "CFO",
    },
]
