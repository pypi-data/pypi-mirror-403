#! /usr/bin/env python3
'''
Test def plot_line_y() of graphs.py

time -f '%e' ./plot_line_y_test.py
./plot_line_y_test.py
'''

import dawgdad as dd

output_url = 'plot_line_y_test.html'
header_title = 'plot_line_y_test'
header_id = 'plot-scatter-x-y-test'


def main():
    original_stdout = dd.html_begin(
        output_url=output_url,
        header_title=header_title,
        header_id=header_id
    )
    # Example 1
    series_y = dd.random_data()
    fig, ax = dd.plot_line_y(y=series_y)
    fig.savefig(
        fname='plot_line_y_test_1.svg',
        format='svg'
    )
    dd.html_figure(file_name='plot_line_y_test_1.svg')
    # Example 2
    fig, ax = dd.plot_line_y(
        y=series_y,
        figsize=(8, 4.5),
        marker='o',
        markersize=4,
        linestyle=':',
        colour='#ee7733'
    )
    fig.savefig(
        fname='plot_line_y_test_2.svg',
        format='svg'
    )
    dd.html_figure(file_name='plot_line_y_test_2.svg')
    dd.html_end(
        original_stdout=original_stdout,
        output_url=output_url
    )


if __name__ == '__main__':
    main()
