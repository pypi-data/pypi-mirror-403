from pandas import DataFrame, Series
from anndata import AnnData
from typing import Optional, Dict, Union, List
from numpy import ndarray
import os

def perform_clustering(correlations: DataFrame) -> ndarray:
    from scipy.cluster.hierarchy import linkage, fcluster
    from scipy.spatial.distance import squareform
    from numpy import argsort
    """
    Perform hierarchical clustering and return column order.

    Args:
        correlations (DataFrame): Correlation matrix.

    Returns:
        ndarray: Ordered column indices.
    """
    dissimilarity = 1 - abs(correlations)
    Z = linkage(squareform(dissimilarity), "complete")
    threshold = 0.8
    labels = fcluster(Z, threshold, criterion="distance")
    return (argsort(labels))

def plot_heatmap(
        ax, correlations: DataFrame, title: str, index: int, first_correlations: Optional[DataFrame] = None
) -> None:
    from scipy.stats import pearsonr

    """
    Plot a heatmap for the given correlation matrix.

    Args:
        ax (plt.Axes): Axes object to draw the heatmap on.
        correlations (DataFrame): Correlation matrix.
        title (str): Title of the heatmap.
        index (int): Index of the dataset being processed.
        first_correlations (Optional[DataFrame]): Correlation matrix of the first dataset.
    """
    from seaborn import heatmap
    heatmap(
        round(correlations, 2),
        cmap="RdBu",
        vmin=-1,
        vmax=1,
        annot=False,
        fmt=".2f",
        xticklabels=False,
        yticklabels=False,
        ax=ax,
    )
    ax.set_title(title)

    if index != 0 and first_correlations is not None:
        # Compute and annotate the Pearson correlation
        r_val, _ = pearsonr(
            first_correlations.values.flatten(), correlations.values.flatten()
        )
        ax.text(
            0.5,
            -0.1,
            f"R = {r_val:.2f}",
            horizontalalignment="center",
            verticalalignment="center",
            transform=ax.transAxes,
        )


def create_spider_chart(data_dict: Dict[str, Dict[str, Union[DataFrame, Series]]], save_path: str,
                        title: Optional[str] = None, color_palette: Optional[List[str]] = None) -> None:
    """
    Create multiple interactive spider charts using Plotly from a dictionary of datasets.

    Args:
        data_dict (Dict[str, Dict]): Dictionary where:
            - Keys are subplot titles (str).
            - Values are dictionaries where keys are simulation technique names,
              and values are DataFrames or Series.
        save_path (str): Path to save the figure.
        title (Optional[str]): Title of the chart.
    """
    from BEASTsim.utils.utils import _format_name_html
    from math import ceil
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    sub_titles = list(data_dict.keys())  # Extract subplot titles
    data_list = list(data_dict.values())  # Extract datasets for subplots

    cols = len(data_list)  # One row, multiple columns
    rows = 1

    fig = make_subplots(
        rows=rows, cols=cols,
        subplot_titles=[f"<b>{sub_title}</b>" for sub_title in sub_titles],
        specs=[[{'type': 'polar'}] * cols for _ in range(rows)],
        vertical_spacing=0.2,
        horizontal_spacing=0.05
    )

    # Extract benchmark names per subplot while preserving order
    benchmark_titles_dict = {}

    for idx, data in enumerate(data_list):
        benchmarks = []

        # Get unique benchmarks in order of appearance
        for df in data.values():
            if isinstance(df, (DataFrame, Series)):
                for item in df.index.tolist():
                    if item not in benchmarks:
                        benchmarks.append(item)

        benchmarks.append(benchmarks[0])  # Close the loop
        benchmark_titles_dict[idx] = [_format_name_html(b) for b in benchmarks]

    # Extract simulation technique names in order of appearance
    ordered_sim_names = []
    for data in data_list:
        for sim_name in data.keys():
            if sim_name not in ordered_sim_names:
                ordered_sim_names.append(sim_name)

    # Assign colors to each simulation technique
    if color_palette is None:
        color_palette = [
        "darkslategray", "maroon", "green", "blue", "darkorange",
        "gold", "lightgreen", "darkturquoise", "cornflowerblue",
        "hotpink", "darkcyan", "red"
        ]

    if len(ordered_sim_names) > len(color_palette):
        raise ValueError(
            f"Number of simulation methods ({len(ordered_sim_names)}) exceeds the available colors ({len(color_palette)}). "
            "Please provide additional colors.")

    color_map = {name: color for name, color in zip(ordered_sim_names, color_palette)}

    # Add traces to the plot
    for idx, data in enumerate(data_list):
        row, col = divmod(idx, cols)

        for sim_name in ordered_sim_names:
            df = data.get(sim_name, None)
            scores = df.iloc[:, 0].tolist() if isinstance(df, DataFrame) else (
                df.tolist() if isinstance(df, Series) else [])

            if scores:  # Only add non-empty data
                scores.append(scores[0])  # Close the loop

                fig.add_trace(go.Scatterpolar(
                    r=scores,
                    theta=benchmark_titles_dict[idx],
                    fill=None,
                    name=sim_name,
                    showlegend=(idx == 0),  # Show legend only once
                    line=dict(color=color_map.get(sim_name, 'black'))
                ), row=row + 1, col=col + 1)

    # Define polar layout settings
    polar_layouts = {
        f"polar{idx + 1 if idx > 0 else ''}": dict(
            radialaxis=dict(
                visible=True,
                range=[-0.1, 1],
                tickvals=[0, 0.25, 0.5, 0.75, 1],
                showline=False
            ),
            angularaxis=dict(
                rotation=90,
                tickfont=dict(size=12, weight="bold"),
                tickangle=0,
                direction="clockwise",
                ticks="outside",
                showline=False,
                tickvals=[i for i in range(len(benchmark_titles_dict[idx]))],
                ticktext=benchmark_titles_dict[idx],
                ticklen=10
            ),
            gridshape="linear"
        ) for idx in range(len(data_list))
    }

    # Update layout with legend and formatting
    fig.update_layout(
        **polar_layouts,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.2 - 0.05 * ceil(len(ordered_sim_names) / 3),
            xanchor="center",
            x=0.5,
            traceorder="normal",
            font=dict(size=12, weight="bold"),
            bgcolor="rgba(255,255,255,0.7)",
            itemsizing="constant"
        ),
        showlegend=True,
        width=700 * cols,
        height=700 * rows,
        margin=dict(t=150, b=0, l=0, r=0)
    )

    if title is not None:
        fig.update_layout(
            title=title,
            title_x=0.5,
            title_y=0.98,
            title_font=dict(size=24, family="Arial, sans-serif", color="black", weight="bold"),
        )

    # Adjust subplot title positions
    for annotation in fig['layout']['annotations']:
        annotation['font'] = dict(size=18, family="Arial, sans-serif", color="black", weight="bold")
        annotation['y'] += 0.2  # Moves subplot titles up slightly

    fig.write_image(save_path, scale=3)

