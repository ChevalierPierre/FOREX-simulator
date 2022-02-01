import plotly.graph_objects as go
from plotly.subplots import make_subplots
import datetime as dt
import pandas as pd


class Graph():
    __instance = None
    figure = None

    buyColor = 'rgba(210, 0, 0, 1)'
    sellColor = 'rgba(0, 0, 210, 1)'
    otherColor = 'rgba(0, 210, 0, 1)'

    @staticmethod
    def getInstance():
        if Graph.__instance == None:
            Graph()
        return Graph.__instance

    def __init__(self):
        if Graph.__instance != None:
            raise Exception("This class is a singleton!")
        Graph.__instance = self
        self.figure = make_subplots(
            rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.01)

    @staticmethod
    def render():
        self = Graph.getInstance()
        self.figure.show()
        # Reset graph when rendering.
        self.figure = make_subplots(
            rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.01)

    @staticmethod
    def setTitle(title):
        self = Graph.getInstance()
        self.figure.update_layout(
            title=go.layout.Title(text=title),
            title_font_size=16
        )
        self.figure.update_xaxes(rangeslider_visible=False)

    @staticmethod
    def addCandleSticks(x, open, high, low, close, name, plot=1):
        self = Graph.getInstance()
        self.figure.add_trace(
            go.Candlestick(
                x=x,
                open=open,
                high=high,
                low=low,
                close=close,
                name=name
            ), row=plot, col=1
        )

    @staticmethod
    def addIndicator(x, y, name, color, plot=1):
        self = Graph.getInstance()
        self.figure.add_trace(
            go.Scatter(
                x=x,
                y=y,
                name=name,
                line_color=color
            ), row=plot, col=1
        )

    @staticmethod
    def addAction(x, y, name, isBuy=None, plot=1):
        self = Graph.getInstance()

        parameters = dict(x=x,
                          y=y,
                          text=name,
                          showarrow=True,
                          align="center",
                          arrowhead=2,
                          arrowsize=1,
                          arrowwidth=2,
                          bordercolor="#c7c7c7",
                          borderwidth=2,
                          borderpad=2,
                          font=dict(
                               size=14 if isBuy != None else 10,
                               color="#ffffff"
                          ),
                          opacity=1)

        if isBuy != None:
            color = self.buyColor if isBuy else self.sellColor
        else:
            color = self.otherColor
        parameters['bgcolor'] = color
        parameters['arrowcolor'] = color

        if plot == 0:  # Plot 0 means BOTH plots!
            self.addAction(x, y, name, isBuy, plot=1)
            self.addAction(x, y, name, isBuy, plot=2)
        else:
            parameters['yref'] = 'y' + str(plot)
            self.figure.add_annotation(parameters)
