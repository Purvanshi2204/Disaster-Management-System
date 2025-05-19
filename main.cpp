// File: main.cpp

#include <iostream>
#include <vector>
#include <unordered_map>
#include <unordered_set>
#include <string>
#include <limits>

#include "utils.h"
#include "graph.h"
#include "shelter_manager.h"

using namespace std;

// Helper function to find nearest hospital
pair<string, vector<string>> findNearestHospital(const Graph& graph, 
                                                const string& location,
                                                const vector<NodeInfo>& nodes,
                                                const unordered_map<string, string>& idToName) {
    int minDistance = numeric_limits<int>::max();
    string nearestHospital;
    vector<string> bestPath;

    for (const auto& node : nodes) {
        if (node.type == "hospital") {
            vector<string> path;
            int dist = graph.shortestPath(location, node.id, path, idToName);
            if (dist >= 0 && dist < minDistance) {
                minDistance = dist;
                nearestHospital = node.id;
                bestPath = path;
            }
        }
    }

    return {nearestHospital, bestPath};
}

int main() {
    // Load data
    vector<NodeInfo> nodes = loadNodes("nodes.txt"); // Loads ID ↔ Name
    vector<pair<string, string>> edges = loadEdges("edges.txt");
    vector<Shelter> shelters = loadShelters("relief_supplies.txt");
    vector<RescueTeam> teams = loadRescueTeams("rescue_teams.txt");
    vector<DisasterZone> disasterZones = loadDisasterZones("disaster_zones.txt");

    // Map name <-> ID
    unordered_map<string, string> nameToId;
    unordered_map<string, string> idToName;
    for (const auto& node : nodes) {
        nameToId[node.name] = node.id;
        idToName[node.id] = node.name;
    }

    Graph graph(edges);
    ShelterManager shelterManager(shelters);

    // 🌍 Ask user for disaster location by name
    string disasterLocationName;
    cout << "Enter disaster location name (e.g., Patel Nagar Main): ";
    getline(cin, disasterLocationName);

    if (nameToId.find(disasterLocationName) == nameToId.end()) {
        cout << "❌ Location not found: " << disasterLocationName << endl;
        return 1;
    }

    string disasterLocation = nameToId[disasterLocationName];

    // 🏥 Find nearest hospital
    auto [nearestHospital, pathToHospital] = findNearestHospital(graph, disasterLocation, nodes, idToName);
    
    if (!nearestHospital.empty()) {
        cout << "\n🏥 Nearest hospital to disaster at " << disasterLocationName 
             << " is " << idToName[nearestHospital] << " (" << nearestHospital << ")\n";
        cout << "Path to hospital: ";
        for (const string& node : pathToHospital) {
            cout << idToName[node] << " -> ";
        }
        cout << "🏥\n";
    } else {
        cout << "\n❌ No hospital found near disaster location: " << disasterLocationName << "\n";
    }

    // 🚑 Find nearest shelter
    vector<string> pathToShelter;
    string nearestShelter = shelterManager.findNearestShelter(graph, disasterLocation, pathToShelter, idToName);

    if (nearestShelter.empty()) {
        cout << "❌ No shelter found near disaster location: " << disasterLocationName << "\n";
    } else {
        cout << "\n✅ Nearest shelter to disaster at " << disasterLocationName << " is " << idToName[nearestShelter] << " (" << nearestShelter << ")\n";
        cout << "Path to shelter: ";
        for (const string& node : pathToShelter) {
            cout << idToName[node] << " -> ";
        }
        cout << "🏥\n";
    }

    // 🩺 Dispatch relief supplies (based on need)
    shelterManager.dispatchSupplies(disasterZones, graph, idToName, disasterLocation);

    // 👨‍🚒 Allocate rescue team
    int minDist = numeric_limits<int>::max();
    RescueTeam* allocatedTeam = nullptr;
    vector<string> pathTeamToDZ;
    for (auto& team : teams) {
        vector<string> path;
        int dist = graph.shortestPath(team.baseLocation, disasterLocation, path, idToName);
        if (dist != -1 && dist < minDist) {
            minDist = dist;
            allocatedTeam = &team;
            pathTeamToDZ = path;
        }
    }

    if (allocatedTeam) {
        cout << "\n🚨 Rescue Team " << allocatedTeam->id << " based at " << idToName[allocatedTeam->baseLocation]
             << " assigned to disaster at " << disasterLocationName << "\n";
        cout << "Path for Rescue Team: ";
        for (const string& node : pathTeamToDZ) cout << idToName[node] << " -> ";
        cout << "🚨\n";
    } else {
        cout << "\n❌ No rescue team available for " << disasterLocationName << "\n";
    }

    return 0;
}
