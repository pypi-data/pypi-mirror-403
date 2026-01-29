#! /usr/bin/env python3
"""
Test def probability_plot() of graphs.py.

time -f '%e' ./probability_plot_test.py
./probability_plot_test.py
"""

import dawgdad as dd

output_url = 'probability_plot_test.html'
header_title = 'probability_plot_test'
header_id = 'probability-plot-test'


def main():
    original_stdout = dd.html_begin(
        output_url=output_url,
        header_title=header_title,
        header_id=header_id
    )
    data = dd.random_data()
    fig, ax = dd.probability_plot(data=data)
    fig.savefig(
        fname='probability_plot_test.svg',
        format='svg'
    )
    dd.html_figure(file_name='probability_plot_test.svg')
    dd.html_end(
        original_stdout=original_stdout,
        output_url=output_url
    )


if __name__ == '__main__':
    main()
