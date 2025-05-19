#include "graph.h"
#include <queue>
#include <iostream>
#include <limits>
#include <unordered_set>
#include <algorithm>

using namespace std;

Graph::Graph(const vector<pair<string, string>>& edges) {
    for (const auto& edge : edges) {
        adjList[edge.first].insert(edge.second);
        adjList[edge.second].insert(edge.first);
    }
}

void Graph::addEdge(const string& from, const string& to) {
    adjList[from].insert(to);
    adjList[to].insert(from);  // Since the graph is undirected
}

// Helper function to check if a node is an affected area
bool isAffectedArea(const string& nodeId, const unordered_map<string, string>& idToName) {
    auto it = idToName.find(nodeId);
    if (it == idToName.end()) {
        return false;  // If we don't know what it is, assume it's safe
    }
    const string& name = it->second;
    return (name.find("Area") != string::npos || 
            name == "Graphic Era University" || 
            name == "Railway Station");
}

int Graph::shortestPath(const string& start, const string& end, vector<string>& path, 
                       const unordered_map<string, string>& idToName) const {
    unordered_map<string, int> dist;
    unordered_map<string, string> prev;
    priority_queue<pair<int, string>, vector<pair<int, string>>, greater<pair<int, string>>> pq;

    // Initialize distances
    for (const auto& p : adjList) {
        dist[p.first] = numeric_limits<int>::max();
    }
    dist[start] = 0;
    pq.push({0, start});
    prev[start] = "";  // Mark start as having no previous node

    while (!pq.empty()) {
        string u = pq.top().second;
        int d = pq.top().first;
        pq.pop();

        if (u == end) break;
        if (d > dist[u]) continue;

        auto it = adjList.find(u);
        if (it == adjList.end()) continue;  // Skip if node has no neighbors

        for (const string& v : it->second) {
            // Skip routing through affected areas (except start and end points)
            if (u != start && u != end && isAffectedArea(u, idToName)) continue;
            if (v != start && v != end && isAffectedArea(v, idToName)) continue;

            int alt = dist[u] + 1;  // Using 1 as edge weight
            if (alt < dist[v]) {
                dist[v] = alt;
                prev[v] = u;
                pq.push({alt, v});
            }
        }
    }

    // Reconstruct path
    path.clear();
    if (dist[end] == numeric_limits<int>::max()) {
        return -1;  // No path exists
    }

    // Build path from end to start
    for (string at = end; !at.empty(); at = prev[at]) {
        path.insert(path.begin(), at);
    }

    return dist[end];
}

int Graph::shortestPath(const string& start, const string& end, vector<string>& path) const {
    // Create a dummy idToName map that marks no locations as affected areas
    unordered_map<string, string> dummyIdToName;
    for (const auto& p : adjList) {
        dummyIdToName[p.first] = "Safe Location";
    }
    return shortestPath(start, end, path, dummyIdToName);
}

int Graph::findSafestPathToNearestShelter(const string& startNode,
                                          const unordered_set<string>& shelterNodes,
                                          vector<string>& pathOut) const {
    unordered_map<string, string> parent;
    unordered_set<string> visited;
    queue<string> q;

    q.push(startNode);
    visited.insert(startNode);
    parent[startNode] = "";  // Mark start as having no parent

    while (!q.empty()) {
        string current = q.front();
        q.pop();

        if (shelterNodes.find(current) != shelterNodes.end()) {
            // found nearest shelter
            pathOut.clear();
            string node = current;
            while (!node.empty()) {
                pathOut.push_back(node);
                node = parent[node];
            }
            reverse(pathOut.begin(), pathOut.end());
            return pathOut.size() - 1;
        }

        auto it = adjList.find(current);
        if (it == adjList.end()) continue;

        for (const string& neighbor : it->second) {
            if (visited.find(neighbor) == visited.end()) {
                visited.insert(neighbor);
                parent[neighbor] = current;
                q.push(neighbor);
            }
        }
    }

    return -1;
}
