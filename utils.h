#pragma once
#include <string>
#include <unordered_map>
#include <vector>

using namespace std;

struct NodeInfo {
    string id;
    string name;
    string type;
};

struct DisasterZone {
    string locationID;
    unordered_map<string, int> requiredResources;  // e.g., {"Water": 300, "Food": 150}
    int severity;
};

struct Shelter {
    string location;
    unordered_map<string, int> stock;  // e.g., {"Food": 200, "Water": 100}
    int vehicleCapacity;
};

struct RescueTeam {
    string id;
    string baseLocation;
    int speed;
    bool isAvailable;
};
// utils.h
extern std::unordered_map<std::string, std::string> idToName;
extern std::unordered_map<std::string, std::string> nameToId;


// Loading functions declarations:
vector<NodeInfo> loadNodes(const string& filename);
vector<pair<string, string>> loadEdges(const string& filename);  // edges as pairs of node IDs
vector<Shelter> loadShelters(const string& filename);
vector<RescueTeam> loadRescueTeams(const string& filename);
vector<DisasterZone> loadDisasterZones(const string& filename);
