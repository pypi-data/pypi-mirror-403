# formula-math
I made this cause I always struggled with keeping up with formulas and remembering each one.

This is a beginner-friendly Python library for math, finance, geometry, trigonometry, statistics, physics, and original helpers.
No need to memorize formulas — just call the function with your values and get results instantly.

## Installation

pip install formula-math

## Usage

import formula_math as fm

# Math
fm.add(2,3,4,5)               # Multi-number addition
fm.sub(20,5,3)                # Multi-number subtraction
fm.multiply(2,3,5)            # Multi-number multiplication
fm.divide(100,2,5)            # Multi-number division
fm.remainder(10,3)            # Remainder
fm.sqrt(25)
fm.per(20,30,50)              # Percentages of numbers
fm.solve_expression("2 + 3 * 4")
fm.smart_calc(10,'+',5,'*',2)

# Finance
fm.si(1000,5,2)
fm.ci(1000,5,2)
fm.time_to_double(1000,6)
fm.emi(100000,10,12)

# Geometry
fm.sq_perimeter(5)
fm.sq_area(5)
fm.rect_area(4,6)
fm.rect_perimeter(4,6)
fm.cube_volume(3)
fm.cube_surface_area(3)
fm.sphere_volume(4)
fm.sphere_surface_area(4)
fm.cone_volume(3,5)
fm.cone_surface_area(3,5)
fm.heron(3,4,5)               # Heron's formula
fm.pyramid_volume(4,5,6)
fm.torus_volume(5,2)
fm.polygon_area_sides(6,3)

# Algebra
fm.solve_quadratic(1,-3,2)
fm.linear_solve_2x2(1,2,5,3,4,11)
fm.arithmetic_mean(1,2,3)
fm.geometric_mean(2,4,8)

# Trigonometry
fm.sin_deg(30)
fm.cos_deg(60)
fm.tan_deg(45)
fm.cosec_deg(30)
fm.sec_deg(60)
fm.cot_deg(45)

# Statistics & Probability
fm.mean(1,2,3)
fm.median(1,2,3,4)
fm.mode(1,2,2,3)
fm.stdev(1,2,3,4)
fm.permutations(5,2)
fm.combinations(5,2)
fm.is_even(4)
fm.is_odd(3)
fm.is_prime(7)
fm.factor_pairs(12)
fm.prime_factors(36)

# Original Helpers
fm.vector_projection((1,2),(3,4))
fm.distance_2d(0,0,3,4)
fm.distance_3d(0,0,0,1,2,2)
fm.math_trick(5)
fm.random_choice(1,2,3,4)
fm.shuffle_list([1,2,3,4])
fm.magic_formula(2,3,4)

# Physics
fm.force(10,5)
fm.weight(10)
fm.work(10,5)
fm.kinetic_energy(10,5)
fm.potential_energy(10,5)
fm.momentum(10,5)
fm.pressure(10,2)
fm.density(10,2)
fm.velocity(10,2)
fm.acceleration(10,2,4)
fm.grav_force(1,2,3)
fm.ohms_law(10,2)
fm.electric_power(10,2)
fm.coulombs_law(1,1,2)

## Available Functions

Simple Interest
fm.si(principal, rate, time)
- principal: amount of money (P)
- rate: annual interest rate in % (R)
- time: time in years (T)
Example: fm.si(1000, 5, 2)  # Returns 100.0

Square Perimeter & Area
fm.sq_perimeter(side)
fm.sq_area(side)
Example: fm.sq_area(5)  # Returns 25

Cube Volume & Surface Area
fm.cube_volume(side)
fm.cube_surface_area(side)
Example: fm.cube_volume(3)  # Returns 27

Sphere Volume & Surface Area
fm.sphere_volume(radius)
fm.sphere_surface_area(radius)
Example: fm.sphere_volume(4)  # Returns 268.08 (approx)

Cone Volume & Surface Area
fm.cone_volume(radius, height)
fm.cone_surface_area(radius, slant_height)
Example: fm.cone_volume(3, 5)  # Returns 47.12 (approx)

Rectangle Area & Perimeter
fm.rect_area(length, width)
fm.rect_perimeter(length, width)
Example: fm.rect_area(4, 6)  # Returns 24

Heron's Triangle Area
fm.heron(a, b, c)
Example: fm.heron(3,4,5)  # Returns 6.0

Percentages
fm.per(n1, n2, n3, ...)
Example: fm.per(20,30,50)  # Returns [20.0, 30.0, 50.0]

Smart Math
fm.solve_expression("2 + 3 * 4")
fm.smart_calc(10,'+',5,'*',2)

Square Root
fm.sqrt(x)
Example: fm.sqrt(9) # Resturns 3.0

Cube Root
fm.cbrt(x)
Example: fm.cbrt(8) # Resturns 2.0

## Notes
- Multi-number arithmetic is supported in add, sub, multiply, divide.
- All functions return numeric results (float or int as appropriate).
- Designed to save time in homework, projects, or quick calculations.
- Original helpers and physics functions make school & creative projects faster.

## License
This project is licensed under the MIT License.
