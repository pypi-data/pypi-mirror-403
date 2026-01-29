/**
 * pybind.cpp
 *
 * Python bindings for PyCNP - Critical Node Problem solver package.
 *
 * This file implements Python bindings for the PyCNP algorithm package, using pybind11
 * to expose C++ core algorithms to Python interface. Contains bindings for core components
 * including graph structures, crossover operators, population management, search strategies, etc.
 */

// Standard library headers
#include <stdexcept>
#include <memory>
#include <functional>

// PyCNP core headers
#include "Graph/CNP_Graph.h"
#include "Graph/DCNP_Graph.h"
#include "Graph/Graph.h"
#include "Population.h"
#include "ProblemData.h"
#include "search/Search.h"
#include "search/SearchStrategy.h"
#include "search/CBNSStrategy.h"
#include "search/CHNSStrategy.h"
#include "search/DLASStrategy.h"
#include "search/BCLSStrategy.h"

// pybind11 related headers
#include <pybind11/functional.h>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/stl_bind.h>
#include <pybind11/numpy.h>

// Auto-generated documentation headers
#include "pycnp_docs.h"

namespace py = pybind11;

// ============================================================================
// Helper function definitions
// ============================================================================

/**
 * Convert C++ Solution (unordered_set<int>) to Python set.
 *
 * This helper function is used to convert solution set data structures between C++ and Python.
 * Solution is represented as unordered_set<int> in C++, containing IDs of removed nodes.
 *
 * Parameters
 * ----------
 * sol : Solution
 *     C++ solution set containing node IDs
 *
 * Returns
 * -------
 * py::set
 *     Python set object containing the same node IDs
 *
 * Raises
 * ------
 * std::bad_alloc
 *     If memory allocation fails
 */
py::set solutionToPyset(const Solution &sol)
{
    try {
        py::set pyset;
        for (const auto &node : sol) {
            pyset.add(py::int_(node));
        }
        return pyset;
    } catch (const std::exception& e) {
        throw std::runtime_error("Failed to convert C++ Solution to Python set: " + std::string(e.what()));
    }
}

/**
 * Convert Python set to C++ Solution (unordered_set<int>).
 *
 * This helper function converts Python-passed node sets to C++ Solution type.
 * Includes input validation to ensure all elements are valid integer node IDs.
 *
 * Parameters
 * ----------
 * py_set : py::set
 *     Python set object, should contain integer node IDs
 *
 * Returns
 * -------
 * Solution
 *     C++ Solution object
 *
 * Raises
 * ------
 * std::invalid_argument
 *     If set contains non-integer elements
 * std::runtime_error
 *     If error occurs during conversion
 */
Solution pysetToSolution(const py::set &py_set)
{
    try {
        Solution sol;
        for (auto item : py_set) {
            if (!py::isinstance<py::int_>(item)) {
                throw std::invalid_argument("All elements in solution set must be integers");
            }
            int node_id = item.cast<int>();
            if (node_id < 0) {
                throw std::invalid_argument("Node IDs must be non-negative integers");
            }
            sol.insert(node_id);
        }
        return sol;
    } catch (const py::cast_error& e) {
        throw std::invalid_argument("Failed to cast Python set element to integer: " + std::string(e.what()));
    } catch (const std::exception& e) {
        throw std::runtime_error("Failed to convert Python set to C++ Solution: " + std::string(e.what()));
    }
}

// ============================================================================
// Python module definition
// ============================================================================

