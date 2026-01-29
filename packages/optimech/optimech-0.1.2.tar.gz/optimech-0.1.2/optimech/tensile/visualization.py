import matplotlib.pyplot as plt
import plotly.graph_objects as go
import os


def plot_results(time_s, elongation_mm, strain, workdir):
    """
    Plot elongation and strain versus time, and save it to the folder workdir.
    """
    filename = "Displacement_and_Strain_vs_Time"

    os.makedirs(workdir, exist_ok=True)
    filepath = os.path.join(workdir, filename)

    plt.figure(figsize=(7, 5))
    plt.plot(time_s, elongation_mm, label="Elongation [mm]")
    plt.plot(time_s, strain, label="Strain [-]")
    plt.xlabel("Time [s]")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(filepath)
    plt.show()

    print("Tensile test plots saved in tensile_plots")


def animate_gauge(images_rgb, top_lines, bottom_lines):
    """
    Animate extensometer line tracking over time with a time slider.
    
    Parameters
    ----------
    images_rgb : list of np.ndarray
        RGB images of the tensile test frames.
    top_lines : list or np.ndarray
        Vertical pixel positions of top extensometer line.
    bottom_lines : list or np.ndarray
        Vertical pixel positions of bottom extensometer line.
    """

    h, w, _ = images_rgb[0].shape

    # Initial frame
    fig = go.Figure(
        data=[
            go.Image(z=images_rgb[0]),
            go.Scatter(x=[0, w], y=[top_lines[0]] * 2, mode="lines", line=dict(color="red", width=2)),
            go.Scatter(x=[0, w], y=[bottom_lines[0]] * 2, mode="lines", line=dict(color="blue", width=2)),
        ]
    )

    # Create frames for animation
    fig.frames = [
        go.Frame(
            data=[
                go.Image(z=images_rgb[i]),
                go.Scatter(x=[0, w], y=[top_lines[i]] * 2, mode="lines", line=dict(color="red", width=2)),
                go.Scatter(x=[0, w], y=[bottom_lines[i]] * 2, mode="lines", line=dict(color="blue", width=2)),
            ],
            name=str(i)
        )
        for i in range(len(images_rgb))
    ]

    # Layout with play/pause buttons and slider
    fig.update_layout(
        updatemenus=[dict(
            type="buttons",
            showactive=False,
            y=1,
            x=1.05,
            xanchor="right",
            yanchor="top",
            buttons=[
                dict(label="Play",
                     method="animate",
                     args=[None, {"frame": {"duration": 100, "redraw": True},
                                  "fromcurrent": True, "transition": {"duration": 0}}]),
                dict(label="Pause",
                     method="animate",
                     args=[[None], {"frame": {"duration": 0, "redraw": False},
                                    "mode": "immediate",
                                    "transition": {"duration": 0}}]),
            ]
        )],
        sliders=[dict(
            steps=[dict(method="animate",
                        args=[[str(i)],
                              {"frame": {"duration": 0, "redraw": True},
                               "mode": "immediate",
                               "transition": {"duration": 0}}],
                        label=str(i)) for i in range(len(images_rgb))],
            currentvalue={"prefix": "Frame: "},
            pad={"t": 50}
        )]
    )

    fig.show()

