Neuro-symbolic pipeline

task: Translate problem statement (domain is typically in another file, state and goal) into Planning Domain Definition Language (PDDL) using a pipeline. The PDDL is then validated by a classical solver.

what are the components in a PDDL?
how do you deal with incorrect / unsolvable PDDLs?

Components:
1. LLM
2. Planner (PDDL works)
3. Validator (plan from planner works)


Run for 3-5 iterations before stopping


