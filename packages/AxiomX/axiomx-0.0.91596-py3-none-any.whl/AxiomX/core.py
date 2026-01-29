# AxiomX 0.0.91596 - the Catalan Edition
# For more info, read README.md

from time import sleep as delay

print("AxiomX loading...")
delay(3)
print("AxiomX is ready to use!")

version = '0.0.91596'

class Constants:
    pi = 3.141592653589793
    e = 2.718281828459045
    tau = 2 * pi
    lemniscate = 2.622057554292119
    euler_mascheroni = 0.577215664910533
    gelfond = e**pi
    sqrt_2 = 2**0.5
    sqrt_3 = 3**0.5
    sqrt_5 = 5**0.5
    golden_ratio = (1 + sqrt_5) / 2
    silver_ratio = 1 + sqrt_2
    ramanujan = gelfond**(163**0.5)
    gauss = lemniscate / pi
    gelfond_schneider = 2**sqrt_2
    infinity = float("inf")
    
class Arithmetic:
    def __parse_linear(self, expr):
        a = 0  # coefficient of x
        b = 0  # constant term

        i = 0
        sign = 1

        while i < len(expr):
            if expr[i] == '+':
                sign = 1
                i += 1
            elif expr[i] == '-':
                sign = -1
                i += 1

            num = ''
            while i < len(expr) and expr[i].isdigit():
                num += expr[i]
                i += 1

            if i < len(expr) and not (expr[i] in [str(i) for i in range(10)]):
                coef = int(num) if num else 1
                a += sign * coef
                i += 1
            else:
                if num:
                    b += sign * int(num)

        return a, b

    def solve_equation(self, eq):
        eq = eq.replace(" ", "")
        left, right = eq.split("=")

        a1, b1 = self.__parse_linear(left)
        a2, b2 = self.__parse_linear(right)

        a = a1 - a2
        b = b1 - b2

        if a == 0:
            raise ValueError("No unique solution")

        return -b / a
        
    def abs(self, x):
        if x >= 0:
            return x
        return -x
        
    def reciprocal(self, x):
        return 1 / x
        
class Calculus:
    def integrate(self, function, lowlim, uplim, n=10000):
        h = (uplim - lowlim) / n
        s = function(lowlim) + function(uplim)

        for i in range(1, n):
            x = lowlim + i * h
            if i % 2 == 0:
                s += 2 * function(x)
            else:
                s += 4 * function(x)

        return s * h / 3
        
    def summation(self, lowlim, uplim, function):
        sum = 0
        if lowlim == -Constants().infinity:
            lowlim = -10**7
        elif uplim == Constants().infinity:
            uplim = 10**7
        for i in range(lowlim, uplim+1):
            sum += function(i)
        return(sum)
        
