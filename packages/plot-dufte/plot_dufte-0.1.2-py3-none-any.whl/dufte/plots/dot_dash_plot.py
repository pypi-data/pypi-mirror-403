import pandas as pd
from plotnine import ggplot, aes, geom_point, geom_rug, labs, theme, element_blank
from ..config_theme import (
    tufte_theme, 
    TUFTE_POINT_SIZE_SMALL, 
    TUFTE_DARK
)


def dot_dash_plot(df:pd.DataFrame, x_col:str, y_col:str, title:str="Dot-Dash Plot") -> ggplot:
    """
    Erstellt einen Dot-Dash-Plot (Tufte's minimalistischer Scatter-Plot).
    Zeigt die Punktwolke mit einer Verteilung der Daten an den Achsen.

    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame mit den Daten für den Plot.
    x_col : str
        Name der Spalte für die X-Achse (numerisch).
    y_col : str
        Name der Spalte für die Y-Achse (numerisch).
    title : str (Standardwert="Dot-Dash Plot")
        Titel des Plots.

    Returns
    -------
    plot : plotnine.ggplot
        Ein ggplot-Objekt mit dem Dot-Dash-Plot.
    
    """
    plot = (
        ggplot(df, aes(x=x_col, y=y_col))
        
        # Punkte definieren 
        + geom_point(color=TUFTE_DARK, size=TUFTE_POINT_SIZE_SMALL, alpha=0.8)
        
        # Verteilungsränder hinzufügen
        + geom_rug(sides="bl", size=0.3, alpha=0.5, color=TUFTE_DARK)
        
        # Beschriftung
        + labs(title=title)

        # Tufte-Theme
        + tufte_theme()
        + theme(
            axis_line=element_blank()
        )
    )
    return plot