PYBIND11_MODULE(_pycnp, m)
{
    // Module documentation string
    m.doc() = R"doc(
        PyCNP - Python bindings for Critical Node Problem solver

        This module provides Python bindings for a high-performance C++ implementation
        of algorithms for solving Critical Node Problems (CNP) and Distance-based
        Critical Node Problems (DCNP).

        The module includes:
        - Graph data structures and algorithms
        - Population-based search algorithms
        - Crossover operators for evolutionary algorithms
        - Local search strategies
        - Problem data management utilities

        Example:
            >>> import pycnp
            >>> problem_data = pycnp.read("graph.txt")
            >>> model = pycnp.Model.from_data(problem_data)
            >>> result = model.solve("CNP", budget=10, stopping_criterion=pycnp.MaxRuntime(60))
    )doc";

    // ========================================================================
    // Constant definitions - Search strategies
    // ========================================================================

    // Search strategy constants - used to specify local search algorithm types
    m.attr("CBNS") = "CBNS";  // Component-Based Neighborhood Search
    m.attr("CHNS") = "CHNS";  // Component-Based Hybrid Neighborhood Search
    m.attr("DLAS") = "DLAS";  // Diversified Late Acceptance Search
    m.attr("BCLS") = "BCLS";  // Betweenness centrality-based late-acceptance search

    // Problem type constants - used to specify the problem type to solve
    m.attr("CNP") = "CNP";     // Critical Node Problem
    m.attr("DCNP") = "DCNP";   // Distance-based Critical Node Problem

    // Crossover strategy constants - used to specify crossover operator types
    m.attr("DBX") = "DBX";     // Double Backbone Based Crossover
    m.attr("RSC") = "RSC";     // Reduce Solve Combine
    m.attr("IRR") = "IRR";     // Inherit Repair Recombination Crossover

    // ========================================================================
    // Exception type bindings
    // ========================================================================

    // Bind standard exception types to ensure C++ exceptions are properly passed to Python
    py::register_exception<std::invalid_argument>(m, "InvalidArgumentError");
    py::register_exception<std::runtime_error>(m, "RuntimeError");

    // ========================================================================
    // Graph structure class bindings
    // ========================================================================

    // Graph wrapper binding - serves as handle type
    py::class_<Graph, std::unique_ptr<Graph>>(m, "Graph", DOC_IMPL(Graph));

    // ========================================================================
    // Search algorithm class bindings
    // ========================================================================

    // Search class binding - Local search algorithm manager
    py::class_<Search>(m, "Search", DOC_IMPL(Search))
        .def(py::init<Graph &, int>(),
             py::arg("graph"),
             py::arg("seed"),
             DOC_IMPL(Search, Search))
        .def("set_strategy", &Search::setStrategy,
             py::arg("strategy"),
             DOC_IMPL(Search, setStrategy))
        .def("run", &Search::run,
             DOC_IMPL(Search, run));

    // ========================================================================
    // Problem data class bindings
    // ========================================================================

    // ProblemData class binding - Graph problem data manager
    py::class_<ProblemData>(m, "ProblemData", DOC_IMPL(ProblemData))
        .def(py::init<int>(),
             py::arg("num_nodes"),
             DOC_IMPL(ProblemData, ProblemData))
        .def_static("read_from_adjacency_list_file",
                    &ProblemData::readFromAdjacencyListFile,
                    py::arg("filename"),
                    DOC_IMPL(ProblemData, readFromAdjacencyListFile))
        .def_static("read_from_edge_list_format",
                    &ProblemData::readFromEdgeListFormat,
                    py::arg("filename"),
                    DOC_IMPL(ProblemData, readFromEdgeListFormat))
        .def("create_original_graph",
             &ProblemData::createOriginalGraph,
             py::arg("problem_type"),
             py::arg("budget"),
             py::arg("seed"),
             py::arg("hop_distance") = std::numeric_limits<int>::max(),
             DOC_IMPL(ProblemData, createOriginalGraph))
        .def("add_node", &ProblemData::addNode,
             py::arg("node_id"),
             DOC_IMPL(ProblemData, addNode))
        .def("add_edge", &ProblemData::addEdge,
             py::arg("u"), py::arg("v"),
             DOC_IMPL(ProblemData, addEdge))
        .def("get_nodes_set", &ProblemData::getNodesSet,
             py::return_value_policy::reference_internal,
             DOC_IMPL(ProblemData, getNodesSet))
        .def("get_adj_list", &ProblemData::getAdjList,
             py::return_value_policy::reference_internal,
             DOC_IMPL(ProblemData, getAdjList))
        .def("num_nodes", &ProblemData::numNodes,
             DOC_IMPL(ProblemData, numNodes));


    // ========================================================================
    // Population management class bindings
    // ========================================================================

    // Population class binding - Evolutionary algorithm population manager
    py::class_<Population, std::unique_ptr<Population>>(m, "Population", DOC_IMPL(Population))
        .def(py::init<Graph &, const std::string &, bool, int, int, int, int, int>(),
             py::arg("original_graph"),
             py::arg("search"),
             py::arg("is_pop_variable"),
             py::arg("initial_pop_size"),
             py::arg("max_pop_size"),
             py::arg("increase_pop_size"),
             py::arg("max_idle_gens"),
             py::arg("seed"))
        .def("update",
             [=](Population &self, const py::set &solution_set, int obj_value,
                int num_idle_generations, bool verbose) {
                 try {
                     // Parameter validation
                     if (obj_value < 0) {
                         throw std::invalid_argument("Objective value must be non-negative");
                     }
                     if (num_idle_generations < 0) {
                         throw std::invalid_argument("Number of idle generations must be non-negative");
                     }

                     // Convert solution set
                     Solution sol = pysetToSolution(solution_set);
                     self.update(sol, obj_value, num_idle_generations, verbose);
                 } catch (const std::exception& e) {
                     throw std::runtime_error("Population update failed: " + std::string(e.what()));
                 }
             },
             py::arg("solution"),
             py::arg("obj_value"),
             py::arg("num_idle_generations"),
             py::arg("verbose") = false,
             DOC_IMPL(Population, update))
        .def("initialize",
             [=](Population &self, bool display, py::object stopping_criterion_obj) {
                 try {
                     // Build stopping criterion function
                     std::function<bool(int)> stopping_criterion = nullptr;
                     if (!stopping_criterion_obj.is_none()) {
                         // Verify if stopping criterion object is callable
                         if (!py::hasattr(stopping_criterion_obj, "__call__")) {
                             throw std::invalid_argument("Stopping criterion must be callable");
                         }

                         stopping_criterion = [=](int best_obj_value) -> bool {
                             try {
                                 return stopping_criterion_obj(best_obj_value).cast<bool>();
                             } catch (const py::cast_error& e) {
                                 throw std::runtime_error("Stopping criterion must return boolean value");
                             }
                         };
                     }

                     auto [solution, obj_value] = self.initialize(display, stopping_criterion);
                     return std::make_pair(solutionToPyset(solution), obj_value);
                 } catch (const std::exception& e) {
                     throw std::runtime_error("Population initialization failed: " + std::string(e.what()));
                 }
             },
             py::arg("display") = false,
             py::arg("stopping_criterion") = py::none())
        .def("select",
             [=](Population &p) {
                 try {
                     // Tournament selection of two different solutions as parents
                     auto result = p.tournamentSelectTwoSolutions();
                     py::tuple py_result(2);
                     py_result[0] = solutionToPyset(result.first);
                     py_result[1] = solutionToPyset(result.second);
                     return py_result;
                 } catch (const std::exception& e) {
                     throw std::runtime_error("Solution selection failed: " + std::string(e.what()));
                 }
             },
             DOC_IMPL(Population, tournamentSelectTwoSolutions))
        .def("get_all_three_solutions",
             [](const Population &p) {
                 try {
                     auto [sol1, sol2, sol3] = p.getAllThreeSolutions();
                     py::tuple py_result(3);
                     py_result[0] = solutionToPyset(sol1);
                     py_result[1] = solutionToPyset(sol2);
                     py_result[2] = solutionToPyset(sol3);
                     return py_result;
                 } catch (const std::exception& e) {
                     throw std::runtime_error("Failed to get three solutions: " + std::string(e.what()));
                 }
             },
             DOC_IMPL(Population, getAllThreeSolutions))
        .def("get_size", &Population::getSize,
             DOC_IMPL(Population, getSize))
        ;

    // ========================================================================
    // Search result class bindings
    // ========================================================================

    // SearchResult class binding - Search algorithm result container
    py::class_<SearchResult>(m, "SearchResult", DOC_IMPL(SearchResult))
        .def(py::init<>())
        .def_property_readonly("solution",
                              [](const SearchResult &r) {
                                  try {
                                      return solutionToPyset(r.solution);
                                  } catch (const std::exception& e) {
                                      throw std::runtime_error("Failed to convert solution: " + std::string(e.what()));
                                  }
                              })
        .def_readwrite("obj_value", &SearchResult::objValue)
        .def("__repr__", [](const SearchResult &r) {
            return "<SearchResult(obj_value=" + std::to_string(r.objValue) +
                   ", solution_size=" + std::to_string(r.solution.size()) + ")>";
        });

    // ========================================================================
    // Internal C++ Graph Implementations
    // ========================================================================

    // CNP_Graph binding - Critical Node Problem graph implementation
    py::class_<CNP_Graph>(m, "CNP_Graph", DOC_IMPL(CNP_Graph))
        .def(py::init<>())
        .def("clone", &CNP_Graph::clone, DOC_IMPL(CNP_Graph, clone))
        .def("update_graph_by_removed_nodes", &CNP_Graph::updateGraphByRemovedNodes)
        .def("get_reduced_graph_by_removed_nodes", &CNP_Graph::getReducedGraphByRemovedNodes)
        .def("add_node", &CNP_Graph::addNode)
        .def("remove_node", &CNP_Graph::removeNode)
        .def("is_node_removed", &CNP_Graph::isNodeRemoved)
        .def("get_num_nodes", &CNP_Graph::getNumNodes)
        .def("get_removed_nodes", &CNP_Graph::getRemovedNodes, py::return_value_policy::reference_internal)
        .def("set_node_age", &CNP_Graph::setNodeAge)
        .def("get_objective_value", &CNP_Graph::getObjectiveValue)
        .def_readwrite("removed_nodes", &CNP_Graph::removedNodes);

    // DCNP_Graph binding - Distance-based Critical Node Problem graph implementation
    py::class_<DCNP_Graph>(m, "DCNP_Graph", DOC_IMPL(DCNP_Graph))
        .def(py::init<>())
        .def("update_graph_by_removed_nodes", &DCNP_Graph::updateGraphByRemovedNodes)
        .def("get_reduced_graph_by_removed_nodes", &DCNP_Graph::getReducedGraphByRemovedNodes)
        .def("remove_node", &DCNP_Graph::removeNode)
        .def("add_node", &DCNP_Graph::addNode)
        .def("set_node_age", &DCNP_Graph::setNodeAge)
        .def("is_node_removed", &DCNP_Graph::isNodeRemoved)
        .def("get_removed_nodes", &DCNP_Graph::getRemovedNodes, py::return_value_policy::reference_internal)
        .def("get_num_nodes", &DCNP_Graph::getNumNodes)
        .def("get_objective_value", &DCNP_Graph::getObjectiveValue)
        .def("get_random_feasible_graph", &DCNP_Graph::getRandomFeasibleGraph)
        .def("build_tree", &DCNP_Graph::buildTree)
        .def("calculate_k_hop_tree_size", &DCNP_Graph::calculateKhopTreeSize)
        .def("calculate_betweenness_centrality", &DCNP_Graph::calculateBetweennessCentrality, py::return_value_policy::reference_internal)
        .def("find_best_node_to_remove", &DCNP_Graph::findBestNodeToRemove)
        .def("find_best_node_to_add", &DCNP_Graph::findBestNodeToAdd)
        .def("clone", &DCNP_Graph::clone);

    // ========================================================================
    // Search Strategy Classes
    // ========================================================================

    // SearchStrategy base class binding
    py::class_<SearchStrategy>(m, "SearchStrategy", DOC_IMPL(SearchStrategy))
        .def("execute", &SearchStrategy::execute);

    // CBNSStrategy binding - Component-Based Neighborhood Search
    py::class_<CBNSStrategy, SearchStrategy>(m, "CBNSStrategy", DOC_IMPL(CBNSStrategy))
        .def(py::init<Graph &, const std::unordered_map<std::string, std::any> &>(),
             py::arg("graph"), py::arg("params"))
        .def("execute", &CBNSStrategy::execute);

    // CHNSStrategy binding - Component-Based Hybrid Neighborhood Search
    py::class_<CHNSStrategy, SearchStrategy>(m, "CHNSStrategy", DOC_IMPL(CHNSStrategy))
        .def(py::init<Graph &, const std::unordered_map<std::string, std::any> &>(),
             py::arg("graph"), py::arg("params"))
        .def("execute", &CHNSStrategy::execute);

    // DLASStrategy binding - Diversified Late Acceptance Search
    py::class_<DLASStrategy, SearchStrategy>(m, "DLASStrategy", DOC_IMPL(DLASStrategy))
        .def(py::init<Graph &, const std::unordered_map<std::string, std::any> &>(),
             py::arg("graph"), py::arg("params"))
        .def("execute", &DLASStrategy::execute);

    // BCLSStrategy binding - Betweenness Centrality-based Late Acceptance Search
    py::class_<BCLSStrategy, SearchStrategy>(m, "BCLSStrategy", DOC_IMPL(BCLSStrategy))
        .def(py::init<Graph &, const std::unordered_map<std::string, std::any> &>(),
             py::arg("graph"), py::arg("params"))
        .def("execute", &BCLSStrategy::execute);

    // ========================================================================
    // Module end marker
    // ========================================================================
}