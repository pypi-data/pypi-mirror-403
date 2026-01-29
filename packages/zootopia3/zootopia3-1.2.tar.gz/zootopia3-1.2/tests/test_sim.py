from zootopia3 import simulate_shapes

def test_simulate_shapes():
    value = simulate_shapes(
        2,
        'triangle',
        128,
        128,
        shades = False,
    )
    assert len(value) == 5
    assert len(value[0]) == (2 * 6)
    assert value[2].shape[1:] == (128, 128, 3)

def test_simulate_shapes_v2():
    value = simulate_shapes(
        4,
        'circle',
        384,
        384,
        shades = True,
    )
    assert isinstance(value, tuple)
    assert len(value) == 5
    assert len(value[0]) == (4 * 8)
    assert value[2].shape[1:] == (384, 384, 3)

if __name__ == '__main__':
    test_simulate_shapes()
    test_simulate_shapes_v2()