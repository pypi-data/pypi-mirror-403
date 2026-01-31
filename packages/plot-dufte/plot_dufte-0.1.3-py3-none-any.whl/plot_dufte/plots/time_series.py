import pandas as pd
from plotnine import ggplot, aes, geom_line, geom_point, labs, theme, element_blank
from ..config_theme import (
    tufte_theme, 
    TUFTE_DARK,
    TUFTE_POINT_SIZE_MEDIUM,
    TUFTE_LINE_SIZE
)


def time_series(df:pd.DataFrame, x_col:str, y_col:str, title:str="Time Series") -> ggplot:
    """
    Erstellt einen minimalistischen Linienplot mit Punkten (Tufte-Stil).
    Ideal für Zeitreihen mit wenigen Datenpunkten.

    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame mit den Daten für den Plot.
    x_col : str
        Name der Spalte für die X-Achse (z.B. Jahre).
    y_col : str
        Name der Spalte für die Y-Achse (numerisch).
    title : str (Standardwert="Time Series")
        Titel des Plots.

    Returns
    -------
    plot : plotnine.ggplot
        Ein ggplot-Objekt mit dem Linienplot.

    """
    # Kopie des DataFrames erstellen, um Originaldaten nicht zu verändern
    df_copy = df.copy()
    
    plot = (
        ggplot(df_copy, aes(x=x_col, y=y_col))
        
        # Linie
        + geom_line(size=TUFTE_LINE_SIZE, color=TUFTE_DARK)
        
        # Punkte
        + geom_point(size=TUFTE_POINT_SIZE_MEDIUM, color=TUFTE_DARK)
        
        # Beschriftung
        + labs(title=title, x=None, y=None)
        
        # Tufte-Theme
        + tufte_theme()
        + theme(
            axis_line=element_blank(),
            legend_position='none'
        )
    )
    
    return plot