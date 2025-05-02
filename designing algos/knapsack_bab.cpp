#include <iostream>
#include <queue>
#include <vector>
#include <algorithm>
using namespace std;

struct Item {
    int weight, value;
    double ratio;
};

struct Node {
    int level, profit, weight;
    double bound;
};

bool cmp(Item a, Item b) {
    return a.ratio > b.ratio;
}

double bound(Node u, int n, int W, vector<Item>& items) {
    if (u.weight >= W) return 0;
    double profit_bound = u.profit;
    int j = u.level + 1;
    int totweight = u.weight;
    while (j < n && totweight + items[j].weight <= W) {
        totweight += items[j].weight;
        profit_bound += items[j].value;
        j++;
    }
    if (j < n) {
        profit_bound += (W - totweight) * items[j].ratio;
    }
    return profit_bound;
}

int knapsack(int W, vector<Item>& items, int n) {
    sort(items.begin(), items.end(), cmp);
    queue<Node> Q;
    Node u, v;
    u.level = -1;
    u.profit = u.weight = 0;
    u.bound = bound(u, n, W, items);
    Q.push(u);
    int maxProfit = 0;
    while (!Q.empty()) {
        u = Q.front();
        Q.pop();
        
        printf("Processing node at level %d: Profit = %d, Weight = %d, Bound = %.2f\n", u.level, u.profit, u.weight, u.bound);
        
        if (u.level == n - 1) continue;

        v.level = u.level + 1;
        v.weight = u.weight + items[v.level].weight;
        v.profit = u.profit + items[v.level].value;

        printf("Consider node with item %d (value = %d, weight = %d)\n", v.level, items[v.level].value, items[v.level].weight);

        if (v.weight <= W && v.profit > maxProfit)
            maxProfit = v.profit;

        v.bound = bound(v, n, W, items);
        if (v.bound > maxProfit) {
            printf("Node with item %d added to queue\n", v.level);
            Q.push(v);
        }

        v.weight = u.weight;
        v.profit = u.profit;
        v.bound = bound(v, n, W, items);
        if (v.bound > maxProfit) {
            printf("Node without item %d added to queue\n", v.level);
            Q.push(v);
        }
    }
    return maxProfit;
}

int main() {
    cout << "Enter n and W: ";
    int n, W;
    cin >> n >> W;
    vector<Item> items(n);
    
    printf("For %d items, enter value and weight:\n", n);
    for (int i = 0; i < n; i++) {
        cin >> items[i].value >> items[i].weight;
        items[i].ratio = (double)items[i].value / items[i].weight;
    }
    cout << "Maximum profit: " << knapsack(W, items, n) << endl;
    return 0;
}
