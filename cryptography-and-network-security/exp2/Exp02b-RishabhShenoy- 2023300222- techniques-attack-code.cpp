#include <bits/stdc++.h>
using namespace std;

string toUpperAlphaOnly(const string &s) {
    string out;
    for (char c : s) if (isalpha((unsigned char)c)) out.push_back(toupper((unsigned char)c));
    return out;
}

string toUpperAlphaPlayfair(const string &s) {
    string out;
    for (char c : s) if (isalpha((unsigned char)c)) {
        char U = toupper((unsigned char)c);
        if (U == 'J') U = 'I';
        out.push_back(U);
    }
    return out;
}

string padIfOdd(const string &s, char padChar='X') {
    string out = s;
    if (out.size() % 2 == 1) out.push_back(padChar);
    return out;
}

int mod26(int x) {
    x %= 26; if (x < 0) x += 26; return x;
}

int invMod(int a, int m=26) {
    a = (a % m + m) % m;
    for (int x = 1; x < m; ++x) if ((a * x) % m == 1) return x;
    return -1;
}

void caesarBruteForce(const string &cipher) {
    cout << "\n=== Caesar Cipher Brute-Force ===\n";
    const int RANGE = 95; 
    for (int k = 0; k < RANGE; ++k) {
        string res;
        for (char ch : cipher) {
            if (ch >= 32 && ch <= 126) res.push_back( char(32 + (ch - 32 + RANGE - k) % RANGE) );
            else res.push_back(ch);
        }
        cout << "Key " << k << ": " << res << "\n";
    }
}

void monoalphabeticDeduce(const string &plainRaw, const string &cipherRaw) {
    cout << "\n=== Monoalphabetic Key Deduction ===\n";

    string plain = toUpperAlphaOnly(plainRaw);
    string cipher = toUpperAlphaOnly(cipherRaw);

    bool cipherLooksLikeKey = (cipherRaw.size() == 26 && count_if(cipherRaw.begin(), cipherRaw.end(),
        [](char c){ return isalpha((unsigned char)c); }) == 26 && cipherRaw.find(' ') == string::npos);

    if (cipherLooksLikeKey) {
        string key;
        for (char c : cipherRaw) key.push_back(toupper((unsigned char)c));
        cout << "Detected direct 26-letter mapping (treated as key):\n";
        cout << key << "\n";
        return;
    }

    map<char,char> p2c;
    map<char,char> c2p;
    size_t n = min(plain.size(), cipher.size());
    for (size_t i = 0; i < n; ++i) {
        char p = plain[i], c = cipher[i];
        if (!isalpha((unsigned char)p) || !isalpha((unsigned char)c)) continue;
        if (!p2c.count(p)) p2c[p] = c;
        else if (p2c[p] != c) {
            cerr << "Conflict in plain->cipher mapping: " << p << " -> " << c << " (was " << p2c[p] << ")\n";
        }
        if (!c2p.count(c)) c2p[c] = p;
    }

    string key = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";
    for (int i = 0; i < 26; ++i) {
        char letter = key[i];
        if (p2c.count(letter)) key[i] = p2c[letter];
        else key[i] = '?';
    }

    cout << "Partial key (A->?, B->?, ... printed as 26-letter string where index 0=A):\n";
    cout << key << "\n";

    cout << "Mappings found:\n";
    for (auto &kv : p2c) cout << kv.first << " -> " << kv.second << "   ";
    cout << "\nUnmapped plaintext letters: ";
    for (char c='A'; c<='Z'; ++c) if (!p2c.count(c)) cout << c;
    cout << "\n";
}

string shortest_period(const string &s) {
    int n = s.size();
    for (int len = 1; len <= n; ++len) {
        if (n % len != 0) continue;
        bool ok = true;
        for (int i = 0; i < n; ++i) if (s[i] != s[i % len]) { ok = false; break; }
        if (ok) return s.substr(0, len);
    }
    for (int len = 1; len <= n; ++len) {
        bool ok = true;
        for (int i = 0; i < n; ++i) if (s[i] != s[i % len]) { ok = false; break; }
        if (ok) return s.substr(0, len);
    }
    return s;
}

