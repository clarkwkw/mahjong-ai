#include "CppTile.h"
#include <string>
using namespace std;

CppTile::CppTile(){
	
}
CppTile::CppTile(string suit, string value){
	this->_suit = suit;
	this->_value = value;
	this->_is_digit = isdigit(value[0]);
	this->_i_value = 0;
	
	if(this->_is_digit){
		this->_i_value = stoi(value.c_str());
	}
}

string CppTile::get_suit(){
	return this->_suit;
}

string CppTile::get_value(){
	return this->_value;
}

int CppTile::get_i_value(){
	return this->_i_value;
} 

string CppTile::as_string(){
	return this->_suit+"-"+this->_value;
}

string CppTile::generate_neighbor_tile_str(int offset){
	if(!this->_is_digit) return "";

	if(this->_i_value + offset > 9 || this->_i_value + offset < 1)return "";

	return this->_suit + to_string(this->_i_value + offset);
}

bool CppTile:: operator<(const CppTile &other){
	return this->_suit < other._suit || (this->_value < other._value);
}