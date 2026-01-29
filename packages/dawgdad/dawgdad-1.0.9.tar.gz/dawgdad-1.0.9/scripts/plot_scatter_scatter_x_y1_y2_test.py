#! /usr/bin/env python3
'''
Test def plot_scatter_scatter_x_y1_y2() of graphs.py

time -f '%e' ./plot_scatter_scatter_x_y1_y2_test.py
./plot_scatter_scatter_x_y1_y2_test.py
'''

import dawgdad as dd

output_url = 'plot_scatter_scatter_x_y1_y2_test.html'
header_title = 'plot_scatter_scatter_x_y1_y2_test'
header_id = 'plot-scatter-scatter-x-y1-y2-test'


def main():
    original_stdout = dd.html_begin(
        output_url=output_url,
        header_title=header_title,
        header_id=header_id
    )
    series_x = dd.datetime_data()
    series_y1 = dd.random_data()
    series_y2 = dd.random_data()
    fig, ax = dd.plot_scatter_scatter_x_y1_y2(
        X=series_x,
        y1=series_y1,
        y2=series_y2
    )
    fig.savefig(
        fname='plot_scatter_scatter_x_y1_y2_datex_test.svg',
        format='svg'
    )
    dd.html_figure(file_name='plot_scatter_scatter_x_y1_y2_datex_test.svg')
    series_x = dd.random_data(distribution='uniform')
    fig, ax = dd.plot_scatter_scatter_x_y1_y2(
        X=series_x,
        y1=series_y1,
        y2=series_y2,
        figsize=(8, 5),
        marker1='o',
        marker2='+',
        markersize1=8,
        markersize2=12,
        colour1='#cc3311',
        colour2='#ee3377',
        labellegendy1='y1',
        labellegendy2='y2'
    )
    ax.legend(frameon=False)
    fig.savefig(
        fname='plot_scatter_scatter_x_y1_y2_test.svg',
        format='svg'
    )
    dd.html_figure(file_name='plot_scatter_scatter_x_y1_y2_test.svg')
    dd.html_end(
        original_stdout=original_stdout,
        output_url=output_url
    )


if __name__ == '__main__':
    main()