def load_raw_plotting_data(data_paths, verbose=False):
    import pickle
    data = {}
    for id, data_path in data_paths.items():
        with open(data_path, "rb") as fh:
            if verbose:
                print(f"Loading raw plotting data at {data_path}.")
            raw_plotting_data = pickle.load(fh)
        data[id] = raw_plotting_data
    return data

def _benchmark_type_score_type_format_plotting_data(data, benchmark_type, score_type, sim_base_names):
    import pandas as pd
    id_keys = list(data.keys())
    score_matrix = {sim_base_name: None for sim_base_name in sim_base_names}
    for key in score_matrix.keys():
        try:
            score_matrix[key] = [data[id_keys[i]][benchmark_type][f'{key}_{id_keys[i]}'][score_type] for i in range(len(id_keys))]
        except Exception:
            score_matrix[key] = [data[id_keys[i]][benchmark_type][f'{key}_{id_keys[i]}'].loc[score_type].iloc[0] for i in range(len(id_keys))]
    return pd.DataFrame(data=score_matrix).T

def _benchmark_type_format_plotting_data(data, benchmark_type, sim_base_names):
    id_keys = list(data.keys())
    method_names = list(data[id_keys[0]][benchmark_type].keys())
    score_names = list(data[id_keys[0]][benchmark_type][method_names[0]].axes[0])
    score_data = {score : None for score in score_names}
    for key in score_data.keys():
        score_data[key] = _benchmark_type_score_type_format_plotting_data(data, benchmark_type, key, sim_base_names)
    return score_data

def format_plotting_data(data, sim_base_names, save_path=None, save=True, load=False):
    import pickle
    if save_path is None:
        save_path = "BEASTsim\Output\Benchmarking\Simulation"
    if load:
        with open(save_path, "rb") as fh:
            print(f"Loading raw plotting data at {save_path}.")
            benchmark_score_data = pickle.load(fh)
    else:
        id_keys = list(data.keys())
        benchmark_types = list(data[id_keys[0]].keys())
        for key in data.keys():
            if list(data[key].keys()) != benchmark_types :
                ValueError(f'Mismatch in data keys: {benchmark_types} and {list(data[key].keys())}')
        benchmark_score_data = {benchmark_type: None for benchmark_type in benchmark_types}
        for benchmark_type in benchmark_types:
            benchmark_score_data[benchmark_type] = _benchmark_type_format_plotting_data(data, benchmark_type, sim_base_names)
        if save:
            with open(save_path, "wb") as fh:
                pickle.dump(benchmark_score_data, fh, protocol=pickle.HIGHEST_PROTOCOL)
    return benchmark_score_data

