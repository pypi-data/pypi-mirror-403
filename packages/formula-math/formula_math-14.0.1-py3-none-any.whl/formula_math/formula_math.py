# formula_math.py
"""
Formula Math Library - Full Starter Version + Upgrades
Usage:
import formula_math as fm
fm.si(1000, 5, 1)
fm.ci(1000, 5, 2)
fm.sq_area(5)
fm.cube_volume(3)
"""

import math
import random
from collections import Counter

# ------------------ sqr and cube roots ------------------

def sqrt(x): return math.sqrt(x)
def cbrt(x): return x**(1/3)

# ------------------ Finance ------------------
def si(x, y, z):
    """Simple Interest: x=Principal, y=Rate%, z=Time(years)"""
    return (x*y*z)/100

def ci(x, y, z):
    """Compound Interest: x=Principal, y=Rate%, z=Time(years)"""
    return x*((1 + y/100)**z) - x

# ------------------ 2D Geometry ------------------
def sq_perimeter(x): return 4*x
def sq_area(x): return x**2

def rect_perimeter(x, y): return 2*(x + y)
def rect_area(x, y): return x*y

def circle_area(r): return math.pi*r**2
def circle_circumference(r): return 2*math.pi*r

def tri_area_base_height(b, h): return 0.5*b*h
def tri_area_sides(a, b, c):
    s = (a+b+c)/2
    return math.sqrt(s*(s-a)*(s-b)*(s-c))
def tri_perimeter(a, b, c): return a+b+c

# ------------------ 3D Geometry ------------------
def cube_volume(x): return x**3
def cube_surface_area(x): return 6*x**2

def cuboid_volume(l, b, h): return l*b*h
def cuboid_surface_area(l, b, h): return 2*(l*b + b*h + l*h)

def sphere_volume(r): return (4/3)*math.pi*r**3
def sphere_surface_area(r): return 4*math.pi*r**2

def cylinder_volume(r, h): return math.pi*r**2*h
def cylinder_surface_area(r, h): return 2*math.pi*r*(r+h)

def cone_volume(r, h): return (1/3)*math.pi*r**2*h
def cone_surface_area(r, l): return math.pi*r*(r+l)  # l = slant height

def hemisphere_volume(r): return (2/3)*math.pi*r**3
def hemisphere_surface_area(r): return 3*math.pi*r**2  # including base

# ------------------ Algebra ------------------
def quad_roots(a, b, c):
    d = b**2 - 4*a*c
    if d < 0: return "Complex roots"
    return ((-b + math.sqrt(d))/(2*a), (-b - math.sqrt(d))/(2*a))

def arithmetic_mean(*args): return sum(args)/len(args)

def geometric_mean(*args):
    product = 1
    for i in args: product *= i
    return product ** (1/len(args))

# ------------------ Trigonometry (degrees) ------------------
def sin_deg(x): return math.sin(math.radians(x))
def cos_deg(x): return math.cos(math.radians(x))
def tan_deg(x): return math.tan(math.radians(x))
def cosec_deg(x): return 1/math.sin(math.radians(x))
def sec_deg(x): return 1/math.cos(math.radians(x))
def cot_deg(x): return 1/math.tan(math.radians(x))

# ------------------ Physics ------------------
def speed(d, t): return d/t
def distance(s, t): return s*t
def time(d, s): return d/s
def force(m, a): return m*a
def weight(m, g=9.8): return m*g
def kinetic_energy(m, v): return 0.5*m*v**2
def potential_energy(m, h, g=9.8): return m*g*h
def work(f, d): return f*d
def pressure(f, a): return f/a
def momentum(m, v): return m*v
def velocity(d, t): return d/t
def acceleration(v, u, t): return (v - u)/t
def power(w, t): return w/t
def density(m, v): return m/v
def frequency(t): return 1/t
def wavelength(v, f): return v/f
def wave_speed(f, l): return f*l
def grav_force(m1, m2, r, G=6.67430e-11): return G*m1*m2/(r**2)
def ohms_law(v, r): return v/r
def electric_power(v, i): return v*i
def coulombs_law(q1, q2, r, k=8.9875517923e9): return k*q1*q2/r**2

