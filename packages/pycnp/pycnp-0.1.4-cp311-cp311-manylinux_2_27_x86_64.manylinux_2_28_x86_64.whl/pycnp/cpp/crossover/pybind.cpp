#include "doubleBackboneBasedCrossover.h"
#include "inherit_repair_recombination.h"
#include "reduceSolveCombine.h"
#include "crossover_docs.h"

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <stdexcept>

namespace py = pybind11;

namespace
{
    Solution pysetToSolution(const py::set &py_set)
    {
        Solution sol;
        for (auto item : py_set)
        {
            sol.insert(item.cast<int>());
        }
        return sol;
    }
}

PYBIND11_MODULE(_crossover, m)
{
    // Ensure core types are registered
    py::module_::import("pycnp._pycnp");

    m.doc() = "Crossover operators for PyCNP";

    m.attr("DBX") = "DBX";
    m.attr("RSC") = "RSC";
    m.attr("IRR") = "IRR";

    m.def(
        "double_backbone_based_crossover",
        [](const Graph &orig_graph, const std::vector<py::set> &parents, int seed)
        {
            if (parents.size() != 2)
            {
                throw std::invalid_argument("double_backbone_based_crossover requires exactly 2 parents");
            }
            std::pair<const Solution *, const Solution *> parent_pair;
            std::vector<Solution> sols;
            sols.reserve(2);
            for (const auto &p : parents)
            {
                sols.push_back(pysetToSolution(p));
            }
            parent_pair = {&sols[0], &sols[1]};
            auto result = doubleBackboneBasedCrossover(orig_graph, parent_pair, seed);
            return result;
        },
        py::arg("orig_graph"),
        py::arg("parents"),
        py::arg("seed"),
        py::return_value_policy::take_ownership,
        DOC_IMPL(doubleBackboneBasedCrossover));

    m.def(
        "inherit_repair_recombination",
        [](const Graph &orig_graph, const std::vector<py::set> &parents, int seed)
        {
            if (parents.size() != 3)
            {
                throw std::invalid_argument("inherit_repair_recombination requires exactly 3 parents");
            }
            std::tuple<const Solution *, const Solution *, const Solution *> parent_tuple;
            std::vector<Solution> sols;
            sols.reserve(3);
            for (const auto &p : parents)
            {
                sols.push_back(pysetToSolution(p));
            }
            parent_tuple = {&sols[0], &sols[1], &sols[2]};
            return inherit_repair_recombination(orig_graph, parent_tuple, seed);
        },
        py::arg("orig_graph"),
        py::arg("parents"),
        py::arg("seed"),
        py::return_value_policy::take_ownership,
        DOC_IMPL(inherit_repair_recombination));

    m.def(
        "reduce_solve_combine",
        [](const Graph &orig_graph,
           const std::vector<py::set> &py_parents,
           const std::string &search_strategy,
           double beta,
           int seed)
        {
            if (py_parents.size() != 2)
            {
                throw std::invalid_argument("reduce_solve_combine requires exactly 2 parents");
            }
            std::vector<Solution> cpp_solutions;
            cpp_solutions.reserve(2);
            for (const auto &p_set : py_parents)
            {
                cpp_solutions.push_back(pysetToSolution(p_set));
            }
            std::pair<const Solution *, const Solution *> parent_pair = {
                &cpp_solutions[0], &cpp_solutions[1]};
            return reduceSolveCombine(
                orig_graph,
                parent_pair,
                search_strategy,
                beta,
                seed);
        },
        py::arg("orig_graph"),
        py::arg("parents"),
        py::arg("search") = "CHNS",
        py::arg("beta") = 0.9,
        py::arg("seed"),
        py::return_value_policy::take_ownership,
        DOC_IMPL(reduceSolveCombine));
}