void vigenereDeduce(const string &plainRaw, const string &cipherRaw) {
    cout << "\n=== Vigenere Key Deduction ===\n";
    string plain = toUpperAlphaOnly(plainRaw);
    string cipher = toUpperAlphaOnly(cipherRaw);
    string keySeq;
    size_t n = min(plain.size(), cipher.size());
    for (size_t i = 0; i < n; ++i) {
        char p = plain[i], c = cipher[i];
        if (!isalpha((unsigned char)p) || !isalpha((unsigned char)c)) continue;
        int shift = mod26((c - 'A') - (p - 'A'));
        keySeq.push_back(char('A' + shift));
    }
    if (keySeq.empty()) { cout << "No alpha pairs to deduce key.\n"; return; }
    cout << "Key sequence (per letter): " << keySeq << "\n";
    string small = shortest_period(keySeq);
    cout << "Suggested shortest repeating key (detected period): " << small << "\n";
}

void playfairDeduce(const string &plainRaw, const string &cipherRaw) {
    cout << "\n=== Playfair Cipher Digraph Mapping & Partial Suggestion ===\n";
    string plain = toUpperAlphaPlayfair(plainRaw);
    string cipher = toUpperAlphaPlayfair(cipherRaw);

    size_t n = min(plain.size(), cipher.size());
    string pclean = plain.substr(0, n);
    string cclean = cipher.substr(0, n);
    if (pclean.size() % 2 == 1) pclean.push_back('X');
    if (cclean.size() % 2 == 1) cclean.push_back('X');

    cout << "\nDigraph pairs (plaintext -> ciphertext):\n";
    map<char,set<char>> p2c;
    map<char,set<char>> c2p;
    for (size_t i = 0; i < min(pclean.size(), cclean.size()); i += 2) {
        string pd = pclean.substr(i, min<size_t>(2, pclean.size()-i));
        string cd = cclean.substr(i, min<size_t>(2, cclean.size()-i));
        cout << pd << " -> " << cd << "\n";
        for (size_t k = 0; k < pd.size() && k < cd.size(); ++k) {
            p2c[pd[k]].insert(cd[k]);
            c2p[cd[k]].insert(pd[k]);
        }
    }

    string letters = "ABCDEFGHIKLMNOPQRSTUVWXYZ";
    cout << "\nPartial single-letter suggestions (plaintext letter -> possible cipher letters):\n";
    for (char L : letters) {
        cout << L << "->";
        if (p2c.count(L)) {
            bool first = true;
            for (char x : p2c[L]) { if (!first) cout<<","; cout<<x; first=false; }
        } else cout << "?";
        cout << "  ";
    }
    cout << "\n\nAnd reverse (cipher letter -> possible plaintext letters):\n";
    for (char L : letters) {
        cout << L << "->";
        if (c2p.count(L)) {
            bool first = true;
            for (char x : c2p[L]) { if (!first) cout<<","; cout<<x; first=false; }
        } else cout << "?";
        cout << "  ";
    }
    cout << "\n\nNote: These are single-letter constraints; use multiple messages to fill the 5x5 table.\n";
}

bool trySolveHill2x2(const vector<pair<int,int>>& pvecs, const vector<pair<int,int>>& cvecs,
                     vector<vector<int>>& outK) {
    int m = pvecs.size();
    for (int i = 0; i < m; ++i) {
        for (int j = i+1; j < m; ++j) {
            int P00 = pvecs[i].first, P01 = pvecs[j].first;
            int P10 = pvecs[i].second, P11 = pvecs[j].second;
            int det = mod26(P00 * P11 - P01 * P10);
            int invdet = invMod(det, 26);
            if (invdet == -1) continue; 

            int invP00 = mod26(invdet * P11);
            int invP01 = mod26(invdet * (-P01));
            int invP10 = mod26(invdet * (-P10));
            int invP11 = mod26(invdet * P00);

            int C00 = cvecs[i].first, C01 = cvecs[j].first;
            int C10 = cvecs[i].second, C11 = cvecs[j].second;

            vector<vector<int>> K(2, vector<int>(2));
            K[0][0] = mod26(C00 * invP00 + C01 * invP10);
            K[0][1] = mod26(C00 * invP01 + C01 * invP11);
            K[1][0] = mod26(C10 * invP00 + C11 * invP10);
            K[1][1] = mod26(C10 * invP01 + C11 * invP11);

            bool valid = true;
            for (size_t t = 0; t < pvecs.size(); ++t) {
                int x0 = pvecs[t].first, x1 = pvecs[t].second;
                int y0 = mod26(K[0][0] * x0 + K[0][1] * x1);
                int y1 = mod26(K[1][0] * x0 + K[1][1] * x1);
                if (y0 != cvecs[t].first || y1 != cvecs[t].second) { valid = false; break; }
            }
            if (valid) {
                outK = K;
                return true;
            }
        }
    }
    return false;
}