def create_benchmark_score_boxplot(
    score_dict,
    method_order=None,
    score_order=None,
    color_discrete_sequence=None,
    show=True,
    save_path=None,
    save_format="html",
    add_dividers=True,
    divider_line_kwargs=None,
    title='Boxplot',
    method_labels=None,
    height= 500,
    xaxis_title_standoff=20,
    width = 600
):
    from BEASTsim.utils.utils import _format_name_html
    import plotly.express as px
    import pandas as pd
    long_frames = []
    for score_name, df in score_dict.items():
        tmp = df.copy()
        tmp["method"] = tmp.index
        tmp_long = tmp.melt(
            id_vars="method",
            var_name="run",
            value_name="value",
        )
        tmp_long["score"] = score_name
        long_frames.append(tmp_long[["score", "method", "value"]])

    data_long = pd.concat(long_frames, ignore_index=True)

    if method_order is None:
        method_order = sorted(data_long["method"].unique())
    if score_order is None:
        score_order = list(score_dict.keys())

    if method_labels is not None:
        if len(method_labels) != len(method_order):
            raise ValueError("method_labels must have same length as method_order")
        name_map = dict(zip(method_order, method_labels))
        data_long["method_display"] = data_long["method"].map(name_map)

        color_col = "method_display"
        method_category_order = method_labels
    else:
        color_col = "method"
        method_category_order = method_order
    fig = px.box(
        data_long,
        x="score",
        y="value",
        color=color_col,
        category_orders={
            "score": score_order,
            color_col: method_category_order,
        },
        color_discrete_sequence=color_discrete_sequence,
    )
    fig.update_traces(
        marker=dict(
            size=5,
            opacity=1,
        ),
        selector=dict(type="box"),
    )
    formatted_scores = {s: _format_name_html(s) for s in score_order}
    fig.update_xaxes(
        tickmode="array",
        tickvals=score_order,
        ticktext=[formatted_scores[s] for s in score_order],
        tickangle=0,
        tickfont=dict(
            family="Arial, sans-serif",
            color="black",
            weight="bold"
        ),
        title_standoff=xaxis_title_standoff,
    )
    fig.update_layout(
        boxmode="group",
        boxgap=0.2,
        boxgroupgap=0.1,
        xaxis_title="",
        yaxis_title="<b>Score Value</b>",
        template="plotly_white",
        height=height,
        width=width,
        xaxis_title_font=dict(family="Arial, sans-serif", color="black", weight="bold"),
        yaxis_title_font=dict(family="Arial, sans-serif", color="black", weight="bold"),
        font=dict(family="Arial, sans-serif", color="black", weight="bold"),
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.2,
            xanchor="center",
            x=0.5,
        ),
    )
    fig.update_yaxes(range=[0, 1])
    if add_dividers and len(score_order) > 1:
        if divider_line_kwargs is None:
            divider_line_kwargs = {
                "width": 1,
                "dash": "dot",
                "color": "gray",
            }
        n_scores = len(score_order)
        shapes = list(fig.layout.shapes) if fig.layout.shapes else []

        for i in range(n_scores - 1):
            boundary = (i + 1) / n_scores
            shapes.append(
                {
                    "type": "line",
                    "xref": "paper",
                    "yref": "paper",
                    "x0": boundary,
                    "x1": boundary,
                    "y0": 0,
                    "y1": 1,
                    "line": divider_line_kwargs,
                    "layer": "below",
                }
            )
        fig.update_layout(shapes=shapes)
    fig.update_layout(
        title=dict(
            text=title,
            x=0.5,
            xanchor="center",
            y=0.98,
            yanchor="top",
            font=dict(size=24, family="Arial, sans-serif", color="black", weight="bold"),
        )
    )
    fig.update_layout(legend_title_text="")
    if save_path is not None:
        if save_format == "html":
            fig.write_html(save_path)
        else:
            fig.write_image(save_path, format=save_format)
    if show:
        fig.show()

    return fig

def create_boxplots(benchmark_score_data, save_path=r'C:\Users\krp\PycharmProjects\MOPITAS', save_name = 'boxplot', save_format="pdf", show = False):
    for key in list(benchmark_score_data.keys()):
        width = 100+100*len(benchmark_score_data[key].keys())
        colors = ["darkslategray", "maroon", "green", "darkturquoise", "blue", "darkorange"]
        method_labels = ['scCube_rfb', 'scCube_rf_𝛿10_𝜆1_c1', 'scDesign3_rb_p1_f0_b1', 'spatialcoGCN', 'SRTsim_rb_domain', 'SRTsim_rf_domain_random']
        first_score = next(iter(benchmark_score_data[key].values()))
        method_order = list(first_score.index)
        create_benchmark_score_boxplot(benchmark_score_data[key], show = show, save_format = save_format,
                                 save_path=os.path.join(save_path, f'{save_name}_{key}.{save_format}'),
                                 add_dividers=True, divider_line_kwargs={"width": 2.0, "dash": "dash", "color": "lightgray"},
                                 title = key, method_order=method_order, color_discrete_sequence=colors, method_labels = method_labels,
                                 height = 500, width = width, xaxis_title_standoff=0)


def plot_cell_type_locations(adata: AnnData, save_path): # TODO: 0 usage?? Holm code?
    from matplotlib.pyplot import scatter, xlabel, ylabel, colorbar, savefig
    x = adata.obs.X.values
    y = adata.obs.Y.values
    probs = adata.obsm["probabilities"].to_numpy()
    selected_cell_type_probs = probs[:, 3]
    scatter(x, y, c=selected_cell_type_probs, cmap="viridis", s=10)
    xlabel("X")
    ylabel("Y")
    colorbar(label="Probability")
    savefig(save_path)

