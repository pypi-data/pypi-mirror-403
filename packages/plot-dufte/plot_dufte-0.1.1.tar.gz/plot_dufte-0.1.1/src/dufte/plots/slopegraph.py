import pandas as pd
from plotnine import ggplot, aes, geom_line, geom_point, geom_text, labs, theme, element_blank
from ..config_theme import (
    tufte_theme, 
    TUFTE_FONT,
    TUFTE_POINT_SIZE_SMALL,
    TUFTE_DARK,
    TUFTE_LINE_SIZE,
    TUFTE_FONT_PLOT_SIZE
)

def slopegraph(df:pd.DataFrame, category_col:str, year_col:str, value_col:str, title:str="Slopegraph") -> ggplot:
    """
    Erstellt einen Slopegraphen (Tufte's minimalistischer Linienvergleich).
    Zeigt die Veränderungen einzelner Kategorien über zwei Zeitpunkte.

    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame mit den Daten für den Plot.
    category_col : str
        Name der Spalte für die Kategorien (z.B. Länder).
    year_col : str
        Name der Spalte für die Zeitpunkte (z.B. Jahre).
    value_col : str
        Name der Spalte für die Werte (numerisch).
    title : str (Standardwert="Slopegraph") 
        Titel des Plots.

    Returns
    -------
    plot : plotnine.ggplot
        Ein ggplot-Objekt mit dem Slopegraph.
    
    """

    # Kopie des DataFrames erstellen, um Originaldaten nicht zu verändern
    df_copy = df.copy()

    # Sicherstellen, dass year_col als String behandelt wird
    df_copy[year_col] = df_copy[year_col].astype(str)
    years = sorted(df_copy[year_col].unique())
    start_year, end_year = years[0], years[-1]

    # Labels für linke und rechte Seite definieren
    left_labels = df_copy[df_copy[year_col] == start_year].copy()
    right_labels = df_copy[df_copy[year_col] == end_year].copy()

    # Linke Labels formatieren
    left_labels["label_text"] = (
        left_labels[category_col].astype(str) 
        + " " 
        + left_labels[value_col].astype(str)
    )

    # Rechte Labels formatieren
    right_labels["label_text"] = (
        right_labels[value_col].astype(str)
        + " "
        + right_labels[category_col].astype(str)
    )


    plot = (
        ggplot(df_copy, aes(x=year_col, y=value_col, group=category_col))
        
        # Linien und Punkte definieren
        + geom_line(size=TUFTE_LINE_SIZE, color=TUFTE_DARK)
        + geom_point(size=TUFTE_POINT_SIZE_SMALL)
        
        # Linke Labels
        + geom_text(
            aes(label="label_text"),
            data=left_labels,
            ha="right",
            nudge_x=-0.05,
            size=TUFTE_FONT_PLOT_SIZE * 0.8,
            family=TUFTE_FONT,
            color=TUFTE_DARK
        )
        # Rechte Labels
        + geom_text(
            aes(label="label_text"),
            data=right_labels,
            ha="left",
            nudge_x=0.05,
            size=TUFTE_FONT_PLOT_SIZE * 0.8,
            family=TUFTE_FONT,
            color=TUFTE_DARK
        )

        # Beschriftung
        + labs(title=title)

        # Tufte-Theme
        + tufte_theme()
        + theme(
            axis_text_y=element_blank(),
            axis_title=element_blank(),
            axis_ticks=element_blank(),
            axis_line=element_blank(),
            panel_grid=element_blank(),
        )
    )
    return plot