/*
KB: scorrer players facts and rules as of Jan 2026

goal: determine which league a player plays in based on facts
      about their gender and region they play in.
*/
% 10 facts 

% male soccer players
male(kylian_mbappe).
male(mohamed_salah).
male(lamine_yamal).

% female soccer players
female(claudia_pina).
female(sam_kerr).
female(aitana_bonmati).

% region they play in
plays_in(kylian_mbappe, spain).
plays_in(claudia_pina, spain).
plays_in(lamine_yamal, spain).
plays_in(mohamed_salah, england).
plays_in(sam_kerr, england).
plays_in(aitana_bonmati, spain).

% exclusivity constraints
% necessary because prover 9 uses OWA
\+male(X) :- female(X).
\+female(X) :- male(X).
\+plays_in(X, spain) :- plays_in(X, england).
\+plays_in(X, england) :- plays_in(X, spain).

% rules matching the player to their actual league name
% based on what region they play in and their gender.
premier_league(X) :- male(X), plays_in(X, england).
la_liga(X) :- male(X), plays_in(X, spain).
wsl(X) :- female(X), plays_in(X, england).
liga_f(X) :- female(X), plays_in(X, spain).