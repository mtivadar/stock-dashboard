import sys
import argparse
import yfinance as yf

import plotly.graph_objects as go
from plotly.subplots import make_subplots

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

import pandas as pd
from datetime import datetime, timezone

def download_data(args, stock_id):
    data = yf.download(  # or pdr.get_data_yahoo(...
            # tickers list or string as well
            tickers = stock_id,

            # use "period" instead of start/end
            # valid periods: 1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max
            # (optional, default is '1mo')
            period = args.period,

            # fetch data by interval (including intraday if period < 60 days)
            # valid intervals: 1m,2m,5m,15m,30m,60m,90m,1h,1d,5d,1wk,1mo,3mo
            # (optional, default is '1d')
            interval = args.interval,

            # group by ticker (to access via data['SPY'])
            # (optional, default is 'column')
            group_by = 'ticker',

            # adjust all OHLC automatically
            # (optional, default is False)
            auto_adjust = True,

            # download pre/post regular market hours data
            # (optional, default is False)
            prepost = args.after,

            # use threads for mass downloading? (True/False/Integer)
            # (optional, default is True)
            threads = True,

            # proxy URL scheme use use when downloading?
            # (optional, default is None)
            proxy = None

        )

    info = yf.Ticker(stock_id)
    #last_quote = (info.history().tail(1)['Close'].iloc[0])
    

    #print(last_quote)

    #print(info.major_holders)
    #print(info.info)
    
    #yf.get_price()
    #sys.exit()
    #print(data.dtypes)
    #print(data.values[1])
    #print(len(data.values))
    #print(data['Open'])
    #print(data.iloc[:, [0]])
    #print(data.index.values)

    #print('----')
    return data

def gen_figure(stock_id, data):
    lt = pd.to_datetime(data.index.values)
    last_quote = (data.tail(1)['Close'].iloc[0])

    from dateutil import tz
    lt = [x.replace(tzinfo=timezone.utc).astimezone(tz.tzlocal()) for x in lt]

    labels = [x.strftime("%H:%M") for x in lt]

    fig_subplot = make_subplots(rows=2, cols=1, 
                        shared_xaxes=True,
                        vertical_spacing=0.02,
                        row_width=[0.3, 0.7])


    bar_colors = []
    for i, value_open in enumerate(data['Open']):
        value_close = data['Close'][i]
        if value_close >= value_open:
            color = 'green'
        else:
            color = 'red'

        bar_colors += [color]

    #print(data['Open'][0])
    #print(data['Close'][0])
    #sys.exit()
    fig_subplot.add_trace(go.Candlestick(x=labels,
                    open=data['Open'],
                    high=data['High'],
                    low=data['Low'],
                    close=data['Close'], name='Candle'), row=1, col=1)

    fig_subplot.add_trace(go.Bar(x=labels,
                    y=data['Volume'], name='Volume', marker_color=bar_colors ), row=2, col=1)
    


    #fig_subplot.update_xaxes(row=1, col=1, rangeslider_thickness=0.05)
    #fig_subplot.update_layout(width=900, height=900)

    fig_subplot.update_layout(height=500, 
                      title_text='<b>{}</b> - ${:,.2f}'.format(stock_id, last_quote), xaxis_rangeslider_visible=False)

    #fig_subplot.show()
    #fig_subplot.show()    
    #fig_subplot.write_html('figggg.html')
    #sys.exit()    

    return fig_subplot

def reload_figures(args):
    figures = []
    for stock_id in args.stocks:
        data = download_data(args, stock_id)
        fig = gen_figure(stock_id, data)
        figures += [fig]

    return figures
    
stock_ids = ''

def cmd_line():
    parser = argparse.ArgumentParser(description='Stock dashboard')
    parser.add_argument('stocks', metavar='STOCK', type=str, nargs='+',
                        help='stock indicatives')

    parser.add_argument('--period', '-p', dest='period',
                        choices=['1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max'], default='1d',
                        help='date period')

    parser.add_argument('--interval', '-i', dest='interval',
                        choices=['1m', '2m', '5m', '15m', '30m', '60m', '90m', '1h', '1d', '5d', '1wk', '1mo', '3mo'], default='5m',
                        help='fetch interval')

    parser.add_argument('--after', dest='after', action='store_true',
                        default=False,
                        help='enable after/before hours')

    args = parser.parse_args()

    return args

if __name__ == '__main__':
    args = cmd_line()

    
    figures = reload_figures(args)
    
    app = dash.Dash()
    app.layout = html.Div([
        html.Div(id='live-update'),#  [dcc.Graph(figure=fig) for fig in figures]),
        
        dcc.Interval(         
            id='interval-component',
            interval=1 * 60 * 1*1000, # in milliseconds
            n_intervals=0
        )
    ])

    @app.callback(Output('live-update', 'children'),
              [Input('interval-component', 'n_intervals')])
    def update_figures(n):
        figures = reload_figures(args)
        return [dcc.Graph(figure=fig) for fig in figures]

    app.run_server(debug=True, use_reloader=False)  # Turn off reloader if inside Jupyter 
    