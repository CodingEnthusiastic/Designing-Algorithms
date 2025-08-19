#include<bits/stdc++.h>
using namespace std;
#define ll long long
int main()
{
    cout<<"Welcome to Rishabh's Math interface\n";
    do
    {
        
        cout<<"\nEnter the choice which operation you would love to perform : \n1.Euclidean\n2.Extnded Euclidean\n3.Euclidean algorithm [Tabular Method] for GCD and MI \n4.Exit .. \nAny other choice will result into exit\n";
        int choice;
        cin>>choice;

        //euclidian algo
        if(choice==1)
        {
            ll a,b;
            cout<<"\nEnter the value of a and b for Euclidean algorithm\n";
            cin>>a;
            cin>>b;
            ll q,r;
            q=a;
            r=b;
            if(a<b)
            {
                swap(a,b);
            }
            ll counter=1;
            cout<<"\nStep\t Q\t A\t B\t R\n";
            while(b!=0)
            {
                cout<<counter<<"\t ";
                cout<<a/b<<"\t ";
                cout<<a<<"\t ";
                cout<<b<<"\t ";
                cout<<a%b<<"\n";
                ll temp=b;
                b=a%b;
                a=temp;
                counter++;
            }
            cout<<"GCD of "<<q<<" and "<<r<<" is "<<a<<"\n";
            // euclidean();
        }
        //extended for mi and gcd
        else if(choice==3)
        {
            ll a,b;
            cout<<"\nEnter the value of a and b for Extended Euclidean algorithm to find gcd and mi(mult inverse)\n";
            cin>>a;
            cin>>b;
            ll q,r;
            q=a;
            r=b;
            if(a<b)
            {
                swap(a,b);
            }
            ll counter=1;
            ll t1=0;
            ll t2=1;
            ll t=0;
            cout<<"\nStep\t Q\t A\t B\t R\t T1\t T2\t T\n";
            while(b!=0)
            {
                cout<<counter<<"\t ";
                cout<<a/b<<"\t ";
                ll q=a/b;
                cout<<a<<"\t ";
                cout<<b<<"\t ";
                cout<<a%b<<"\t ";
                cout<<t1<<"\t ";
                cout<<t2<<"\t ";
                ll temp=b;
                b=a%b;
                a=temp;
                t=t1-(t2*q);
                t1=t2;
                t2=t;
                cout<<t<<endl;
                counter++;
            }

            cout<<"The GCD of the algorithm is "<<a<<"\n";
            if(a>1)
            {
                cout<<"The numbers have gcd > 1 , so the multiplicative inverse does not exists\n";
            }
            else
            cout<<"The multiplicative inverse of "<<r<<" is "<<t1<<"\n";


        }
        else if(choice==2)
        {
            ll a,b;
            // cin>>a>>b;
            cout<<"\nEnter the value of a and b for Extended Euclidean algorithm to find gcd and mi(mult inverse)\n";
            cin>>a;
            cin>>b;
            ll q,r;
            q=a;
            r=b;
            if(a<b)
            {
                swap(a,b);
            }
            ll counter=1;
            ll t1=0;
            ll t2=1;
            ll t=0;
            ll s1=1;
            ll s2=0;
            ll s=0;
            cout<<"\nStep\t Q\t A\t B\t R\t T1\t T2\t T\t S1\t S2\t S\n";
            while(b!=0)
            {
                cout<<counter<<"\t ";
                cout<<a/b<<"\t ";
                ll q=a/b;
                cout<<a<<"\t ";
                cout<<b<<"\t ";
                cout<<a%b<<"\t ";
                cout<<t1<<"\t ";
                cout<<t2<<"\t ";
                
                ll temp=b;
                b=a%b;
                a=temp;
                t=t1-(t2*q);
                s=s1-(s2*q);

                t1=t2;
                t2=t;
                cout<<t<<"\t ";
                cout<<s1<<"\t ";
                cout<<s2<<"\t ";
                s1=s2;
                s2=s;
                cout<<s<<endl;
                counter++;
            }

            cout<<"The GCD of two numbers is : "<<a<<endl;
            if(a>1)
            {
                cout<<"The numbers have gcd > 1 , so the multiplicative inverse does not exists\n";
            }
            else
            cout<<"The Multiplicative inverse of "<<r<<" is : "<<t1<<endl;
            cout<<"S2 = "<<s2<<endl;
            
        }
        else
        {
            break;
        }
    } while (true);
    
    return 0;
}
