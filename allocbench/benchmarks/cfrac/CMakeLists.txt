cmake_minimum_required(VERSION 3.0)
project(cfrac C)

set(CMAKE_BUILD_TYPE "Release")

set(cfrac_sources
    cfrac.c
    pops.c pconst.c pio.c
    pabs.c pneg.c pcmp.c podd.c phalf.c
    padd.c psub.c pmul.c pdivmod.c psqrt.c ppowmod.c
    atop.c ptoa.c itop.c utop.c ptou.c errorp.c
    pfloat.c pidiv.c pimod.c picmp.c
    primes.c pcfrac.c pgcd.c)

add_executable(cfrac ${cfrac_sources})
target_compile_options(cfrac PRIVATE $<$<C_COMPILER_ID:GNU>:-std=gnu89>)
target_compile_definitions(cfrac PRIVATE NOMEMOPT=1)
target_link_libraries(cfrac m)