def plot_robustness(
    adatas: list[AnnData], cell_types: list[int], save_path
):
    """
    Plots a robustness plot given an array of AnnData objets containing proper cell type location probabilities. Outputs a figure that dynamically scales to to add room for more each run and cell type.

    Parameters:
        adatas:
            Array containing AnnData Objects representing multiple applications of some spatial cellular abbundance model.
            Each AnnData Object needs to have a "probabilities" value in the obsm field, containing a DataFrame with the probabilities for each celltype to be a each cell location.
            The Rows in the DataFrame should be the cell locations, each row should represent a given cell location, and the columns should be the probabilities for each cell type to be at a given location.
        cell_types:
            Array containing the indexes of the celltypes that the robustness is measured on.
        save_path:
            Path to save the generated figure to.
    """
    from matplotlib.pyplot import ioff, subplots, tight_layout, savefig, ion
    from random import sample
    assert (
        len(adatas) > 0
    ), "No Adata objects were detected, please make certain to pass the data from the runs"
    if len(cell_types) < 1:
        cell_types = len(adatas[0].obsm["probabilities"].columns.tolist())
        potential_choices = range(0, cell_types)
        if cell_types < 4:
            samples = cell_types
        else:
            samples = 4
        cell_types = sample(potential_choices, k=samples)
    cols = len(adatas)
    rows = len(cell_types)
    ioff()
    figure, axs = subplots(rows, cols, figsize=(cols * 7.5, rows * 5))
    for i, cell_type in enumerate(cell_types):
        for j, data in enumerate(adatas):
            ax = axs[i, j]
            x = data.obs.X.values
            y = data.obs.Y.values
            cell_type_name = data.obsm["probabilities"].columns.tolist()[cell_type]
            probs = data.obsm["probabilities"].to_numpy()
            probs_cell_type = probs[:, cell_type]
            scatter_plot = ax.scatter(x, y, c=probs_cell_type, cmap="viridis", s=10)
            figure.colorbar(scatter_plot, ax=ax, label="Probability")
            ax.set_xlabel("X")
            ax.set_ylabel("Y")
            ax.set_title(f"Cell type {cell_type_name}")
    figure.suptitle("Robustness benchmark")
    tight_layout()
    savefig(save_path)
    ion()

def calc_width_ratios(datas):
    total_length = 0
    dfs = []
    for data in datas:
        df = data
        dfs.append(df)
        total_length += len(df.columns)
    return [len(df.columns)/total_length for df in dfs]

def create_comparison_benchmarks(datas,max_dot_size,min_dot_size,names,save_path):
    from seaborn import color_palette, set_theme, scatterplot, despine
    from matplotlib.gridspec import GridSpec
    import matplotlib.pyplot as plt

    if not isinstance(datas, list) or not all(isinstance(df, DataFrame) for df in datas):
        raise ValueError("datas must be a list of pandas DataFrames.")
    if len(datas) != len(names):
        raise ValueError("The length of datas and names must be the same.")
    width_ratios = calc_width_ratios(datas)
    fig = plt.figure(figsize=(8*len(datas), 8))
    gs = GridSpec(2,len(datas),width_ratios = width_ratios,height_ratios = [1,0.3])
    cmap = color_palette("Blues", as_cmap=True)
    axis = []
    set_theme(style='whitegrid')
    plt.rcParams["font.family"] = "DejaVu Sans"
    for i,data in enumerate(datas):
        df = data
        current_ax = fig.add_subplot(gs[0,i])
        # Melt the dataframe for easier plotting with seaborn
        df_melted = df.melt(id_vars='Method', var_name='Category', value_name='Rank')
        min_val = df_melted['Rank'].min()
        max_val =df_melted['Rank'].max()
        keys = list(range(max_val,min_val - 1,-1))
        values = list(range(min_val,max_val + 1))
        size_mapping = dict(zip(keys,values))
        #calculate slope for scaling dot sizes linearly
        slope = max_dot_size/max_val

        df_melted['size'] = df_melted['Rank'].map(size_mapping)*slope + min_dot_size
        scatter = scatterplot(data=df_melted, x='Category', y='Method', size='size', hue='Rank', palette=cmap, sizes=(50, 500),ax=current_ax,legend=False,edgecolor='black')
        current_ax.set_title(names[i])
        if i != 0:
            current_ax.spines["left"].set_visible(False)
            current_ax.get_yaxis().set_ticks([]) # TODO find alternative for this.
            current_ax.set_xlabel("")
            current_ax.set_ylabel("")
        axis.append(current_ax)
    normalized = plt.Normalize(df_melted['Rank'].min(),df_melted['Rank'].max())
    scalar_map = plt.cm.ScalarMappable(cmap=cmap,norm=normalized)
    scalar_map.set_array([])
    cbar_ax = fig.add_subplot(gs[1,:])
    fig.colorbar(scalar_map,label="Rank",ax=cbar_ax,orientation = "horizontal",fraction = 0.1, pad= 0)
    despine()
    for i in range(len(datas)):
        plt.sca(axis[i])
        plt.xticks(rotation=45, ha='right')
    handles = [plt.Line2D([], [], marker='o', color='w', markerfacecolor='grey', markersize=size_mapping[cat]*slope + min_dot_size, label=cat) for cat in sorted(size_mapping.keys())]
    cbar_ax.axis("off")
    cbar_ax.legend(title='Rank', loc='lower center',labelspacing = 1,handles = handles,ncol=len(size_mapping.keys()))
    cbar_ax.set_aspect(0.01)
    plt.gca().set(xlabel='', ylabel='')

    plt.tight_layout()
    plt.savefig(save_path)

