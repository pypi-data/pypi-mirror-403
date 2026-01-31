import pandas as pd
from plotnine import ggplot, aes, geom_line, geom_point, geom_text, labs, theme, element_blank, facet_wrap, coord_cartesian
from ..config_theme import (
    tufte_theme,
    TUFTE_LINE_SIZE,
    TUFTE_FONT, 
    SPARKLINE_LINE_COLOR, 
    SPARKLINE_ENDPOINT_COLOR,
    SPARKLINE_ENDPOINT_SIZE,
    SPARKLINE_LABEL_SIZE
)


def sparklines(df:pd.DataFrame, category_col:str, time_col:str, value_col:str, title:str="Sparklines") -> ggplot:
    """
    Erstellt Sparklines (Tufte's kompakte Zeitreihen-Visualisierung).
    Zeigt mehrere Zeitreihen übereinander mit minimalistischem Design.

    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame mit den Daten für den Plot.
    category_col : str
        Name der Spalte für die Kategorien (z.B. Aktien).
    time_col : str
        Name der Spalte für die Zeitpunkte.
    value_col : str
        Name der Spalte für die Werte (numerisch).
    title : str (Standardwert="Sparklines")
        Titel des Plots.

    Returns
    -------
    plot : plotnine.ggplot
        Ein ggplot-Objekt mit den Sparklines.

    """
    # Kopie des DataFrames erstellen, um Originaldaten nicht zu verändern
    df_copy = df.copy()
    
    # Start- und Endpunkte für jede Kategorie ermitteln
    endpoints = df_copy.groupby(category_col).agg({
        time_col: ['min', 'max'],
        value_col: ['first', 'last']
    }).reset_index()
    endpoints.columns = [category_col, 'time_min', 'time_max', 'value_start', 'value_end']
    
    # Endpunkte als separate DataFrames
    start_points = df_copy.merge(
        endpoints[[category_col, 'time_min']], 
        left_on=[category_col, time_col], 
        right_on=[category_col, 'time_min']
    )
    
    end_points = df_copy.merge(
        endpoints[[category_col, 'time_max']], 
        left_on=[category_col, time_col], 
        right_on=[category_col, 'time_max']
    )
    
    # Labels für linke Seite (Kategorie-Name)
    start_points['label_text'] = start_points[category_col].astype(str)
    
    # Labels für rechte Seite (Endwert)
    end_points['label_text'] = end_points[value_col].round(1).astype(str)
    
    # Berechne Achsenbereiche mit Padding
    y_min = df_copy[value_col].min()
    y_max = df_copy[value_col].max()
    y_range = y_max - y_min
    y_padding = y_range * 0.15
    
    x_min = df_copy[time_col].min()
    x_max = df_copy[time_col].max()
    x_range = x_max - x_min
    x_padding = x_range * 0.2  # Mehr Platz für Labels
    
    plot = (
        ggplot(df_copy, aes(x=time_col, y=value_col, group=category_col))
        
        # Linie
        + geom_line(size=TUFTE_LINE_SIZE, color=SPARKLINE_LINE_COLOR)
        
        # Startpunkt (dezent)
        + geom_point(
            data=start_points,
            size=SPARKLINE_ENDPOINT_SIZE * 0.7,
            color=SPARKLINE_LINE_COLOR
        )
        
        # Endpunkt (hervorgehoben)
        + geom_point(
            data=end_points,
            size=SPARKLINE_ENDPOINT_SIZE,
            color=SPARKLINE_ENDPOINT_COLOR
        )
        
        # Linke Labels (Kategorie-Name)
        + geom_text(
            aes(label='label_text'),
            data=start_points,
            ha='right',
            nudge_x=-x_range * 0.05,
            size=SPARKLINE_LABEL_SIZE,
            family=TUFTE_FONT,
            color=SPARKLINE_LINE_COLOR
        )
        
        # Rechte Labels (Endwert)
        + geom_text(
            aes(label='label_text'),
            data=end_points,
            ha='left',
            nudge_x=x_range * 0.05,
            size=SPARKLINE_LABEL_SIZE,
            family=TUFTE_FONT,
            color=SPARKLINE_ENDPOINT_COLOR
        )
        
        # Koordinatensystem mit definierten Grenzen
        + coord_cartesian(
            xlim=(x_min - x_padding, x_max + x_padding),
            ylim=(y_min - y_padding, y_max + y_padding)
        )
        
        # Facetten für jede Kategorie
        + facet_wrap(f'~{category_col}', ncol=1, scales='free_y')
        
        # Beschriftung
        + labs(title=title)
        
        # Tufte-Theme
        + tufte_theme()
        + theme(
            axis_text=element_blank(),
            axis_title=element_blank(),
            axis_ticks=element_blank(),
            axis_line=element_blank(),
            panel_grid=element_blank(),
            strip_text=element_blank(),
        )
    )
    
    return plot