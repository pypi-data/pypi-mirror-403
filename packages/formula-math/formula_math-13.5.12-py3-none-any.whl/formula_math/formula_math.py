# formula_math.py
"""
Formula Math Library - Full Starter Version
Usage:
import formula_math as fm
fm.si(1000, 5, 1)
fm.ci(1000, 5, 2)
fm.sq_area(5)
fm.cube_volume(3)
"""

import math

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
