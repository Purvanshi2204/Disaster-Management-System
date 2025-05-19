#include "shelter_manager.h"
#include <iostream>
#include <limits>
#include <algorithm>
#include <unordered_set>

using namespace std;

ShelterManager::ShelterManager(const vector<Shelter>& shelters)
    : shelters(shelters) {}

// Simple BFS or graph method could be used, here use graph.shortestPath for distance if needed
int ShelterManager::calculateDistance(const Graph& graph, const string& from, const string& to) const {
    vector<string> dummyPath;
    int dist = graph.shortestPath(from, to, dummyPath);
    return dist;
}

string ShelterManager::findNearestShelter(const Graph& graph, const string& location, vector<string>& pathOut, const unordered_map<string, string>& idToName) const {
    int minDistance = numeric_limits<int>::max();
    string nearestShelter;
    vector<string> bestPath;

    // Get a list of affected areas to exclude from paths
    unordered_set<string> affectedAreas;
    for (const auto& pair : idToName) {
        const string& id = pair.first;
        const string& name = pair.second;
        if (name.find("Area") != string::npos || 
            name == "Graphic Era University" || 
            name == "Railway Station") {
            affectedAreas.insert(id);
        }
    }

    // Only consider actual shelters (not warehouses)
    for (const Shelter& shelter : shelters) {
        // Skip if this location is a warehouse
        if (idToName.at(shelter.location).find("Warehouse") != string::npos ||
            idToName.at(shelter.location).find("Storehouse") != string::npos) {
            continue;
        }

        vector<string> currentPath;
        int dist = graph.shortestPath(location, shelter.location, currentPath);
        if (dist >= 0 && dist < minDistance) {
            // Check if the path goes through any affected areas
            bool validPath = true;
            for (size_t i = 1; i < currentPath.size() - 1; i++) { // Skip start and end points
                if (affectedAreas.count(currentPath[i]) > 0) {
                    validPath = false;
                    break;
                }
            }
            
            if (validPath) {
                minDistance = dist;
                nearestShelter = shelter.location;
                bestPath = currentPath;
            }
        }
    }

    pathOut = bestPath;
    return nearestShelter;
}

Shelter* ShelterManager::getShelterByLocation(const string& location) {
    for (auto& shelter : shelters) {
        if (shelter.location == location) return &shelter;
    }
    return nullptr;
}

void ShelterManager::dispatchSupplies(const vector<DisasterZone>& disasterZones, const Graph& graph, const unordered_map<string, string>& idToName, const string& targetLocation) {
    cout << "\nDispatching supplies to disaster location " << idToName.at(targetLocation) << ":\n";
    
    // Find the disaster zone for the target location
    const DisasterZone* targetZone = nullptr;
    for (const DisasterZone& dz : disasterZones) {
        if (dz.locationID == targetLocation) {
            targetZone = &dz;
            break;
        }
    }
    
    if (!targetZone) {
        cout << "No disaster zone information found for location: " << idToName.at(targetLocation) << endl;
        return;
    }

    // Resource priority order
    vector<string> resourcePriority = {"Medicine", "Food", "Water"};
    
    for (const string& resource : resourcePriority) {
        auto requiredIt = targetZone->requiredResources.find(resource);
        if (requiredIt == targetZone->requiredResources.end()) continue;

        int needed = requiredIt->second;
        if (needed <= 0) continue;

        cout << "\nDispatching " << resource << ":\n";
        
        // Find all shelters with this resource
        vector<pair<string, int>> availableShelters;
        for (const auto& shelter : shelters) {
            auto stockIt = shelter.stock.find(resource);
            if (stockIt != shelter.stock.end() && stockIt->second > 0) {
                vector<string> path;
                int distance = graph.shortestPath(targetZone->locationID, shelter.location, path);
                if (distance >= 0) {
                    availableShelters.push_back({shelter.location, distance});
                }
            }
        }

        // Sort shelters by distance
        sort(availableShelters.begin(), availableShelters.end(),
             [](const auto& a, const auto& b) { return a.second < b.second; });

        int remainingNeed = needed;
        for (const auto& [shelterLoc, distance] : availableShelters) {
            if (remainingNeed <= 0) break;

            Shelter* shelter = getShelterByLocation(shelterLoc);
            if (!shelter) continue;

            int available = shelter->stock[resource];
            int supplied = min(remainingNeed, available);
            
            if (supplied > 0) {
                shelter->stock[resource] -= supplied;
                remainingNeed -= supplied;

                cout << " Received " << supplied << " units from shelter " << shelterLoc
                     << " (" << idToName.at(shelterLoc) << ") at distance: " << distance << " hops\n";
            }
        }

        if (remainingNeed > 0) {
            cout << " Shortfall of " << remainingNeed << " units\n";
        }
    }
}
