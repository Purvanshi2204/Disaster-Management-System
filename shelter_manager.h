#pragma once
#include "utils.h"
#include "graph.h"
#include <vector>
#include <unordered_map>

using namespace std;

class ShelterManager {
public:
    ShelterManager(const vector<Shelter>& shelters);

    // Find nearest shelter to location, returns shelter location, fills pathOut
    string findNearestShelter(const Graph& graph, const string& location, vector<string>& pathOut, const unordered_map<string, string>& idToName) const;

    Shelter* getShelterByLocation(const string& location);

    // Dispatch supplies from shelters to a specific disaster zone
    void dispatchSupplies(const vector<DisasterZone>& disasterZones, const Graph& graph, const unordered_map<string, string>& idToName, const string& targetLocation);

private:
    vector<Shelter> shelters;

    int calculateDistance(const Graph& graph, const string& from, const string& to) const;
};
