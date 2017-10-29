#include <string>
using namespace std;

class CppTile{
public:
	CppTile();
	CppTile(string suit, string value);
	//void set_suit(string suit);
	//void set_value(string value);
	string get_suit();
	string get_value();
	bool operator<(const CppTile& other);
private:
	string _suit, _value;
};