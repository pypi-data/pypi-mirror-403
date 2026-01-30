
// Auto-generated during compilation. Do not edit.

#define __EXPAND(x) x
#define __COUNT(_1, _2, _3, _4, _5, _6, _7, COUNT, ...) COUNT
#define __VA_SIZE(...) __EXPAND(__COUNT(__VA_ARGS__, 7, 6, 5, 4, 3, 2, 1, 0))
#define __CAT1(a, b) a ## b
#define __CAT2(a, b) __CAT1(a, b)
#define __DOC1(n1) PYCNP_doc_##n1
#define __DOC2(n1, n2) PYCNP_doc_##n1##_##n2
#define __DOC3(n1, n2, n3) PYCNP_doc_##n1##_##n2##_##n3
#define __DOC4(n1, n2, n3, n4) PYCNP_doc_##n1##_##n2##_##n3##_##n4
#define __DOC5(n1, n2, n3, n4, n5) PYCNP_doc_##n1##_##n2##_##n3##_##n4##_##n5
#define __DOC6(n1, n2, n3, n4, n5, n6)     PYCNP_doc_##n1##_##n2##_##n3##_##n4##_##n5##_##n6
#define __DOC7(n1, n2, n3, n4, n5, n6, n7)     PYCNP_doc_##n1##_##n2##_##n3##_##n4##_##n5##_##n6##_##n7
#define DOC(...)     __EXPAND(__EXPAND(__CAT2(__DOC, __VA_SIZE(__VA_ARGS__)))(__VA_ARGS__))
#define DOC_IMPL(...) DOC(__VA_ARGS__)

#if defined(__GNUG__)
#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wunused-variable"
#endif

static char const *PYCNP_doc_inherit_repair_recombination = R"doc(
@brief Inherit-Repair-Recombination (IRR) crossover operator.

Uses three parents to create offspring through a process of inheritance
followed by repair operations to maintain feasibility.

@param originalGraph The original problem graph.
@param parents Tuple of three parent solutions.
@param seed Random seed for the operation.
@return Unique pointer to the new offspring graph.
)doc";
static char const *PYCNP_doc_doubleBackboneBasedCrossover = R"doc(
@brief Double Backbone Based (DBX) crossover operator.

Identifies common nodes between parent solutions (the "backbone") and
constructs an offspring by preserving these common nodes and probabilistically
inheriting others.

@param originalGraph The original problem graph.
@param parents Pair of parent solutions to cross over.
@param seed Random seed for the operation.
@return Unique pointer to the new offspring graph.
)doc";
static char const *PYCNP_doc_reduceSolveCombine = R"doc(
@brief Reduce-Solve-Combine (RSC) crossover operator.

Reduces common nodes between parents, solves the reduced subproblem
via local search, and combines the results to form an offspring.

@param originalGraph The original problem graph.
@param parents Pair of parent solutions.
@param search_strategy The local search strategy to use on the subproblem.
@param beta Parameter controlling the reduction intensity.
@param seed Random seed for the operation.
@return Unique pointer to the new offspring graph.
)doc";
static char const *PYCNP_doc_Population_initialize = R"doc(
initialize

Initializes the population with diverse solutions.

Generates initial solutions using local search with random starting points.

Returns
-------
Tuple[Solution, int]
    Pair of (best initial solution, its objective value)
)doc";

#if defined(__GNUG__)
#pragma GCC diagnostic pop
#endif

