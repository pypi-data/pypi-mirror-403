import altair as alt

# https://altair-viz.github.io/user_guide/configuration.html


def custom_theme():
    return {
        "config": {
            "axis": {"labelFontSize": 18, "titleFontSize": 22, "labelFlush": False},
            "header": {"labelFontSize": 18, "title": None},
            "legend": {"labelFontSize": 18, "titleFontSize": 22, "symbolOpacity": 1.0},
            "title": {"fontSize": 22},
            "header": {"titleFontSize": 22, "labelFontSize": 18},
            "view": {
                "continuousHeight": 540,
                "continuousWidth": 960,
                "discreteHeight": 540,
                "discreteWidth": 960,
            },
        }
    }


# register the custom theme under a chosen name
alt.themes.register("custom_theme", custom_theme)

# enable the newly registered theme
alt.themes.enable("custom_theme")
