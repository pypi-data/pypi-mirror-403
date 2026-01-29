import plotly.express as px
from dash import Dash, html
from dash_ag_grid import AgGrid

import dash_aggrid_scales as das

medals = px.data.medals_long().assign(negative=list(range(-5, 4)))

app = Dash()

app.layout = html.Div(
    [
        AgGrid(
            rowData=medals.to_dict("records"),
            columnSize="sizeToFit",
            style={"height": 500},
            columnDefs=[
                {
                    "field": "nation",
                    "headerName": "nation (qualitative)",
                    "cellStyle": {"styleConditions": das.qualitative(medals["nation"])},
                },
                {
                    "field": "medal",
                    "headerName": "medal (qualitative with dict)",
                    "cellStyle": {
                        "styleConditions": das.qualitative(
                            medals["medal"],
                            {"gold": "gold", "silver": "silver", "bronze": "#cd7f32"},
                        )
                    },
                },
                {
                    "field": "count",
                    "headerName": "count (sequential)",
                    "cellStyle": {"styleConditions": das.sequential(medals["count"])},
                },
                {
                    "field": "count",
                    "headerName": "count (bar)",
                    "cellStyle": {"styleConditions": das.bar(medals["count"])},
                },
                {
                    "field": "negative",
                    "headerName": "random +ve & -ve values (bar)",
                    "cellStyle": {
                        "styleConditions": das.bar(medals["negative"], "teal")
                    },
                },
            ],
        )
    ]
)

if __name__ == "__main__":
    app.run(debug=True)
