#include "utils.h"
#include <fstream>
#include <sstream>
#include <iostream>

using namespace std;

unordered_map<string, string> idToName;
unordered_map<string, string> nameToId;

vector<NodeInfo> loadNodes(const string& filename) {
    vector<NodeInfo> nodes;
    ifstream file(filename);
   string line;
    getline(file, line); // skip header

    while (std::getline(file, line)) {
        std::stringstream ss(line);
        std::string id, name, lat, lon, type;
        std::getline(ss, id, ',');
        std::getline(ss, name, ',');
        std::getline(ss, lat, ',');  // Skip latitude
        std::getline(ss, lon, ',');  // Skip longitude
        std::getline(ss, type, ','); // Read type
        nodes.push_back({id, name, type});
        idToName[id] = name;
        nameToId[name] = id;
    }
    return nodes;
}

vector<pair<string, string>> loadEdges(const string& filename) {
    vector<pair<string, string>> edges;
    ifstream file(filename);
    string line;

    if (!file.is_open()) {
        cerr << "Failed to open edges file: " << filename << endl;
        return edges;
    }

    bool firstLine = true;
    while (getline(file, line)) {
        if (firstLine) { firstLine = false; continue; }  // skip header
        stringstream ss(line);
        string from, to;
        if (!getline(ss, from, ',')) continue;
        if (!getline(ss, to, ',')) continue;

        edges.emplace_back(from, to);
    }
    return edges;
}

vector<Shelter> loadShelters(const string& filename) {
    vector<Shelter> shelters;
    ifstream file(filename);
    string line;

    if (!file.is_open()) {
        cerr << "Failed to open shelters file: " << filename << endl;
        return shelters;
    }

    bool firstLine = true;
    while (getline(file, line)) {
        if (firstLine) { firstLine = false; continue; }  // skip header
        stringstream ss(line);
        string location, stockLevelStr, supplyType, vehicleCapacityStr;

        if (!getline(ss, location, ',')) continue;
        if (!getline(ss, stockLevelStr, ',')) continue;
        if (!getline(ss, supplyType, ',')) continue;
        if (!getline(ss, vehicleCapacityStr, ',')) continue;

        int stockLevel = stoi(stockLevelStr);
        int vehicleCapacity = stoi(vehicleCapacityStr);

        // Find if shelter location already exists
        auto it = find_if(shelters.begin(), shelters.end(), 
            [&](const Shelter& s){ return s.location == location; });
        
        if (it != shelters.end()) {
            it->stock[supplyType] = stockLevel;
            it->vehicleCapacity = max(it->vehicleCapacity, vehicleCapacity);
        } else {
            Shelter s;
            s.location = location;
            s.stock[supplyType] = stockLevel;
            s.vehicleCapacity = vehicleCapacity;
            shelters.push_back(s);
        }
    }
    return shelters;
}

vector<RescueTeam> loadRescueTeams(const string& filename) {
    vector<RescueTeam> teams;
    ifstream file(filename);
    string line;

    if (!file.is_open()) {
        cerr << "Failed to open rescue teams file: " << filename << endl;
        return teams;
    }

    bool firstLine = true;
    while (getline(file, line)) {
        if (firstLine) { firstLine = false; continue; }
        stringstream ss(line);
        string id, baseLocation, speedStr, availabilityStr;

        if (!getline(ss, id, ',')) continue;
        if (!getline(ss, baseLocation, ',')) continue;
        if (!getline(ss, speedStr, ',')) continue;
        if (!getline(ss, availabilityStr, ',')) continue;

        int speed = stoi(speedStr);
        bool isAvailable = (availabilityStr == "Available");

        teams.push_back({id, baseLocation, speed, isAvailable});
    }
    return teams;
}

vector<DisasterZone> loadDisasterZones(const string& filename) {
    vector<DisasterZone> zones;
    ifstream file(filename);
    string line;

    if (!file.is_open()) {
        cerr << "Failed to open disaster zones file: " << filename << endl;
        return zones;
    }

    bool firstLine = true;
    while (getline(file, line)) {
        if (firstLine) { firstLine = false; continue; }
        stringstream ss(line);
        string locationID, resourceType, amountStr, severityStr;

        if (!getline(ss, locationID, ',')) continue;
        if (!getline(ss, resourceType, ',')) continue;
        if (!getline(ss, amountStr, ',')) continue;
        if (!getline(ss, severityStr, ',')) continue;

        int amount = stoi(amountStr);
        int severity = stoi(severityStr);

        // Find if disaster zone exists
        auto it = find_if(zones.begin(), zones.end(), 
            [&](const DisasterZone& dz) { return dz.locationID == locationID; });
        
        if (it != zones.end()) {
            it->requiredResources[resourceType] = amount;
            it->severity = max(it->severity, severity);
        } else {
            DisasterZone dz;
            dz.locationID = locationID;
            dz.requiredResources[resourceType] = amount;
            dz.severity = severity;
            zones.push_back(dz);
        }
    }
    return zones;
}