# ------------------ Misc Math ------------------
def factorial(x): return math.factorial(x)

def fibonacci(n):
    fib = [0,1]
    for i in range(2,n): fib.append(fib[-1]+fib[-2])
    return fib[:n]

def nCr(n, r):
    return math.factorial(n)//(math.factorial(r)*math.factorial(n-r))

def nPr(n, r):
    return math.factorial(n)//math.factorial(n-r)

# ------------------ Multi-number Arithmetic ------------------
def add(*args): return sum(args)

def sub(*args):
    if not args: return 0
    result = args[0]
    for x in args[1:]: result -= x
    return result

def mul(*args):
    result = 1
    for x in args: result *= x
    return result

def div(*args):
    if not args: return None
    result = args[0]
    for x in args[1:]: result /= x
    return result

# ------------------ Percentage ------------------
def per(*args):
    total = sum(args)
    return [round((x/total)*100, 2) for x in args]

# ------------------ Smart Calculation Helpers ------------------
def solve_expression(expr):
    allowed_chars = "0123456789+-*/(). "
    if any(c not in allowed_chars for c in expr):
        raise ValueError("Invalid characters in expression")
    return eval(expr)

def smart_calc(*args):
    expr = "".join(str(x) for x in args)
    return solve_expression(expr)

# ------------------ Statistics / Helpers ------------------
def avg(numbers): return sum(numbers)/len(numbers)
def sum_list(numbers): return sum(numbers)
def list_product(numbers):
    result = 1
    for x in numbers: result *= x
    return result

def max_value(numbers): return max(numbers)
def min_value(numbers): return min(numbers)
def range_sum(start, end): return sum(range(start, end+1))
def median(numbers):
    n = sorted(numbers)
    l = len(n)
    if l%2==1: return n[l//2]
    else: return (n[l//2-1]+n[l//2])/2

def mean(numbers): return sum(numbers)/len(numbers)
def mode(numbers):
    c = Counter(numbers)
    most = c.most_common(1)
    return most[0][0]

def square_list(*args): return [x**2 for x in args]

# ------------------ Logical Helpers ------------------
def is_even(n): return n%2==0
def is_odd(n): return n%2!=0
def is_prime(n):
    if n<2: return False
    for i in range(2, int(n**0.5)+1):
        if n%i==0: return False
    return True

def permutation(n,r): return math.factorial(n)//math.factorial(n-r)
def combination(n,r): return math.factorial(n)//(math.factorial(r)*math.factorial(n-r))
def lcm(a,b): return abs(a*b)//math.gcd(a,b)
def gcd(a,b): return math.gcd(a,b)

def is_palindrome_number(n): return str(n)==str(n)[::-1]

def is_armstrong_number(n):
    digits = [int(d) for d in str(n)]
    return n == sum([d**len(digits) for d in digits])

def factor_pairs(n): return [(i, n//i) for i in range(1,n+1) if n%i==0]

def prime_factors(n):
    i=2
    factors=[]
    while i*i <= n:
        if n%i==0:
            factors.append(i)
            n//=i
        else:
            i+=1
    if n>1: factors.append(n)
    return factors

# ------------------ Fun / Random ------------------
def magic_formula(a,b,c): return (a**2 + b**2)/math.sqrt(c)
def random_choice(*args): return random.choice(args)
def shuffle_list(numbers):
    l = numbers.copy()
    random.shuffle(l)
    return l

# ------------------ Backward-compatible aliases ------------------
heron = tri_area_sides
triangle_area_heron = heron
cube_vol = cube_volume
circle_circ = circle_circumference
square_area = sq_area
square_perimeter = sq_perimeter
rectangle_area = rect_area
rectangle_perimeter = rect_perimeter