def create_comparison_benchmarks_new_suggestion(datas, max_dot_size, min_dot_size, names, save_path): #TODO: What is this? 0 usage?
    """
    Creates a comparison benchmark plot with custom colorbar position and size legend.

    Parameters:
    - datas: List of pandas DataFrames containing the data.
    - max_dot_size: Maximum size for the dots.
    - min_dot_size: Minimum size for the dots.
    - names: List of names for each subplot.
    - save_path: Path to save the output plot.

    Returns:
    - None
    """
    from pandas import concat
    from seaborn import set_theme, scatterplot
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    from sklearn.preprocessing import MinMaxScaler
    from numpy import linspace

    if not isinstance(datas, list) or not all(isinstance(df, DataFrame) for df in datas):
        raise ValueError("datas must be a list of pandas DataFrames.")
    if len(datas) != len(names):
        raise ValueError("The length of datas and names must be the same.")

    all_ranks = concat([
        df.melt(id_vars='Method', var_name='Category', value_name='Rank')['Rank']
        for df in datas
    ])
    global_min_rank = all_ranks.min()
    global_max_rank = all_ranks.max()

    set_theme(style='whitegrid')

    fig, axes = plt.subplots(1, len(datas), figsize=(8 * len(datas), 14), sharey=True)
    if len(datas) == 1:
        axes = [axes]

    scaler = MinMaxScaler(feature_range=(min_dot_size, max_dot_size))

    for i, (df, ax) in enumerate(zip(datas, axes)):
        df_melted = df.melt(id_vars='Method', var_name='Category', value_name='Rank')
        df_melted['SizeRank'] = global_max_rank - df_melted['Rank'] + global_min_rank
        df_melted['ScaledSize'] = scaler.fit_transform(df_melted[['SizeRank']])

        scatter = scatterplot(
            data=df_melted,
            x='Category',
            y='Method',
            size='ScaledSize',
            hue='Rank',
            palette='coolwarm',
            ax=ax,
            legend=False
        )
        ax.set_title(names[i])
        if i != 0:
            ax.set_ylabel('')
        ax.set_xlabel('Category')
        ax.tick_params(axis='x', rotation=45)

    fig.text(0.04, 0.5, 'Method', va='center', rotation='vertical')

    norm = plt.Normalize(global_min_rank, global_max_rank)
    sm = plt.cm.ScalarMappable(cmap='coolwarm', norm=norm)
    sm.set_array([])

    cbar_ax = fig.add_axes([0.15, 0.07, 0.4, 0.02])  # [left, bottom, width, height]
    cbar = fig.colorbar(sm, cax=cbar_ax, orientation='horizontal')
    cbar.set_label('Rank')

    # Select representative rank values
    size_legend_ranks = linspace(global_min_rank, global_max_rank, num=len(df)).astype(int)
    size_legend_sizes = scaler.transform(size_legend_ranks.reshape(-1, 1)).flatten()


    legend_handles = [
        Line2D(
            [], [], marker='o', color='w', markerfacecolor='gray',
            markersize=size, label=str(rank), linestyle='None'
        )
        for rank, size in zip(size_legend_ranks, size_legend_sizes)
    ]

    legend_ax = fig.add_axes([0.15, 0.02, 0.4, 0.02])
    legend_ax.axis('off')
    legend_ax.legend(
        handles=legend_handles, title='Rank (Size)',
        loc='center', ncol=len(size_legend_ranks), frameon=False
    )

    plt.tight_layout(rect=[0, 0.1, 1, 1])

    plt.savefig(save_path)
    plt.close(fig)

