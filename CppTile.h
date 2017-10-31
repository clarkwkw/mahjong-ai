#include <string>
using namespace std;

class CppTile{
public:
	CppTile();
	CppTile(string suit, string value);
	string get_suit();
	string get_value();
	string as_string();
	bool operator<(const CppTile& other);
	string generate_neighbor_tile_str(int offset);
	int get_i_value();
	
	string _suit, _value;
private:
	bool _is_digit;
	int _i_value;
};