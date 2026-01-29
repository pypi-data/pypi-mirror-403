from mlcheck import check

## Function to test
def test_x_y_length_mismatch():
    X = [1, 2, 3]
    y = [1, 2]
    report = check(X, y_train=y)
    assert "length mismatch" in report["errors"][0]
    