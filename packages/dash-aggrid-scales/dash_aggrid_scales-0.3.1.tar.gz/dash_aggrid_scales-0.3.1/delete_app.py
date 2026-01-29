import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
from dash import Dash, html
from dash_ag_grid import AgGrid

import dash_aggrid_scales as das

medals = px.data.medals_long().assign(negative=list(range(-5, 4)))

app = Dash(external_stylesheets=[dbc.themes.LITERA])


df = pd.DataFrame({x: list(range(1, 11)) + [20] for x in list("ABCD")})
print(df)
app.layout = dbc.Container(
    [
        html.Br(),
        html.H2(["Set the number of bins with the ", html.Code("nbins"), " parameter"]),
        html.H2(
            [
                "Use a completely custom scale",
                html.Code('["olive", "yellow", "brown"]'),
                " (use more than two colors)",
            ]
        ),
        html.Br(),
        AgGrid(
            rowData=df.to_dict("records"),
            columnSize="sizeToFit",
            dashGridOptions={"domLayout": "autoHeight"},
            columnDefs=[
                {
                    "field": col,
                    "headerName": f"nbins: {i * 2}",
                    "cellStyle": {
                        "styleConditions": das.sequential(
                            df[col],
                            colorscale=["olive", "yellow", "brown"],
                            nbins=i * 2,
                        )
                    },
                }
                for i, col in enumerate(df.columns, 1)
            ],
        ),
    ],
)

if __name__ == "__main__":
    app.run(debug=True)
