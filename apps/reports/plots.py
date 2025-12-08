from bokeh.embed import components, file_html
from bokeh.layouts import column
from bokeh.models import ColumnDataSource, CustomJS, Select
from bokeh.palettes import Spectral6
from bokeh.plotting import figure
from bokeh.resources import CDN
from bokeh.transform import factor_cmap


def sale_inventory_bar_plot(sales_data):
    # Extract item names and totals

    # Extract item names and totals
    items = [item["stock__batch__item__name"] for item in sales_data]
    stocks = [int(item["stock__quantity"]) for item in sales_data]
    totals = [item["total"] for item in sales_data]
    total_facturation = [item["total_facturation"] for item in sales_data]

    # Create a ColumnDataSource
    source = ColumnDataSource(
        data={
            "items": items,
            "totals": totals,
            "stocks": stocks,
            "total_facturation": total_facturation,
        }
    )

    # Set the plot width based on the number of items
    plot_width = max(800, len(items) * 40)  # Adjust bar width as needed

    # Create a figure
    plot = figure(
        x_range=items,
        height=500,
        width=plot_width,
        title="Item vs Total",
        toolbar_location=None,
        tools="",
    )

    # Rotate x-axis labels vertically
    plot.xaxis.major_label_orientation = "vertical"  # or use 90 for 90 degrees

    # Create a bar plot
    bars = plot.vbar(
        x="items",
        top="totals",
        width=0.9,
        source=source,
        fill_color=factor_cmap("items", palette=Spectral6, factors=items),
    )

    # Add a Select widget to choose the metric
    select = Select(
        title="Select Metric:",
        value="totals",
        options=["totals", "total_facturation", "stocks"],
    )

    # JavaScript callback to update the plot
    callback = CustomJS(
        args=dict(source=source, bars=bars),
        code="""
        const metric = cb_obj.value;
        bars.glyph.top = {field: metric};  // Update the top attribute of the vbar glyph
        source.change.emit();
    """,
    )

    # Attach the callback to the Select widget
    select.js_on_change("value", callback)

    # Combine the plot and widget into a layout
    layout = column(select, plot)

    # Generate the HTML for the plot and widgets
    # plot_html = file_html(layout, CDN, "Item vs Total Bar Plot")
    # print("this is the bokeh string", plot_html)

    # Generate the script and div components
    script, div = components(layout)

    return script, div
