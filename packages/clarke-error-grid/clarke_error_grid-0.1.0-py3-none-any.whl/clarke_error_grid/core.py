import plotly.graph_objects as go

def plot(ref_values, pred_values, title_string="Clarke Error Grid"):
    """
    Plot Clarke Error Grid using Plotly.

    Parameters
    ----------
    ref_values : array-like
        Reference glucose values (mg/dl).
    pred_values : array-like
        Predicted glucose values (mg/dl).
    title_string : str, optional
        Title of the plot (default is "Clarke Error Grid").

    Returns
    -------
    fig : plotly.graph_objects.Figure
        Interactive Plotly figure displaying the Clarke Error Grid.
    """

    # Checking lengths
    assert len(ref_values) == len(pred_values), (
        f"Unequal number of values (reference : {len(ref_values)}) "
        f"(prediction : {len(pred_values)})."
    )

    # Physiological range warnings
    if max(ref_values) > 400 or max(pred_values) > 400:
        print(
            f"Input Warning: the maximum reference value {max(ref_values)} "
            f"or the maximum prediction value {max(pred_values)} exceeds "
            f"the normal physiological range of glucose (<400 mg/dl)."
        )

    if min(ref_values) < 0 or min(pred_values) < 0:
        print(
            f"Input Warning: the minimum reference value {min(ref_values)} "
            f"or the minimum prediction value {min(pred_values)} is less than 0 mg/dl."
        )

    fig = go.Figure()

    # Scatter points
    fig.add_trace(
        go.Scatter(
            x=ref_values,
            y=pred_values,
            mode="markers",
            marker=dict(color="black", size=6),
            showlegend=False
        )
    )

    # Helper function to add lines
    def add_line(x, y, dash="solid"):
        fig.add_trace(
            go.Scatter(
                x=x,
                y=y,
                mode="lines",
                line=dict(color="black", dash=dash),
                showlegend=False
            )
        )

    # Theoretical 45° line
    add_line([0, 400], [0, 400], dash="dot")

    # Zone lines (exact translations)
    add_line([0, 175/3], [70, 70])
    add_line([175/3, 400/1.2], [70, 400])
    add_line([70, 70], [84, 400])
    add_line([0, 70], [180, 180])
    add_line([70, 290], [180, 400])
    add_line([70, 70], [0, 56])
    add_line([70, 400], [56, 320])
    add_line([180, 180], [0, 70])
    add_line([180, 400], [70, 70])
    add_line([240, 240], [70, 180])
    add_line([240, 400], [180, 180])
    add_line([130, 180], [0, 70])

    # Zone labels
    annotations = [
        (30, 15, "A"),
        (370, 260, "B"),
        (280, 370, "B"),
        (160, 370, "C"),
        (160, 15, "C"),
        (30, 140, "D"),
        (370, 120, "D"),
        (30, 370, "E"),
        (370, 15, "E"),
    ]

    for x, y, label in annotations:
        fig.add_annotation(
            x=x,
            y=y,
            text=label,
            showarrow=False,
            font=dict(size=15, color="black")
        )

    # Layout
    fig.update_layout(
        title=title_string,
        xaxis=dict(
            title="Reference Concentration (mg/dl)",
            range=[0, 400],
            tickvals=[0, 50, 100, 150, 200, 250, 300, 350, 400],
            showgrid=False,
            zeroline=False
        ),
        yaxis=dict(
            title="Prediction Concentration (mg/dl)",
            range=[0, 400],
            tickvals=[0, 50, 100, 150, 200, 250, 300, 350, 400],
            showgrid=False,
            zeroline=False,
            scaleanchor="x",
            scaleratio=1
        ),
        plot_bgcolor="white",
        paper_bgcolor="white",
        width=700,
        height=700
    )

    return fig


def zone(ref_values, pred_values):
    """
    Classify points into Clarke Error Grid zones.

    Returns
    -------
    list
        Counts for zones [A, B, C, D, E]
    """
    
    zone = [0] * 5
    for i in range(len(ref_values)):
        if (ref_values[i] <= 70 and pred_values[i] <= 70) or (pred_values[i] <= 1.2*ref_values[i] and pred_values[i] >= 0.8*ref_values[i]):
            zone[0] += 1    #Zone A

        elif (ref_values[i] >= 180 and pred_values[i] <= 70) or (ref_values[i] <= 70 and pred_values[i] >= 180):
            zone[4] += 1    #Zone E

        elif ((ref_values[i] >= 70 and ref_values[i] <= 290) and pred_values[i] >= ref_values[i] + 110) or ((ref_values[i] >= 130 and ref_values[i] <= 180) and (pred_values[i] <= (7/5)*ref_values[i] - 182)):
            zone[2] += 1    #Zone C
        elif (ref_values[i] >= 240 and (pred_values[i] >= 70 and pred_values[i] <= 180)) or (ref_values[i] <= 175/3 and pred_values[i] <= 180 and pred_values[i] >= 70) or ((ref_values[i] >= 175/3 and ref_values[i] <= 70) and pred_values[i] >= (6/5)*ref_values[i]):
            zone[3] += 1    #Zone D
        else:
            zone[1] += 1    #Zone B
    
    return zone