void hillDeduce(const string &plainRaw, const string &cipherRaw) {
    cout << "\n=== Hill Cipher 2x2 Mapping & Attempt Key Recovery ===\n";
    string plain = toUpperAlphaOnly(plainRaw);
    string cipher = toUpperAlphaOnly(cipherRaw);

    if (plain.size() % 2 == 1) plain.push_back('X');
    if (cipher.size() % 2 == 1) cipher.push_back('X');

    size_t n = min(plain.size(), cipher.size());
    vector<pair<int,int>> pvecs, cvecs;
    cout << "\nPairs (plaintext -> ciphertext):\n";
    for (size_t i = 0; i + 1 < n; i += 2) {
        string pd = plain.substr(i, 2);
        string cd = cipher.substr(i, 2);
        cout << pd << " -> " << cd << "\n";
        pvecs.emplace_back(pd[0]-'A', pd[1]-'A');
        cvecs.emplace_back(cd[0]-'A', cd[1]-'A');
    }

    if (pvecs.size() < 2) {
        cout << "Need at least two plaintext-ciphertext digraph pairs to attempt 2x2 key recovery.\n";
        return;
    }

    vector<vector<int>> K;
    bool ok = trySolveHill2x2(pvecs, cvecs, K);
    if (ok) {
        cout << "\nRecovered 2x2 key matrix (mod 26):\n";
        cout << "[[" << K[0][0] << ", " << K[0][1] << "],\n";
        cout << " [" << K[1][0] << ", " << K[1][1] << "]]\n";
    } else {
        cout << "\nCould not find an invertible plaintext pair or consistent key from pairs provided.\n";
        cout << "Try providing more independent digraphs (non-collinear mod26) or different pairs.\n";
    }
}


int main() {
    // ios::sync_with_stdio(false);
    // cin.tie(nullptr);
    int choice;
    do {
        cout << "\nHack in Rishabh Playground--Substitution Ciphers Brute-Force Menu =====\n";
        cout << "1. Caesar Cipher\n";
        cout << "2. Monoalphabetic Cipher\n";
        cout << "3. Playfair Cipher\n";
        cout << "4. Hill Cipher\n";
        cout << "5. Polyalphabetic Cipher (Vigenere)\n";
        cout << "6. Exit\n";
        cout << "Enter your choice: ";
        if (!(cin >> choice)) return 0;
        cin.ignore(numeric_limits<streamsize>::max(), '\n');

        if (choice >= 1 && choice <= 5) {
            string plain, cipher;

            if (choice != 1) {
                cout << "Enter plain text: ";
                getline(cin, plain);
            }
            cout << "Enter cipher text: ";
            getline(cin, cipher);

            switch (choice) {
                case 1: caesarBruteForce(cipher); break;
                case 2: monoalphabeticDeduce(plain, cipher); break;
                case 3: playfairDeduce(plain, cipher); break;
                case 4: hillDeduce(plain, cipher); break;
                case 5: vigenereDeduce(plain, cipher); break;
            }
        } else if (choice == 6) {
            cout << "Exiting program.\n";
        } else {
            cout << "Invalid choice! Try again.\n";
        }
    } while (choice != 6);

    return 0;
}
