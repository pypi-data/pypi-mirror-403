#! /usr/bin/env python3
'''
Test help for dawgdad.

time -f '%e' ./dawgdad.help_test.py
./dawgdad.help_test.py

Typical input:
dd.stats.random_data
'''

import dawgdad as dd

output_url = 'dawgdad.help_test.html'
header_title = 'dawgdad.help'
header_id = 'dawgdad.help'


def main():
    input_value = eval(input(r'module.file.function name? > '))
    original_stdout = dd.html_begin(
        output_url=output_url,
        header_title=header_title,
        header_id=header_id
    )
    print('<pre style="white-space: pre-wrap;">')
    help(input_value)
    print('</pre>')
    dd.html_end(
        original_stdout=original_stdout,
        output_url=output_url
    )


if __name__ == '__main__':
    main()
