#include <iostream>
#include <vector>
#include <queue>
#include <algorithm>
#include <unordered_set>
using namespace std;

#define N 4

struct Node {
    vector<vector<int>> mat;
    int x, y, cost, level;
    Node* parent;
};

int row[] = {1, 0, -1, 0};
int col[] = {0, -1, 0, 1};

int calculateCost(vector<vector<int>>& mat, vector<vector<int>>& final) {
    int count = 0;
    for (int i = 0; i < N; i++)
        for (int j = 0; j < N; j++)
            if (mat[i][j] && mat[i][j] != final[i][j])
                count++;
    return count;
}

bool isSafe(int x, int y) {
    return (x >= 0 && x < N && y >= 0 && y < N);
}

bool operator>(const Node& a, const Node& b) {
    return (a.cost + a.level) > (b.cost + b.level);
}

string serialize(vector<vector<int>>& mat) {
    string s;
    for (auto& row : mat)
        for (auto& num : row)
            s += to_string(num) + ",";
    return s;
}

void printPath(Node* root) {
    if (root == nullptr) return;
    printPath(root->parent);
    for (auto& row : root->mat) {
        for (auto& val : row)
            cout << val << " ";
        cout << endl;
    }
    cout << endl;
}

void solve(vector<vector<int>> initial, vector<vector<int>> final, int x, int y) {
    priority_queue<Node, vector<Node>, greater<Node>> pq;
    unordered_set<string> visited;
    Node* root = new Node{initial, x, y, calculateCost(initial, final), 0, nullptr};
    pq.push(*root);
    visited.insert(serialize(initial));
    
    printf("Initial State:\n");
    printPath(root); // Print the initial state

    while (!pq.empty()) {
        Node min = pq.top();
        pq.pop();
        if (min.cost == 0) {
            printf("Goal state reached:\n");
            printPath(&min);  // Print the goal state
            return;
        }
        
        // Exploring possible moves
        for (int i = 0; i < 4; i++) {
            int newX = min.x + row[i], newY = min.y + col[i];
            if (isSafe(newX, newY)) {
                vector<vector<int>> newMat = min.mat;
                swap(newMat[min.x][min.y], newMat[newX][newY]);
                string key = serialize(newMat);
                if (visited.find(key) == visited.end()) {
                    Node* child = new Node{newMat, newX, newY, calculateCost(newMat, final), min.level + 1, new Node(min)};
                    pq.push(*child);
                    visited.insert(key);
                    
                    // Print the direction and state derived from the move
                    if (i == 0) printf("Moving Down to:\n");
                    if (i == 1) printf("Moving Left to:\n");
                    if (i == 2) printf("Moving Up to:\n");
                    if (i == 3) printf("Moving Right to:\n");

                    printPath(child);  // Print the new state after moving
                }
            }
        }
    }
}

int main() {
    vector<vector<int>> initial(N, vector<int>(N));
    vector<vector<int>> final(N, vector<int>(N));
    int x, y;
    
    printf("Enter the initial state of the puzzle (4x4 grid, with 0 as the empty space):\n");
    for (int i = 0; i < N; i++)
        for (int j = 0; j < N; j++) {
            cin >> initial[i][j];
            if (initial[i][j] == 0) {
                x = i;
                y = j;
            }
        }
        
    printf("Enter the final goal state (4x4 grid):\n");
    for (int i = 0; i < N; i++)
        for (int j = 0; j < N; j++)
            cin >> final[i][j];
    
    solve(initial, final, x, y);
    return 0;
}
