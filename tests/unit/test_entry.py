from unpbs.entry import logic


def test_logic():
    file_content = '\n'.join([
        'def bar():',
        '    return 0',
        'def foo():',
        '    bar()',
    ])
    assert logic(file_content) == '\n'.join([
        'bar',
        '  fan_in: 1',
        '  fan_out: 0',
        'foo',
        '  fan_in: 0',
        '  fan_out: 1',
    ])
