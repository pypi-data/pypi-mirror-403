def _run_test(case, func, eq):
    """
    Run a single test case (not recommended for direct use).

    Note:
        This is a minimal implementation and primarily intended for internal use
        by the `teststs` function. Direct usage is not recommended.

    Parameters:
        case (tuple): A tuple containing function arguments and the expected value (*args, expected).
        func (callable): The function to test.
        eq (callable): Comparison function for the result. Default is equality (a == b).

    Returns:
        tuple: (ok, args, expected, result, error)
            ok (bool): Whether the test passed.
            args (tuple): Input arguments used for the function.
            expected: The expected result.
            result: Actual function return value (None if an exception occurred).
            error: Exception object if an error occurred, else None.
    """
    *args, expected = case
    try:
        result = func(*args)
    except Exception as error:
        return False, args, expected, None, error
    if not eq(result, expected):
        return False, args, expected, result, None
    return True, None, None, None, None


def teststs(tests, func, detail=False, failed_stop=True, eq=lambda a, b: a == b):
    """
    Run multiple test cases and print results.

    Parameters:
        tests (list of tuples): List of test cases. Each case is (*args, expected).
        func (callable): The function to test.
        detail (bool): If True, prints detailed info for failed tests.
        failed_stop (bool): If True, stops after the first failed test.
        eq (callable): Comparison function for results. Default is equality (a == b).

    Returns:
        list: List of failed cases. Each element is a tuple (args, expected, result, error).
              Returns an empty list if all tests pass.
    """
    faileds = []
    for case in tests:
        ok, args, expected, result, error = _run_test(case, func, eq)
        if not ok:
            faileds.append((args, expected, result, error))
            if detail:
                print("Test failed")
                print("input:", args)
                print("expected:", expected)
                print("actual:", result)
                if error:
                    print("error:", error)
            else:
                print("Test failed:", args, result)
            if failed_stop:
                return faileds
    if not faileds:
        print("OK!")
    return faileds
