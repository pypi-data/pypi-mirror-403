#ifndef SEARCH_UTILS_H
#define SEARCH_UTILS_H

#include "RandomNumberGenerator.h"
#include <any>
#include <string>
#include <unordered_map>

namespace SearchUtils
{
template <typename T>
T getParamOr(const std::unordered_map<std::string, std::any> &params,
             const std::string &key,
             T defaultValue)
{
    auto it = params.find(key);
    if (it != params.end())
    {
        try
        {
            return std::any_cast<T>(it->second);
        }
        catch (const std::bad_any_cast &)
        {
        }
    }
    return defaultValue;
}

inline void applySeed(const std::unordered_map<std::string, std::any> &params,
                      RandomNumberGenerator &rng)
{
    const int seed = getParamOr<int>(params, "seed", 0);
    if (seed > 0)
    {
        rng.setSeed(seed);
    }
}
}  // namespace SearchUtils

#endif  // SEARCH_UTILS_H