def plot_similarity_dotplot(
    results: dict,
    *,
    benchmark_name: str = "SimilarityBenchmark",
    title: str = "Similarity",
    cmap: str = "RdYlBu_r",
    group_sep: str = "_",
    tool_short_names: Optional[dict] = None,
    dataset_display_names: Optional[dict] = None,
    thresholds: tuple[float, float] = (0.4, 0.8),
    size_map: Optional[dict] = None,
    overall_bottom_label: str = "",
    drop_cols: tuple[str, ...] = ("AvgRank", "OverallRank"),
    save_path: Optional[str] = None,
    dpi: int = 300,
    figsize: Optional[tuple[float, float]] = None,
):
    """
    Creates a similarity dotplot where color encodes raw similarity and dot size encodes similarity category.
    Parameters:
        results (dict): Nested dict results[dataset][tool][benchmark] = object.
        benchmark_name (str): Benchmark to plot (default: "SimilarityBenchmark").
        title (str): Figure title.
        cmap (str): Matplotlib colormap for raw similarity.
        group_sep (str): Separator between dataset prefix and tool name in column keys.
        tool_short_names (dict | None): Mapping of tool keys -> short labels shown on x-axis (unknown -> blank).
        dataset_display_names (dict | None): Mapping of dataset prefix -> display label for top brackets.
        thresholds (Tuple[float, float]): (medium_threshold, high_threshold) for Low/Medium/High.
        size_map (dict | None): Mapping {"Low": size, "Medium": size, "High": size}.
        overall_bottom_label (str): Bottom label under the Overall column (often blank).
        drop_cols (Tuple[str, ...]): Columns to drop before plotting (leaderboard columns).
        save_path (str | None): Optional path to save PNG/PDF.
        dpi (int): Save DPI.
        figsize (Tuple[float, float] | None): Optional fixed figsize.
    Returns:
        None
    """
    import numpy as np
    import pandas as pd
    import matplotlib.pyplot as plt

    from BEASTsim.utils.utils import build_raw_table, build_similarity_category_table

    _configure_matplotlib_bold()

    tool_short_names = tool_short_names or _default_tool_short_names()
    dataset_display_names = dataset_display_names or _default_dataset_display_names()
    size_map = size_map or {"Low": 30, "Medium": 90, "High": 180}

    med_thr, high_thr = thresholds

    df_raw = build_raw_table(results, benchmark_name)
    df_cat = build_similarity_category_table(
        results,
        benchmark_name,
        thresholds=thresholds,
        labels=("Low", "Medium", "High"),
    )

    df_raw_plot = df_raw.drop(columns=[c for c in drop_cols if c in df_raw.columns], errors="ignore").copy()
    df_cat_plot = df_cat.drop(columns=[c for c in drop_cols if c in df_cat.columns], errors="ignore").copy()

    cols = [c for c in df_raw_plot.columns if c in df_cat_plot.columns]
    if "OverallSimilarity" in df_raw_plot.columns:
        cols.append("OverallSimilarity")
    rows = list(df_raw_plot.index)

    def short_label(tool: str) -> str:
        return tool_short_names.get(tool.strip().lower(), "")

    prefixes, bottom_labels = [], []
    for col in cols:
        if col == "OverallSimilarity":
            prefixes.append("overall")
            bottom_labels.append(overall_bottom_label)
            continue
        dataset, tool = _parse_dataset_and_tool(col, group_sep)
        prefixes.append(dataset)
        bottom_labels.append(short_label(tool))

    xs, ys, colors, sizes = [], [], [], []
    for i, row in enumerate(rows):
        for j, col in enumerate(cols):
            raw = df_raw_plot.loc[row, col]
            if pd.isna(raw):
                continue

            cat = (
                df_cat_plot.loc[row, "OverallSimilarityCategory"]
                if col == "OverallSimilarity"
                else df_cat_plot.loc[row, col]
            )
            if pd.isna(cat):
                continue

            xs.append(j)
            ys.append(i)
            colors.append(float(raw))
            sizes.append(float(size_map.get(str(cat), 60)))

    colors = np.asarray(colors, dtype=float)
    sizes = np.asarray(sizes, dtype=float)

    if figsize is None:
        fig_w = max(7, 0.65 * len(cols) + 4)
        fig_h = max(4, 0.45 * len(rows) + 2.3)
        figsize = (fig_w, fig_h)

    fig, ax = plt.subplots(figsize=figsize)

    sc = ax.scatter(
        xs, ys,
        s=sizes,
        c=colors,
        cmap=cmap,
        vmin=0, vmax=1,
        edgecolors="black",
        linewidths=0.4,
    )

    ax.set_xticks(range(len(cols)))
    ax.set_xticklabels(bottom_labels, rotation=0, ha="center", fontweight="bold")
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels(rows, fontweight="bold")

    ax.set_xlim(-0.5, len(cols) - 0.5)
    ax.set_ylim(len(rows) - 0.5, -0.5)
    ax.set_title(title, pad=55, fontweight="bold")

    ax.set_xticks(np.arange(-0.5, len(cols), 1), minor=True)
    ax.set_yticks(np.arange(-0.5, len(rows), 1), minor=True)
    ax.grid(which="minor", linewidth=0.6, alpha=0.2)
    ax.tick_params(which="minor", bottom=False, left=False)

    cbar = plt.colorbar(sc, ax=ax, orientation="horizontal", fraction=0.05, pad=0.12, aspect=30)
    cbar.set_ticks([0.0, med_thr, high_thr, 1.0])
    cbar.set_label("Similarity score", labelpad=6, fontweight="bold")
    for t in cbar.ax.get_xticklabels():
        t.set_fontweight("bold")

    ranges = {
        "Low": f"[0, {med_thr:.1f}]",
        "Medium": f"({med_thr:.1f}, {high_thr:.1f}]",
        "High": f"({high_thr:.1f}, 1]",
    }
    handles, labels = [], []
    for lab in ["Low", "Medium", "High"]:
        h = ax.scatter([], [], s=size_map[lab], c="lightgray", edgecolors="black", linewidths=0.4)
        handles.append(h)
        labels.append(f"{lab} {ranges[lab]}")

    leg = ax.legend(
        handles, labels,
        title="Similarity",
        loc="upper left",
        bbox_to_anchor=(1.02, 0.55),
        frameon=False,
        borderaxespad=0,
    )
    leg.get_title().set_fontweight("bold")
    for t in leg.get_texts():
        t.set_fontweight("bold")

    _add_top_brackets(ax, prefixes, dataset_display_names)

    plt.tight_layout()
    if save_path is not None:
        plt.savefig(save_path, dpi=dpi, bbox_inches="tight")
    plt.show()


