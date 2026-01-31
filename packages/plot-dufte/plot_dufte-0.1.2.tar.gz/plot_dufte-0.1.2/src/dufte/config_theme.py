from plotnine import theme, theme_minimal, element_blank, element_line, element_text, element_rect

# Farbenpalette
TUFTE_DARK = "#333333"
TUFTE_GREY = "#888888"
TUFTE_RED = "#bd0026"

# Schrift
TUFTE_FONT = "Arial"
TUFTE_FONT_PLOT_SIZE = 11
TUFTE_TITLE_POSITION = "center"

# Punkt-Größe
TUFTE_POINT_SIZE_SMALL = 1.5
TUFTE_POINT_SIZE_MEDIUM = 3.0

# Linien-Größe
TUFTE_LINE_SIZE = 0.5

# Sparkline-spezifische Konstanten
SPARKLINE_LINE_COLOR = TUFTE_DARK
SPARKLINE_ENDPOINT_COLOR = TUFTE_RED
SPARKLINE_ENDPOINT_SIZE = 2.0
SPARKLINE_LABEL_SIZE = 9


def tufte_theme() -> theme:
    """
    Minimalistisches Tufte-inspiriertes Theme für plotnine.

    Returns
    ------- 
    theme: plotnine.theme
        Ein angepasstes Plotnine Theme-Objekt nach Tuftes-Designprinzipien.
    """
    return (
        theme_minimal(base_size=TUFTE_FONT_PLOT_SIZE, base_family=TUFTE_FONT) +
        theme(
            # Hintergrund
            plot_background=element_rect(fill="white", color=None),
            panel_background=element_rect(fill="white", color=None),
            panel_border=element_blank(),
            plot_margin=0.025,
            
            # Rasterlinien
            panel_grid=element_blank(),
            
            # Achsen
            axis_line=element_line(color="black", size=TUFTE_LINE_SIZE),
            axis_ticks=element_line(color="black", size=TUFTE_LINE_SIZE),
            axis_ticks_length=3,
            
            # Typografie
            plot_title=element_text(
                size=TUFTE_FONT_PLOT_SIZE*1.2, 
                weight="bold", 
                ha=TUFTE_TITLE_POSITION,
                family=TUFTE_FONT
            ),
            axis_title=element_text(
                size=TUFTE_FONT_PLOT_SIZE*0.9, 
                face="italic", 
                ha="center",
                family=TUFTE_FONT
            ),
            axis_text=element_text(
                size=TUFTE_FONT_PLOT_SIZE*0.85, 
                color=TUFTE_DARK,
                family=TUFTE_FONT
            ),
            
            # Legende
            legend_background=element_blank(),
            legend_key=element_blank(),
            
            # Facetten
            strip_background=element_blank(),
            strip_text=element_text(
                face="bold", 
                ha="center",
                family=TUFTE_FONT
            )
        )
    )