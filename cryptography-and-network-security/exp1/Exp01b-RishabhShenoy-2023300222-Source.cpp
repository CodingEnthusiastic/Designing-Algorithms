#include <iostream>
#include <vector>
#include <string>
#include <algorithm>
#include <cctype>

using namespace std;
using ll=long long;
using u128 = uint64_t; 
using i128 = int64_t; 

string stringconvert(u128 x) 
{
    if(x==0) 
    {
        return "0";
    }
    string s;
    while (x > 0) 
    {
        int d=x%10;
        s.push_back('0'+d);
        x=x/10;
    }
    reverse(s.begin(), s.end());
    return s;
}

long long modulusnormal(long long a, long long m) 
{
    long long r=a%m;
    if (r < 0)
    {
        r=r+m;
    }
    return r;
}

long long egcd(long long a, long long b, long long &x, long long &y) 
{
    if(b == 0) 
    {
        x = 1; 
        y = 0;
        if(a>=0)
        {
            return a;
        }
        return -a;
    }
    long long x1, y1;
    long long g = egcd(b, a % b, x1, y1);
    x = y1;
    y = x1 - (a / b) * y1;
    return g;
}

pair<bool,long long>inversemodulo(long long a, long long m) 
{
    a = modulusnormal(a, m);
    long long x, y;
    long long g = egcd(a, m, x, y);
    if (g != 1) return make_pair(false, 0);
    long long inv = modulusnormal(x, m);
    return make_pair(true, inv);
}

long long stringmodulus(const string &s, long long mod) 
{
    long long r = 0;
    int i = 0; bool neg = false;
    while (i < (int)s.size() && isspace((unsigned char)s[i])) ++i;
    if (i < (int)s.size() && (s[i] == '+' || s[i] == '-')) 
    {
        neg = (s[i] == '-');
        ++i;
    }
    for (; i < (int)s.size(); ++i) 
    {
        char c = s[i];
        if (c < '0' || c > '9') break;
        int d = c - '0';
        r = ((r * 10LL) + d) % mod;
    }
    if (neg) 
    {
        r = modulusnormal(-r, mod);
    }
    return r;
}

int main() 
{
    cout<<"\n\nWelcome to Rishabh's CRT Theorem : \n\n";
    cout << "Enter k (number of pairwise-coprime moduli): ";
    int k; 
    if (!(cin >> k)) 
    {
        return 0;
    }
    vector<long long> m(k);
    cout << "Enter m1..mk (pairwise coprime):\n";
    for (int i = 0; i < k; i++) 
    {
        cin >> m[i];
    }
    u128 M = 1;
    for(int i = 0; i < k; i++) 
    {
        M *= (u128)m[i];
    }
    vector<u128> Mi(k);
    vector<long long> invMi(k);
    for (int i = 0; i < k; i++) 
    {
        u128 Mi_u = M / (u128)m[i];
        Mi[i] = Mi_u;
        long long Mi_mod_mi = (long long)(Mi_u % (u128)m[i]);
        pair<bool,long long> res = inversemodulo(Mi_mod_mi, m[i]);
        if (!res.first) 
        {
            cout << "Error: not invertible\n";
            return 0;
        }
        invMi[i] = res.second;
    }

    while (true) 
    {
        cout << "\nMenu Options present in my application:\n";
        cout << "1) Addition\n";
        cout << "2) Subtraction\n";
        cout << "3) Multiplication\n";
        cout << "4) Division\n";
        cout << "5) Quit\n";
        cout << "Choose option: ";
        int op; 
        if (!(cin >> op)) 
        {
            break;
        }
        if (op == 5) 
        {
            break;
        }
        cout << "Enter A: ";
        string A; 
        cin >> A;
        cout << "Enter B: ";
        string B; 
        cin >> B;

        vector<long long> a(k), b(k), c(k);
        for (int i = 0; i < k; i++) 
        {
            a[i] = stringmodulus(A, m[i]);
            b[i] = stringmodulus(B, m[i]);
        }

        if (op == 1) 
        {
            for (int i = 0; i < k; i++) 
            {
                c[i] = (a[i] + b[i]) % m[i];
            }
        } 
        else if (op == 2) 
        {
            for (int i = 0; i < k; i++) 
            {
                c[i] = modulusnormal(a[i] - b[i], m[i]);
            }
        } 
        else if (op == 3) 
        {
            for (int i = 0; i < k; i++) 
            {
                c[i] = (long long)((a[i] * b[i]) % m[i]);
            }
        } 
        else if (op == 4) 
        {
            bool ok = true;
            for (int i = 0; i < k; i++) 
            {
                pair<bool,long long> inv = inversemodulo(b[i], m[i]);
                if (!inv.first) 
                ok = false;
                else 
                c[i] = (long long)((a[i] * inv.second) % m[i]);
            }
            if (!ok) 
            {
                cout << "Division undefined\n";
                continue;
            }
        } 
        else 
        {
            cout << "Invalid option\n";
            continue;
        }

        cout << "Result residues: ";
        for (int i = 0; i < k; i++) 
        {
            cout << c[i] << " mod " << m[i] << (i==k-1?"":", ");
        }
        cout << "\n";

        u128 Cres = 0;
        for (int i = 0; i < k; i++) 
        {
            long long ci = modulusnormal(c[i], m[i]);
            long long t = (long long)((ci * invMi[i]) % m[i]);
            Cres += Mi[i] * (u128)t;
            Cres %= M;
        }
        Cres %= M;
        cout << "M = " << stringconvert(M) << "\n";
        cout << "Final C (mod M) = " << stringconvert(Cres) << "\n";
    }
    return 0;
}

// Exp01b-IssacNewton-202500145-Source.py