#! /usr/bin/env python3
"""
Example of box-and-whisker plot.
"""

from pathlib import Path

import dawgdad as dd


def main():
    dd.style_graph()
    series = dd.random_data()
    fig, ax = dd.plot_boxplot(series=series)
    ax.set_title(label='Box-and-whisker plot')
    ax.set_xticks(ticks=[1], labels=['series'])
    ax.set_ylabel('y')
    fig.savefig(fname=Path('boxplot.svg'))


if __name__ == '__main__':
    main()
