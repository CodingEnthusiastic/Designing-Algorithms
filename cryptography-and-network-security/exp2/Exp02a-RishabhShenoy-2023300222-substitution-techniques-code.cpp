#include <iostream>
#include <string>
#include <vector>
#include<map>
using namespace std;

class CaesarCipher {
public:
    static const int RANGE = 95; 
    int normalizeKey(int key) 
    {
        key %= RANGE;
        if (key < 0) key += RANGE;
        return key;
    }

    char shiftChar(char ch, int key) 
    {
        if (ch >= 32 && ch <= 126) 
        {
            return 32 + (ch - 32 + key) % RANGE;
        }
        return ch;
    }

    string encrypt(const string &msg, int key) 
    {
        key = normalizeKey(key);
        string result = msg;
        for (size_t i = 0; i < result.size(); i++) 
        {
            result[i] = shiftChar(result[i], key);
        }
        return result;
    }

    string decrypt(const string &msg, int key) 
    {
        key = normalizeKey(key);
        int decryptKey = RANGE - key;
        string result = msg;
        for (size_t i = 0; i < result.size(); i++) 
        {
            result[i] = shiftChar(result[i], decryptKey);
        }
        return result;
    }

    void bruteForce(const string &cipherText) 
    {
        cout << "\nTrying all possible keys from 0 to 94:\n";
        for (int possibleKey = 0; possibleKey < RANGE; possibleKey++) 
        {
            cout << "Key " << possibleKey << ": ";
            for (size_t i = 0; i < cipherText.size(); i++) 
            {
                cout << shiftChar(cipherText[i], RANGE - possibleKey);
            }
            cout << endl;
        }
    }

public:
    void run() {
        cout << "Choose:\n1. Encryption\n2. Decryption\n3. Decrypt without key (brute-force)\n";
        int choice;
        cin >> choice;
        cin.ignore();

        if (choice == 1 || choice == 2) {
            cout << "Enter the message:\n";
            string msg;
            getline(cin, msg);

            int key;
            cout << "Enter key (shift amount): ";
            cin >> key;

            if (choice == 1) {
                cout << "Encrypted message: " << encrypt(msg, key) << endl;
            } else {
                cout << "Decrypted message: " << decrypt(msg, key) << endl;
            }
        }
        else if (choice == 3) {
            cout << "Enter the cipher text:\n";
            string cipherText;
            getline(cin, cipherText);
            bruteForce(cipherText);
        }
        else {
            cout << "Invalid choice!" << endl;
        }
    }
};


class MonoalphabeticCipher {
public:
    string key;  
    map<char, char> encMap, decMap;

    void buildMaps() {
        encMap.clear(); decMap.clear();
        string alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";
        for (int i = 0; i < 26; i++) {
            encMap[alphabet[i]] = key[i];
            decMap[key[i]] = alphabet[i];
        }
    }

public:
    MonoalphabeticCipher(string k) {
        key = k;
        buildMaps();
    }

    string encrypt(const string &msg) {
        string res = "";
        for (char c : msg) {
            if (isalpha(c)) {
                char up = toupper(c);
                res += isupper(c) ? encMap[up] : tolower(encMap[up]);
            } else res += c;
        }
        return res;
    }

    string decrypt(const string &msg) {
        string res = "";
        for (char c : msg) {
            if (isalpha(c)) {
                char up = toupper(c);
                res += isupper(c) ? decMap[up] : tolower(decMap[up]);
            } else res += c;
        }
        return res;
    }
};

class PlayfairCipher {
private:
    char matrix[5][5];
    string key;

    void generateMatrix() {
        string alpha = "ABCDEFGHIKLMNOPQRSTUVWXYZ";
        string temp = "";
        vector<bool> used(26, false);

        for (char c : key) {
            c = toupper(c);
            if (c == 'J') c = 'I';
            if (!used[c - 'A']) {
                temp += c;
                used[c - 'A'] = true;
            }
        }

        for (char c : alpha) {
            if (!used[c - 'A']) {
                temp += c;
                used[c - 'A'] = true;
            }
        }

        int k = 0;
        for (int i = 0; i < 5; i++)
            for (int j = 0; j < 5; j++)
                matrix[i][j] = temp[k++];
    }

    pair<int,int> findChar(char c) {
        if (c == 'J') c = 'I';
        for (int i = 0; i < 5; i++)
            for (int j = 0; j < 5; j++)
                if (matrix[i][j] == c) return {i, j};
        return {-1, -1};
    }

