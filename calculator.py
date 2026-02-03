class Calculator:
    """A simple calculator providing basic arithmetic operations."""

    def add(self, a, b):
        """Return the sum of a and b."""
        return a + b

    def subtract(self, a, b):
        """Return the difference of a and b (a - b)."""
        return a - b

    def apowerb(self, a, b):
        """Return a raised to the power of b."""
        return a**b

    def multiply(self, a, b):
        """Return the product of a and b."""
        return a * b

    def divide(self, a, b):
        """Return the quotient of a and b (a / b).

        Raises:
            ValueError: If b is zero.
        """
        if b == 0:
            raise ValueError("division by zero")
        return a / b
