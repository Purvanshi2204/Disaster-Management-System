#pragma once
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>

using namespace std;

class Graph {
public:
    Graph(const vector<pair<string, string>>& edges);
    void addEdge(const string& from, const string& to);
    
    // Find shortest path between two nodes, avoiding affected areas
    int shortestPath(const string& start, const string& end, vector<string>& path, 
                    const unordered_map<string, string>& idToName) const;
    
    // Legacy version for backward compatibility
    int shortestPath(const string& start, const string& end, vector<string>& path) const;
    
    int findSafestPathToNearestShelter(const string& startNode,
                                      const unordered_set<string>& shelterNodes,
                                      vector<string>& pathOut) const;

private:
    unordered_map<string, unordered_set<string>> adjList;
};
