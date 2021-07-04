# GEM POWERPLANT CODING CHALLENGE
<p style="text-align:center;">
<img src="/Images/powerplant.jpg" width="80%" >
</p>

## AUTHOR

Hello! I am Olivier Algoet, a control & automation engineer with a passion for artificial intelligence, deep learning and smart control algorithms.
<p style="text-align:center;">
<img src="/Images/myself.jpeg" width="40%">
</p>

## API LAUNCH

I used a conda environment
Clone the github repo
```shell
cd powerplant-coding-challenge
conda create -n gemchallenge python=3.8
## Enter y a few times
conda activate gemchallenge
pip install -r requirements.txt
python GEMChallenge.py
```

## ALGORITHM EXPLANATION

At first I wanted to solve the challenge using the classical optimization algorithms:

- CEM (Cross entropy method)
- Linear programming (With integer part for windturbine)
- Particle swarm optimization (With bounded particles)
- ...

Without the Pmin constraint for the gasfired plant the challenge is not difficult since we can simply follow the merit order.
I chose to solve the problem by using a forward pass following the merit order and backward pass to account for Pmin constraints
I define a Pmin constraint as a forward pass with loadleft< Pmin of the gasfired plant

### Forward pass

When this happens there are 2 options:

- Don't use the gasfired turbine P=0
- Make sure to use the gasfired turbine P≠0 by freeing energy from the previous plants (Backward pass)

### Backward pass

similarly for the backward pass we have 2 options when a gasfired (Pmin) constraint presents itself:

- Assign P as 0 --> Deactivate the plant
- Assign P as Pmin --> Take all excess power from the plant

When during the backward pass a windturbine is deactivate there might be an excess of energy due to the power drop.
This excess energy is redistributed using the merit order across the plants

## UNIT TEST

A small unittest program is also written which reads the example json and changes the load from 0 to sum(Plants)
The results of this program are written in unit_test_results.txt with Correct/ Wrong or no solution found
```shell
cd powerplant-coding-challenge
conda activate gemchallenge
python unittest.py
```
