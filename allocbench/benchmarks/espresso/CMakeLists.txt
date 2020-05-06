cmake_minimum_required(VERSION 3.0)
project(espresso C)
set(CMAKE_CXX_STANDARD 17)

set(CMAKE_BUILD_TYPE "Release")

set(espresso_sources
    cofactor.c cols.c compl.c contain.c cubestr.c cvrin.c cvrm.c cvrmisc.c cvrout.c
    dominate.c equiv.c espresso.c essen.c exact.c expand.c gasp.c getopt.c gimpel.c
    globals.c hack.c indep.c irred.c main.c map.c matrix.c mincov.c opo.c pair.c part.c
    primes.c reduce.c rows.c set.c setc.c sharp.c sminterf.c solution.c sparse.c unate.c
    utility.c verify.c)

add_executable(espresso ${espresso_sources})
target_compile_options(espresso PRIVATE $<$<C_COMPILER_ID:GNU>:-std=gnu89>)
target_link_libraries(espresso m)

