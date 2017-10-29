#include "CppTile.h"
#include <string>
using namespace std;

CppTile::CppTile(string suit, string value){
	this->_suit = suit;
	this->_value = value;
}

string CppTile::get_suit(){
	return this->_suit;
}

string CppTile::get_value(){
	return this->_value;
}

bool CppTile:: operator<(const CppTile &other){
	return this->_suit < other._suit || (this->_value < other._value);
}