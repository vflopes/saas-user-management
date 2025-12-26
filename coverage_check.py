import sys
import os
from coverage.control import Coverage

MinimumCoverage = float(os.getenv("MIN_COVERAGE_PERCENTAGE", 90.0))

if __name__ == "__main__":
    cov = Coverage()
    cov.load()

    null_io = open(os.devnull, "w")

    total_coverage = cov.report(
        show_missing=True, file=null_io, output_format="total"
    )

    if total_coverage < MinimumCoverage:
        print(
            f"Coverage check failed: {total_coverage:.2f}% < {MinimumCoverage:.2f}%"
        )
        sys.exit(1)

    print(
        f"Coverage check passed: {total_coverage:.2f}% >= {MinimumCoverage:.2f}%"
    )
    sys.exit(0)
