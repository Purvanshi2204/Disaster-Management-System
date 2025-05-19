#ifndef SHELTERS_H
#define SHELTERS_H

#include <string>
#include <unordered_map>
#include <vector>
#include <iostream>

using namespace std;

struct Shelter {
    string location;      // Shelter location ID
    int stockLevel;       // Available stock level (capacity)
    string supplyType;    // Supply type: Food, Water, Medicine
    int vehicleCapacity;  // Vehicle capacity for transport

    Shelter() : stockLevel(0), vehicleCapacity(0) {}
    Shelter(const string& loc, int stock, const string& supply, int vehicleCap)
        : location(loc), stockLevel(stock), supplyType(supply), vehicleCapacity(vehicleCap) {}

    bool isFull() const {
        return stockLevel <= 0;  // no stock means unavailable/full
    }
};

class ShelterManager {
private:
    unordered_map<string, Shelter> shelters; // key: location

public:
    void loadSheltersFromFile(const string& filename);

    // Get shelter by location, return true if found
    bool getShelterByLocation(const string& location, Shelter& shelter) const;

    // Update stock level, mark unavailable if stock <= 0
    bool updateStockLevel(const string& location, int newStockLevel);

    vector<Shelter> getAllShelters() const;

    void printShelters() const;
};

#endif // SHELTERS_H