    string processDigraph(string digraph, bool encrypt) {
        auto p1 = findChar(digraph[0]);
        auto p2 = findChar(digraph[1]);
        int r1 = p1.first, c1 = p1.second;
        int r2 = p2.first, c2 = p2.second;

        if (r1 == r2) {
            c1 = (c1 + (encrypt ? 1 : 4)) % 5;
            c2 = (c2 + (encrypt ? 1 : 4)) % 5;
        } else if (c1 == c2) {
            r1 = (r1 + (encrypt ? 1 : 4)) % 5;
            r2 = (r2 + (encrypt ? 1 : 4)) % 5;
        } else {
            swap(c1, c2);
        }
        string res = "";
        res += matrix[r1][c1];
        res += matrix[r2][c2];
        return res;
    }

public:
    PlayfairCipher(string k) {
        key = k;
        generateMatrix();
    }

    string formatText(string msg) {
        string res = "";
        for (char c : msg) {
            if (isalpha(c)) res += toupper(c);
        }
        for (size_t i = 0; i < res.size(); i += 2) {
            if (i + 1 == res.size() || res[i] == res[i + 1]) {
                res.insert(i + 1, "X");
            }
        }
        if (res.size() % 2) res += "X";
        return res;
    }

    string encrypt(string msg) {
        msg = formatText(msg);
        string res = "";
        for (size_t i = 0; i < msg.size(); i += 2) {
            res += processDigraph(msg.substr(i, 2), true);
        }
        return res;
    }

    string decrypt(string msg) {
        string res = "";
        for (size_t i = 0; i < msg.size(); i += 2) {
            res += processDigraph(msg.substr(i, 2), false);
        }
        return res;
    }
};

class HillCipher {
public:
    int key[2][2];

    int mod26(int x) { return (x % 26 + 26) % 26; }

    int determinant() {
        return mod26(key[0][0] * key[1][1] - key[0][1] * key[1][0]);
    }

    int modInverse(int a) {
        for (int x = 1; x < 26; x++) {
            if (mod26(a * x) == 1) return x;
        }
        return -1;
    }

    vector<int> multiply(vector<int> v, int k[2][2]) {
        vector<int> res(2);
        res[0] = mod26(k[0][0] * v[0] + k[0][1] * v[1]);
        res[1] = mod26(k[1][0] * v[0] + k[1][1] * v[1]);
        return res;
    }

public:
    HillCipher(int k[2][2]) {
        key[0][0] = k[0][0]; key[0][1] = k[0][1];
        key[1][0] = k[1][0]; key[1][1] = k[1][1];
    }

    string encrypt(string msg) {
        string res = "";
        if (msg.size() % 2) msg += 'X';
        for (size_t i = 0; i < msg.size(); i += 2) {
            vector<int> v = {msg[i] - 'A', msg[i+1] - 'A'};
            auto r = multiply(v, key);
            res += char(r[0] + 'A');
            res += char(r[1] + 'A');
        }
        return res;
    }

    string decrypt(string msg) {
        int det = determinant();
        int invDet = modInverse(det);
        if (invDet == -1) return "Key not invertible!";
        
        int invKey[2][2];
        invKey[0][0] = mod26( key[1][1] * invDet);
        invKey[0][1] = mod26(-key[0][1] * invDet);
        invKey[1][0] = mod26(-key[1][0] * invDet);
        invKey[1][1] = mod26( key[0][0] * invDet);

        string res = "";
        for (size_t i = 0; i < msg.size(); i += 2) {
            vector<int> v = {msg[i] - 'A', msg[i+1] - 'A'};
            auto r = multiply(v, invKey);
            res += char(r[0] + 'A');
            res += char(r[1] + 'A');
        }
        return res;
    }
};


class PolyalphabeticCipher {
private:
    string key;

    char shiftChar(char c, char k, bool encrypt) {
        if (!isalpha(c)) return c;
        int base = isupper(c) ? 'A' : 'a';
        int keyShift = toupper(k) - 'A';
        if (!encrypt) keyShift = 26 - keyShift;
        return base + (c - base + keyShift) % 26;
    }

public:
    PolyalphabeticCipher(string k) {
        key = k;
    }

    string encrypt(const string &msg) {
        string res = "";
        int j = 0;
        for (char c : msg) {
            res += shiftChar(c, key[j % key.size()], true);
            if (isalpha(c)) j++;
        }
        return res;
    }

