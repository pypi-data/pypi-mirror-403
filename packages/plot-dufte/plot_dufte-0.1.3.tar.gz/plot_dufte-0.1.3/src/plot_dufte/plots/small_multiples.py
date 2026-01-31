import pandas as pd
from plotnine import ggplot, aes, geom_line, facet_wrap, labs, theme, element_text
from ..config_theme import (
    tufte_theme, 
    TUFTE_DARK,
    TUFTE_LINE_SIZE
)


def small_multiples(
        df:pd.DataFrame, 
        x_col:str, 
        y_col:str, 
        facet_col:str, 
        title:str="Small Multiples", 
        ncol:int=4, 
        x_label:str=None, 
        y_label:str=None) -> ggplot:
    """
    Erstellt kleine Mehrfachplots (Small Multiples) für kategoriale Datenreihen.
    Zeigt mehrere Linienplots nebeneinander, getrennt nach der Facettenkategorie.

    Parameters
    ----------
    df : pandas.DataFrame   
        DataFrame mit den Daten für den Plot.
    x_col : str
        Name der Spalte für die X-Achse (kategorisch oder kontinuierlich).
    y_col : str
        Name der Spalte für die Y-Achse (numerisch).
    facet_col : str
        Name der Spalte für die Facettenkategorie.
    title : str (Standardwert="Small Multiples")
        Titel des Plots.
    ncol : int (Standardwert=4)
        Anzahl der Spalten für die Facettenanordnung.
    x_label : str
        Beschriftung der X-Achse.
    y_label : str
        Beschriftung der Y-Achse.

    Returns
    -------
    plot : plotnine.ggplot
        Ein ggplot-Objekt mit den kleinen Mehrfachplots.

    """

    plot = (
        ggplot(df, aes(x=x_col, y=y_col)) +
        
        # Linien definieren
        geom_line(size=TUFTE_LINE_SIZE, color=TUFTE_DARK) +
        
        # Facetten anlegen
        facet_wrap(f'~{facet_col}', ncol=ncol, scales='fixed') +
        
        # Beschriftung
        labs(title=title or "Small Multiples", x=x_label, y=y_label) +
        
        # Tufte-Theme
        tufte_theme() +
        theme(
            panel_spacing_x=0.05,
            panel_spacing_y=0.05,
            strip_text=element_text(size=10, weight="bold", ha="left"),
            axis_text_x=element_text(size=7, angle=45, hjust=1),
            axis_text_y=element_text(size=7)
        )
    )

    return plot