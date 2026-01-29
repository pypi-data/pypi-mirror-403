def check(X_train, X_test=None, *, y_train=None):
    """
    Run basic ML validation checks.

    Parameters
    ----------
    X_train : array-like
    X_test : array-like, optional
    The * means: Everything after this must be passed by keyword
    y_train : array-like, optional; must be passed with keyword

    Returns
    -------
    dict
        Validation report
    """

    report = {
        "status": "ok",
        "warnings": [],
        "errors": []
    }

    if y_train is not None and len(X_train) != len(y_train):
        report["errors"].append("X_train and y_train length mismatch")

    return report