def plot_rank_bubble_dotplot(
    nested_results: dict,
    *,
    average_rank: bool,
    benchmark_name: str,
    title: Optional[str] = None,
    cmap: str = "RdYlBu",
    group_sep: str = "_",
    tool_short_names: Optional[dict] = None,
    dataset_display_names: Optional[dict] = None,
    overall_bottom_label: str = "",
    overall_col_candidates: tuple[str, ...] = ("OverallSimilarity", "Overall", "Overall Score", "OverallSimilarityScore"),
    size_range: tuple[float, float] = (30, 180),
    drop_cols: tuple[str, ...] = ("AvgRank", "OverallRank"),
    save_path: Optional[str] = None,
    dpi: int = 300,
    figsize: Optional[tuple[float, float]] = None,
    invert_colorbar: bool = True,
):
    """
    Creates a bubble dotplot for rank-like benchmark tables.
    Parameters:
        nested_results (dict): Nested dict results[dataset][method][benchmark] = scores/object.
        average_rank (bool): If True, lower values are better (avg-rank scenario).
        benchmark_name (str): Benchmark key to plot.
        title (str | None): Optional plot title.
        cmap (str): Matplotlib colormap (reversed automatically when average_rank=True).
        group_sep (str): Separator between dataset prefix and tool name in column keys.
        tool_short_names (dict | None): Mapping tool key -> short label (unknown -> blank).
        dataset_display_names (dict | None): Mapping dataset prefix -> display label for top brackets.
        overall_bottom_label (str): Bottom label under the Overall column (often blank).
        overall_col_candidates (Tuple[str, ...]): Preferred names for the Overall column.
        size_range (Tuple[float, float]): (min_dot_size, max_dot_size).
        drop_cols (Tuple[str, ...]): Columns to drop before plotting (leaderboard columns).
        save_path (str | None): Optional path to save output.
        dpi (int): Save DPI.
        figsize (Tuple[float, float] | None): Optional fixed figsize.
        invert_colorbar (bool): If True, invert colorbar when average_rank=True.
    Returns:
        None
    """
    import numpy as np
    import pandas as pd
    import matplotlib.pyplot as plt

    from BEASTsim.utils.utils import summarize_benchmark_results, build_raw_table

    _configure_matplotlib_bold()

    tool_short_names = tool_short_names or _default_tool_short_names()
    dataset_display_names = dataset_display_names or _default_dataset_display_names()

    cmap_to_use = f"{cmap}_r" if average_rank else cmap

    avg_scores, _ = summarize_benchmark_results(nested_results, average_rank)
    df_raw = build_raw_table(avg_scores, benchmark_name)
    df_plot = df_raw.drop(columns=[c for c in drop_cols if c in df_raw.columns], errors="ignore").copy()

    overall_col = next((c for c in overall_col_candidates if c in df_plot.columns), None)
    if overall_col is None:
        overall_col = next((c for c in df_plot.columns if "overall" in str(c).lower()), None)

    if overall_col is not None:
        df_plot = df_plot.sort_values(by=overall_col, ascending=average_rank)

    cols = list(df_plot.columns)
    rows = list(df_plot.index)

    def short_label(tool: str) -> str:
        return tool_short_names.get(tool.strip().lower(), "")

    prefixes, bottom_labels = [], []
    for col in cols:
        if overall_col is not None and col == overall_col:
            prefixes.append("overall")
            bottom_labels.append(overall_bottom_label)
            continue
        dataset, tool = _parse_dataset_and_tool(col, group_sep)
        prefixes.append(dataset)
        bottom_labels.append(short_label(tool))

    ranks = pd.DataFrame(index=df_plot.index, columns=df_plot.columns, dtype=float)
    for col in cols:
        ranks[col] = df_plot[col].rank(ascending=average_rank, method="min")

    min_size, max_size = size_range

    def rank_to_size(r: float, r_max: float) -> float:
        if pd.isna(r) or pd.isna(r_max) or r_max <= 1:
            return (min_size + max_size) / 2
        return min_size + (r_max - r) * (max_size - min_size) / (r_max - 1)

    col_rank_max = {c: float(ranks[c].max(skipna=True)) for c in cols}

    xs, ys, colors, sizes = [], [], [], []
    for i, row in enumerate(rows):
        for j, col in enumerate(cols):
            v = df_plot.loc[row, col]
            if pd.isna(v):
                continue
            xs.append(j)
            ys.append(i)
            colors.append(float(v))
            sizes.append(rank_to_size(float(ranks.loc[row, col]), float(col_rank_max.get(col, np.nan))))

    colors = np.asarray(colors, dtype=float)
    sizes = np.asarray(sizes, dtype=float)

    vmin = float(np.nanmin(colors)) if colors.size else 0.0
    vmax = float(np.nanmax(colors)) if colors.size else 1.0

    if figsize is None:
        fig_w = max(7, 0.85 * len(cols) + 3)
        fig_h = max(4, 0.45 * len(rows) + 2.3)
        figsize = (fig_w, fig_h)

    fig, ax = plt.subplots(figsize=figsize)

    sc = ax.scatter(
        xs, ys,
        s=sizes,
        c=colors,
        cmap=cmap_to_use,
        vmin=vmin, vmax=vmax,
        edgecolors="black",
        linewidths=0.4,
    )

    ax.set_xticks(range(len(cols)))
    ax.set_xticklabels(bottom_labels, rotation=0, ha="center", fontweight="bold")
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels(rows, fontweight="bold")

    ax.set_xlim(-0.5, len(cols) - 0.5)
    ax.set_ylim(len(rows) - 0.5, -0.5)
    ax.set_title(title if title is not None else benchmark_name, pad=55, fontweight="bold")

    ax.set_xticks(np.arange(-0.5, len(cols), 1), minor=True)
    ax.set_yticks(np.arange(-0.5, len(rows), 1), minor=True)
    ax.grid(which="minor", linewidth=0.6, alpha=0.2)
    ax.tick_params(which="minor", bottom=False, left=False)

    cbar = plt.colorbar(sc, ax=ax, orientation="horizontal", fraction=0.05, pad=0.12, aspect=30)
    if invert_colorbar and average_rank:
        cbar.ax.invert_xaxis()
    cbar.set_label("Value", labelpad=6, fontweight="bold")
    for t in cbar.ax.get_xticklabels():
        t.set_fontweight("bold")

    global_max_rank = int(np.nanmax([col_rank_max[c] for c in cols if not pd.isna(col_rank_max[c])] or [1]))
    show_ranks = (
        [1, (global_max_rank + 1) // 2, global_max_rank]
        if global_max_rank >= 3
        else list(range(1, global_max_rank + 1))
    )

    handles, labels = [], []
    for rr in show_ranks:
        h = ax.scatter([], [], s=rank_to_size(rr, global_max_rank), c="lightgray",
                       edgecolors="black", linewidths=0.4)
        handles.append(h)
        labels.append(f"{rr}")

    leg = ax.legend(
        handles, labels,
        title="Rank",
        loc="upper left",
        bbox_to_anchor=(1.02, 0.55),
        frameon=False,
        borderaxespad=0,
    )
    leg.get_title().set_fontweight("bold")
    for t in leg.get_texts():
        t.set_fontweight("bold")

    _add_top_brackets(ax, prefixes, dataset_display_names)

    plt.tight_layout()
    if save_path is not None:
        plt.savefig(save_path, dpi=dpi, bbox_inches="tight")
    plt.show()


# -------------------------
# Internal helpers (private)
# -------------------------

def _configure_matplotlib_bold(xtick_size: int = 11, ytick_size: int = 11) -> None:
    import matplotlib.pyplot as plt
    plt.rcParams.update({
        "font.weight": "bold",
        "axes.labelweight": "bold",
        "axes.titleweight": "bold",
        "xtick.labelsize": xtick_size,
        "ytick.labelsize": ytick_size,
    })


def _default_tool_short_names() -> dict:
    return {"spapros": "Spa", "spatialde": "SVG"}


def _default_dataset_display_names() -> dict:
    return {"visium": "Visium", "merfish": "MERFISH", "xenium": "Xenium", "overall": "Overall"}


def _parse_dataset_and_tool(col: str, group_sep: str) -> tuple[str, str]:
    if group_sep in col:
        a, b = col.split(group_sep, 1)
        return a, b
    return col, ""


def _runs(values: list[str]) -> list[tuple[str, int, int]]:
    out = []
    start = 0
    for k in range(1, len(values) + 1):
        if k == len(values) or values[k] != values[start]:
            out.append((values[start], start, k - 1))
            start = k
    return out


def _add_top_brackets(ax, prefixes: list[str], dataset_display_names: dict) -> None:
    for name, a, b in _runs(prefixes):
        ax.plot([a - 0.4, b + 0.4], [-1.15, -1.15], color="black", linewidth=1.0, clip_on=False)
        ax.plot([a - 0.4, a - 0.4], [-1.15, -0.95], color="black", linewidth=1.0, clip_on=False)
        ax.plot([b + 0.4, b + 0.4], [-1.15, -0.95], color="black", linewidth=1.0, clip_on=False)

        label = dataset_display_names.get(str(name).lower(), name)
        ax.text(
            (a + b) / 2, -1.40, label,
            ha="center", va="bottom",
            fontsize=11, fontweight="bold",
            clip_on=False,
        )