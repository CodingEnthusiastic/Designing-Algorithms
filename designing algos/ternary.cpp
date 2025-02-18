#include <iostream>
#include <cmath>
using namespace std;

double f(double x) {
    return (x - 2) * (x - 2) + 3;
}

double ternarySearch(double left, double right, double epsilon = 1e-7) {
    while (right - left > epsilon) {
        double mid1 = left + (right - left) / 3;
        double mid2 = right - (right - left) / 3;
        if (f(mid1) < f(mid2)) {
            right = mid2;
        } else {
            left = mid1;
        }
    }
    return (left + right) / 2;
}

int main() {
    double left = -10, right = 10;
    double minX = ternarySearch(left, right);
    cout << "Minimum occurs at x = " << minX << endl;
    cout << "Minimum value is f(x) = " << f(minX) << endl;
    return 0;
}
