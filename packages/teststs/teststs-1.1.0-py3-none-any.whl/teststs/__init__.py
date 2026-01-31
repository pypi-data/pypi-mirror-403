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
    except Exception as error: # Error Failed
        return False, args, expected, None, error
    
    if not eq(result, expected): # Not Match Failed
        return False, args, expected, result, None
    
    return True, None, None, None, None # OK!


def test(
    tests: tuple[tuple], 
    func: callable, 
    detail: bool = False, 
    log: bool = True,
    ok_log: bool = False,
    failed_stop: bool = True, 
    eq: callable = 
    lambda a, b: a == b
):
    """
    Run multiple test cases and print results.

    Parameters:
        tests (list of tuples): List of test cases. Each case is (*args, expected).
        func (callable): The function to test.
        detail (bool): If True, prints detailed info for failed tests.
        log (bool): If True, prints test results; if False, suppresses all output. Default is True.
        ok_log (bool): If True, prints success test. Defualt is False.
        failed_stop (bool): If True, stops after the first failed test.
        eq (callable): Comparison function for results. Default is equality (a == b).

    Returns:
        list: List of failed cases. Each element is a tuple (args, expected, result, error).
              Returns an empty list if all tests pass.
    """

    faileds = []

    for case in tests:
        ok, args, expected, result, error = _run_test(case, func, eq) # Single Test

        if ok:
            if ok_log:
                print("Test success:", args, result)
            continue

        # Failed
        faileds.append((args, expected, result, error))

        if not log: # No print
            if failed_stop: # and failed stop
                return faileds
            continue # No failed stop
        
        if not detail: 
            print("Test failed:", args, result)
        else: # Detail Log
            print("Test failed")
            print("input:", args)
            print("expected:", expected)
            print("actual:", result)
            if error:
                print("error:", error)
        
        if failed_stop:
            return faileds
    
    if not faileds:
        print("OK!")
    
    return faileds