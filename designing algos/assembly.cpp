#include <iostream>
#include <vector>
#include <algorithm>

int min(int a, int b) {
    return (a < b) ? a : b;
}

void assemblyLineScheduling(int n, int a1[], int a2[], int t1[], int t2[], int e1, int e2, int x1, int x2) {
    int f1[n], f2[n];
    int l1[n], l2[n];
    int result, last;

    f1[0] = e1 + a1[0];
    f2[0] = e2 + a2[0];

    for (int j = 1; j < n; j++) {
        f1[j] = min(f1[j - 1] + a1[j], f2[j - 1] + t2[j - 1] + a1[j]);
        l1[j] = (f1[j - 1] + a1[j] < f2[j - 1] + t2[j - 1] + a1[j]) ? 1 : 2;

        f2[j] = min(f2[j - 1] + a2[j], f1[j - 1] + t1[j - 1] + a2[j]);
        l2[j] = (f2[j - 1] + a2[j] < f1[j - 1] + t1[j - 1] + a2[j]) ? 2 : 1;
    }

    result = min(f1[n - 1] + x1, f2[n - 1] + x2);
    last = (f1[n - 1] + x1 < f2[n - 1] + x2) ? 1 : 2;

    std::cout << "Minimum time required: " << result << std::endl;

    std::cout << "Optimal path:" << std::endl;
    int i = last;
    std::cout << "Line " << i << ", Station " << n << std::endl;
    for (int j = n - 1; j >= 1; j--) {
        if (i == 1) {
            i = l1[j];
        } else {
            i = l2[j];
        }
        std::cout << "Line " << i << ", Station " << j << std::endl;
    }
}

int main() {
    int n = 4;
    int a1[] = {4, 5, 3, 2};
    int a2[] = {2, 10, 1, 4};
    int t1[] = {0, 7, 4, 5};
    int t2[] = {0, 9, 2, 8};
    int e1 = 10, e2 = 12;
    int x1 = 18, x2 = 7;

    assemblyLineScheduling(n, a1, a2, t1, t2, e1, e2, x1, x2);

    return 0;
}

