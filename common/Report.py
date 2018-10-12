#!/usr/bin/env python
#coding=utf-8

def get_summary(result):
    """ get summary from test result
    """
    summary = {
        "success": result.wasSuccessful(),
        "stat": {
            'testsRun': result.testsRun,
            'failures': len(result.failures),
            'errors': len(result.errors),
            # 'skipped': len(result.skipped),
            'expectedFailures': len(result.expectedFailures),
            'unexpectedSuccesses': len(result.unexpectedSuccesses)
        }
    }
    summary["stat"]["successes"] = summary["stat"]["testsRun"] \
        - summary["stat"]["failures"] \
        - summary["stat"]["errors"] \
        - summary["stat"]["expectedFailures"] \
        - summary["stat"]["unexpectedSuccesses"]

    if getattr(result, "records", None):
        summary["time"] = {
            'start_at': result.start_at,
            'duration': result.duration
        }
        summary["records"] = result.records
    else:
        summary["records"] = []

    return summary


# if __name__ == "__main__":