class Functions:
    def sqrt(self, a, x0=None, tol=1e-30, max_iter=20):
        if a < 0:
            raise ValueError("a must be non-negative")

        if a == 0:
            return 0.0

        # Initial guess
        x = a if x0 is None else x0

        for _ in range(max_iter):
            x2 = x * x
            x_new = x * (x2 + 3*a) / (3*x2 + a)

            if abs(x_new - x) < tol * x_new:
                return x_new

            x = x_new

        return x
        
    def cbrt(self, N, tolerance=1e-10, max_iterations=1000):
        x = N / 3.0 if N != 0 else 0.0
        for i in range(max_iterations):
            x_next = x - (x**3 - N) / (3 * x**2)
            if abs(x_next - x) < tolerance:
                return x_next
            x = x_next 
        return x
        
    def gamma(self, x):
        # Lanczos approximation constants
        p = [
            0.99999999999980993,
            676.5203681218851,
            -1259.1392167224028,
            771.32342877765313,
            -176.61502916214059,
            12.507343278686905,
            -0.13857109526572012,
            9.9843695780195716e-6,
            1.5056327351493116e-7
        ]

        if x < 0.5:
            # Reflection formula
            return Constants().pi / (Trig.sin(Constants().pi * x) * gamma(1 - x))

        x -= 1
        t = p[0]
        for i in range(1, len(p)):
            t += p[i] / (x + i)

        g = 7
        return (2 * Constants().pi)**0.5 * (x + g + 0.5)**(x + 0.5) * (Constants().e**(-(x + g + 0.5))) * t
        
    def factorial(self, x):
        if (x // 1 == x):
            f = 1
            while x > 0:
                f *= x
                x -= 1
            return f
        else:
            return self.gamma(x+1)
            
    def agm(self, a, b):
        a1 = 0; b1 = 0
        for i in range(10000):
            a1 = (a+b) / 2
            b1 = self.sqrt(a*b)
            a = a1
            b = b1
            if a1 == b1:
                break
        return a1

    def zeta(self, n):
        zetval = 0
        if n <= 1:
            raise ValueError("zeta(n) diverges for n <= 1")
        for _ in range(1, 100001):
            zetval += (1 / _**n)
        return zetval
        
    def beta(self, n):
        if n == 0:
            return 0.5
        total = 0.0
        for i in range(100000):
            total += ((-1)**i) / ((2*i + 1)**n)
        return total

class Exponential:    
    def exp(self, n):
        return Constants().e**n
        
    def ln(self, x):
        if x <= 0:
            raise ValueError("ln(x) is undefined for x <= 0")
        k = 0
        while x >= 2.0:
            x *= 0.5
            k += 1
        while x < 1.0:
            x *= 2.0
            k -= 1
        y = (x - 1) / (x + 1)
        y2 = y * y
        s = 0.0
        term = y
        n = 1
        while abs(term) > 1e-17:
            s += term / n
            term *= y2
            n += 2
        return 2*s + k * (0.693147180559945309417232121458176568) # ln 2
        
    def log10(self, x):
        return self.ln(x) / self.ln(10)
        
    def log2(self, x):
        return self.log10(x) / self.log10(2)
        
    def log(self, arg, base):
        return self.log2(arg) / self.log2(base)

class Trigonometry:
    def radians(self, deg):
        return (pi/180)*deg
        
    def degrees(self, rad):
        return (180/pi)*rad
        
    def sin(self, x, terms=20):
        tau = Constants().tau
        quarter = ((x // tau) + 1) % 4
        if x == pi:
            return 0.0
        x = x % tau
        # Input validation
        if not isinstance(x, (int, float)):
            raise TypeError("x must be a number (int or float).")
        if not isinstance(terms, int) or terms <= 0:
            raise ValueError("terms must be a positive integer.")
        sine_value = 0.0
        for n in range(terms):
            term = ((-1)**n) * (x**(2*n + 1)) / Functions().factorial(2*n + 1)
            sine_value += term
        return sine_value
        if quarter == 1:
            return sine_value
        elif quarter == 2:
            return sqrt(1 - (sine_value**2))
        elif quarter == 3:
            return -sine_value
        elif quarter == 0:
            return -sqrt(1 - (sine_value**2))
            
    def cos(self, x):
        return self.sin((pi/2)-x)
        
    def tan(self, x):
        return self.sin(x) / self.cos(x)

    def cot(self, x):
        return 1 / self.tan(x)

    def sec(self, x):
        return 1 / self.cos(x)
        
    def cosec(self, x):
        return 1 / self.sin(x)

    def arcsin(self, x, iterations=10):
        if abs(x) > 1:
            raise ValueError("x must be in [-1, 1]")
        y = x
        for _ in range(iterations):
            y -= (self.sin(y) - x) / self.cos(y)
        return y
        
    def arccos(self, x):
        return (Constants().pi / 2) - self.arcsin(x)
        
    def arctan(self, x):
        return self.arcsin(x / Functions.sqrt(1+ x**2))
        
    def arccot(self, x):
        return (Constants().pi/2) - arctan(x)

    def arcsec(self,x):
        return self.arccos(1/x)
        
    def arccosec(self, x):
        return self.arcsin(1/x)

class Hyperbolic:
    
    def __init__(self):
        self.ex = Exponential()
    
    def sinh(self, x):
        return (self.ex.exp(x) - self.ex.exp(-x))/2
        
    def cosh(self, x):
        return (self.ex.exp(x) + self.ex.exp(-x))/2
        
    def tanh(self, x):
        return self.sinh(x) / self.cosh(x)
        
    def coth(self, x):
        return self.cosh(x) / self.sinh(x)
        
    def sech(self, x):
        return 1 / self.cosh(x)
        
    def cosech(self, x):
        return 1 / self.sinh(x)
        
    def arcsinh(self, x):
        return self.ex.ln(x + sqrt(x**2 + 1))
        
    def arccosh(self, x):
        return abs(self.arcsinh(Functions().sqrt(x**2 - 1)))
        
    def arccoth(self, x):
        return 0.5 * self.ex.ln((x+1)/(x-1))
        
    def arctanh(self, x):
        return self.arccoth(1/x)
        
    def arcsech(self, x):
        return self.arccosh(1/x)
        
    def arccosech(x):
        return arcsinh(1/x)