    string decrypt(const string &msg) {
        string res = "";
        int j = 0;
        for (char c : msg) {
            res += shiftChar(c, key[j % key.size()], false);
            if (isalpha(c)) j++;
        }
        return res;
    }
};

int main() {
    int choice;
    do {
        cout << "\nSubstitution Ciphers Menu in Rishabh's Hacking Arena\n";
        cout << "1. Caesar Cipher\n";
        cout << "2. Monoalphabetic Cipher\n";
        cout << "3. Playfair Cipher\n";
        cout << "4. Hill Cipher\n";
        cout << "5. Polyalphabetic Cipher (Vigenere)\n";
        cout << "6. Exit\n";
        cout << "Enter your choice: ";
        cin >> choice;
        cin.ignore();

        if (choice == 1) {
            int action;
            cout << "Choose:\n1. Encrypt\n2. Decrypt\n3. Brute-force Decrypt\n";
            cin >> action;
            cin.ignore();

            if (action == 1 || action == 2) 
            {
                string msg;
                cout << "Enter message: ";
                getline(cin, msg);
                int key;
                cout << "Enter shift key: ";
                cin >> key;
                CaesarCipher cc;
                if (action == 1)
                    cout << "Encrypted: " << cc.encrypt(msg, key) << endl;
                else
                    cout << "Decrypted: " << cc.decrypt(msg, key) << endl;
            } 
            else if (action == 3) 
            {
                string cipherText;
                cout << "Enter cipher text: ";
                getline(cin, cipherText);
                CaesarCipher cc;
                cc.bruteForce(cipherText);
            } 
            else 
            {
                cout << "Invalid choice!\n";
            }
        }
        else if (choice == 2) 
        {
            int action;
            cout << "Choose:\n1. Encrypt\n2. Decrypt\n";
            cin >> action;
            cin.ignore();

            string msg;
            cout << "Enter message: ";
            getline(cin, msg);
            string key;
            cout << "Enter 26-letter substitution key (A–Z): ";
            getline(cin, key);
            MonoalphabeticCipher mc(key);

            if (action == 1)
                cout << "Encrypted: " << mc.encrypt(msg) << endl;
            else if (action == 2)
                cout << "Decrypted: " << mc.decrypt(msg) << endl;
            else
                cout << "Invalid choice!\n";
        }
        else if (choice == 3) 
        {
            int action;
            cout << "Choose:\n1. Encrypt\n2. Decrypt\n";
            cin >> action;
            cin.ignore();

            string msg;
            cout << "Enter message: ";
            getline(cin, msg);
            string key;
            cout << "Enter Playfair key: ";
            getline(cin, key);
            PlayfairCipher pc(key);

            if (action == 1)
                cout << "Encrypted: " << pc.encrypt(msg) << endl;
            else if (action == 2)
                cout << "Decrypted: " << pc.decrypt(msg) << endl;
            else
                cout << "Invalid choice!\n";
        }
        else if (choice == 4) 
        {
            int action;
            cout << "Choose:\n1. Encrypt\n2. Decrypt\n";
            cin >> action;
            cin.ignore();

            string msg;
            cout << "Enter message (uppercase only): ";
            getline(cin, msg);
            int key[2][2];
            cout << "Enter 2x2 key matrix (row-wise): ";
            cin >> key[0][0] >> key[0][1] >> key[1][0] >> key[1][1];
            cin.ignore();
            HillCipher hc(key);

            if (action == 1)
                cout << "Encrypted: " << hc.encrypt(msg) << endl;
            else if (action == 2)
                cout << "Decrypted: " << hc.decrypt(msg) << endl;
            else
                cout << "Invalid choice!\n";
        }
        else if (choice == 5) 
        {
            int action;
            cout << "Choose:\n1. Encrypt\n2. Decrypt\n";
            cin >> action;
            cin.ignore();

            string msg;
            cout << "Enter message: ";
            getline(cin, msg);
            string key;
            cout << "Enter keyword for Vigenere: ";
            getline(cin, key);
            PolyalphabeticCipher pc(key);

            if (action == 1)
                cout << "Encrypted: " << pc.encrypt(msg) << endl;
            else if (action == 2)
                cout << "Decrypted: " << pc.decrypt(msg) << endl;
            else
                cout << "Invalid choice!\n";
        }
        else if (choice == 6) 
        {
            cout << "Exiting program. Goodbye!\n";
        }
        else 
        {
            cout << "Invalid choice! Try again.\n";
        }

    } while (choice != 6);

    return 0;
}
