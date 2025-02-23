#include <iostream>
#include <vector>
#include <queue>
using namespace std;
using ll=long long;

struct Node {
    char data;
    int freq;
    Node *left, *right;
    Node(char d, int f) : data(d), freq(f), left(nullptr), right(nullptr) {}
};

struct Compare {
    bool operator()(Node* l, Node* r) {
        return l->freq > r->freq;
    }
};

void printCodes(Node* root, vector<int>& code) {
    if (!root) return;
    if (!root->left && !root->right) {
        cout << root->data << ": ";
        for (int bit : code) cout << bit;
        cout << endl;
    }
    if (root->left) {
        code.push_back(0);
        printCodes(root->left, code);
        code.pop_back();
    }
    if (root->right) {
        code.push_back(1);
        printCodes(root->right, code);
        code.pop_back();
    }
}

Node* buildHuffmanTree(vector<char>& data, vector<int>& freq) {
    priority_queue<Node*, vector<Node*>, Compare> minHeap;
    for (size_t i = 0; i < data.size(); ++i)
        minHeap.push(new Node(data[i], freq[i]));
    while (minHeap.size() > 1) {
        Node* left = minHeap.top(); minHeap.pop();
        Node* right = minHeap.top(); minHeap.pop();
        Node* top = new Node('$', left->freq + right->freq);
        top->left = left;
        top->right = right;
        minHeap.push(top);
    }
    return minHeap.top();
}

int main() {
    vector<char> arr = {'a', 'b', 'c', 'd', 'e', 'f'};
    vector<int> freq = {5, 9, 12, 13, 16, 45};
    
    Node* root = buildHuffmanTree(arr, freq);
    vector<int> huffCode;
    
    cout << "Huffman Codes:\n";
    printCodes(root, huffCode);
    return 0;
}
