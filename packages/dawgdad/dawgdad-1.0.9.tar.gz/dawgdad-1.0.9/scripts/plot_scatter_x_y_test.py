#! /usr/bin/env python3
'''
Test def plot_scatter_x_y() of graphs.py

time -f '%e' ./plot_scatter_x_y_test.py
./plot_scatter_x_y_test.py
'''

import dawgdad as dd

output_url = 'plot_scatter_x_y_test.html'
header_title = 'plot_scatter_x_y_test'
header_id = 'plot-scatter-x-y-test'


def main():
    original_stdout = dd.html_begin(
        output_url=output_url,
        header_title=header_title,
        header_id=header_id
    )
    # Example 1
    series_x = dd.datetime_data()
    series_y = dd.random_data()
    fig, ax = dd.plot_scatter_x_y(
        X=series_x,
        y=series_y
    )
    fig.savefig(
        fname='plot_scatter_x_y_datex_test.svg',
        format='svg'
    )
    dd.html_figure(file_name='plot_scatter_x_y_datex_test.svg')
    # Example 2
    series_x = dd.random_data(distribution='randint').sort_values()
    fig, ax = dd.plot_scatter_x_y(
        X=series_x,
        y=series_y,
        figsize=(8, 4.5),
        marker='o',
        markersize=8,
        colour='#cc3311'
    )
    fig.savefig(
        fname='plot_scatter_x_y_intx_test.svg',
        format='svg'
    )
    dd.html_figure(file_name='plot_scatter_x_y_intx_test.svg')
    # Example 3
    series_x = dd.random_data(distribution='uniform').sort_values()
    fig, ax = dd.plot_scatter_x_y(
        X=series_x,
        y=series_y
    )
    fig.savefig(
        fname='plot_scatter_x_y_uniformx_test.svg',
        format='svg'
    )
    dd.html_figure(file_name='plot_scatter_x_y_uniformx_test.svg')
    # Example 4
    series_x = dd.random_data().sort_values()
    fig, ax = dd.plot_scatter_x_y(
        X=series_x,
        y=series_y
    )
    fig.savefig(
        fname='plot_scatter_x_y_normx_test.svg',
        format='svg'
    )
    dd.html_figure(file_name='plot_scatter_x_y_normx_test.svg')
    dd.html_end(
        original_stdout=original_stdout,
        output_url=output_url
    )


if __name__ == '__main__':
    main()
