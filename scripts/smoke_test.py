"""Solves Hock and Schittkowski problem 71 with the installed cyipopt.

The script raises an error when Ipopt does not report success or when the
objective differs from the known optimum. Run it with the interpreter of a
virtual environment that has the wheel installed.
"""

import numpy as np

import cyipopt

# The optimal objective value of Hock and Schittkowski problem 71.
EXPECTED_OBJECTIVE_VALUE = 17.0140173


class HockSchittkowski71:
    """Callbacks that describe Hock and Schittkowski problem 71."""

    def objective(self, variables):
        """Returns the objective value at `variables`."""
        return variables[0] * variables[3] * np.sum(variables[0:3]) + variables[2]

    def gradient(self, variables):
        """Returns the gradient of the objective at `variables`."""
        return np.array(
            [
                variables[0] * variables[3] + variables[3] * np.sum(variables[0:3]),
                variables[0] * variables[3],
                variables[0] * variables[3] + 1.0,
                variables[0] * np.sum(variables[0:3]),
            ]
        )

    def constraints(self, variables):
        """Returns the two constraint values at `variables`."""
        return np.array((np.prod(variables), np.dot(variables, variables)))

    def jacobian(self, variables):
        """Returns the dense Jacobian of the constraints, row by row."""
        return np.concatenate((np.prod(variables) / variables, 2 * variables))


def main() -> None:
    """Solves the problem and compares the objective with the known optimum."""
    problem = cyipopt.Problem(
        n=4,
        m=2,
        problem_obj=HockSchittkowski71(),
        lb=[1.0, 1.0, 1.0, 1.0],
        ub=[5.0, 5.0, 5.0, 5.0],
        cl=[25.0, 40.0],
        cu=[2.0e19, 40.0],
    )
    # The Hessian is approximated, so the test does not need a Hessian callback.
    problem.add_option("hessian_approximation", "limited-memory")
    problem.add_option("print_level", 0)
    problem.add_option("sb", "yes")

    _, information = problem.solve(np.array([1.0, 5.0, 5.0, 1.0]))
    if information["status"] != 0:
        raise RuntimeError(
            f"Ipopt did not solve the problem: {information['status_msg']}."
        )

    objective_value = float(information["obj_val"])
    if not np.isclose(objective_value, EXPECTED_OBJECTIVE_VALUE, rtol=0, atol=1e-4):
        raise RuntimeError(
            f"Objective {objective_value} differs from {EXPECTED_OBJECTIVE_VALUE}."
        )

    print(
        f"cyipopt {cyipopt.__version__} solved problem 71 "
        f"with objective {objective_value:.7f}."
    )


if __name__ == "__main__":
    main()
