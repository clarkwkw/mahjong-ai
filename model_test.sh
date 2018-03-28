#!/usr/bin/env bash

if [ "$#" -ne 2 ]; then
	echo "usage: sh model_test.sh [MODEL] [OUTPUT_PREFIX]"
	exit 1
fi

MODEL=$1
MODEL_SHORT=$2
H_MODELS=("heuristics1" "heuristics2" "heuristics3")
H_MODELS_SHORT=("h1" "h2" "h3")
PYVER="3"

eval "python${PYVER} test.py ai_battle ${MODEL} rand rand rand > ${MODEL_SHORT}_vs_3r.txt"

for ((i=0; i<${#H_MODELS[@]}; i++));
	do
	for ((j=1; j<3; j++));
		do
		opponents=("rand" "rand" "rand")
		for ((k=0; k<j; k++));
		do
			opponents[k]=${H_MODELS[i]}
		done
		rand_count=$((3-j))
		eval "python${PYVER} test.py ai_battle ${MODEL} ${opponents[0]} ${opponents[1]} ${opponents[2]} > ${MODEL_SHORT}_vs_${rand_count}r_${j}${H_MODELS_SHORT[i]}.txt"
	done
done

eval "python${PYVER} test.py ai_battle ${MODEL} ${H_MODELS[0]} ${H_MODELS[1} ${H_MODELS[2]} > ${MODEL_SHORT}_vs_mixed.txt"