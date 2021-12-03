import random
import sys
import asyncio

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import time
from spade.agent import Agent
from spade.behaviour import FSMBehaviour, State


# -----------------------------------------------------------------------------------------------------------------------
# Creating Agents objects.

class DiceAgent(Agent):
    # Overwriting the Agent-constructor to add a total score
    def __init__(self, jid, password, total=0):
        super().__init__(jid, password)
        self.total = total


# -----------------------------------------------------------------------------------------------------------------------
# FSM-AGENT

class FSMAgent(Agent):
    async def setup(self):
        # On FSM-AGENT startup creating two Agents
        dice_agent = DiceAgent('diceagent@chatserver.space', '12345')
        dice_opponent = DiceAgent("diceopponent@chatserver.space", "12345")
        print(f'{dice_agent.jid} STARTED AS Hairy Punter')
        time.sleep(5)
        print(f'{dice_opponent.jid} STARTED AS Hairmoney Stranger')

        # Adding state machine on_start, on_stop behaviours
        fsm = FiniteStateMachineBehaviour()
        # Declaring and connecting the state names to the state classes
        fsm.add_state(name=STATE_START, state=StateStart(), initial=True)
        fsm.add_state(name=STATE_ONE, state=StateOne(dice_agent, dice_opponent))
        fsm.add_state(name=STATE_TWO, state=StateTwo(dice_agent))
        fsm.add_state(name=STATE_THREE, state=StateThree(dice_opponent))
        fsm.add_state(name=STATE_FOUR, state=StateFour(dice_agent, dice_opponent))
        fsm.add_state(name=STATE_STOP, state=StateStop())
        # State machines transition flow between states.
        fsm.add_transition(source=STATE_START, dest=STATE_ONE)
        fsm.add_transition(source=STATE_ONE, dest=STATE_TWO)
        fsm.add_transition(source=STATE_ONE, dest=STATE_THREE)
        fsm.add_transition(source=STATE_TWO, dest=STATE_ONE)
        fsm.add_transition(source=STATE_THREE, dest=STATE_ONE)
        fsm.add_transition(source=STATE_ONE, dest=STATE_FOUR)
        fsm.add_transition(source=STATE_FOUR, dest=STATE_STOP)
        self.add_behaviour(fsm)


# -----------------------------------------------------------------------------------------------------------------------
# On Start and End behaviours, needed to start and stop the finite state machine.

class FiniteStateMachineBehaviour(FSMBehaviour):
    async def on_start(self):
        print(f"INITIAL STATE - {self.current_state}")

    async def on_end(self):
        print(f"FINISHING STATE - {self.current_state}")
        await self.agent.stop()


# -----------------------------------------------------------------------------------------------------------------------
# STATES (All the declared states for the state machine).

STATE_START = "STATE_START"
STATE_ONE = "STATE_ONE"
STATE_TWO = "STATE_TWO"
STATE_THREE = "STATE_THREE"
STATE_FOUR = "STATE_FOUR"
STATE_STOP = "STATE_STOP"


# -----------------------------------------------------------------------------------------------------------------------
# STATE_START

class StateStart(State):
    async def run(self):  # Start state which prints and moves on to next state
        print(f'Starting up STARTING_STATE')
        time.sleep(1)
        self.set_next_state(STATE_ONE)


# -----------------------------------------------------------------------------------------------------------------------
# STATE_ONE
class StateOne(State):
    # Overwriting constructor to pass the agents into the state
    def __init__(self, dice_agent, dice_opponent):
        super().__init__()
        self.check = True  # Adding a flag to play the role of an alternator
        self.dice_agent = dice_agent
        self.dice_opponent = dice_opponent

    async def run(self):
        # If statement that will run if self.check is true
        if self.check:
            # If check is True and dice_agents total is above 18, DO NOT run.
            if not self.dice_agent.total >= 18:
                # If total is at or below 18, go to state_two and set self.check to false (which will alternate agents)
                self.set_next_state(STATE_TWO)
                self.check = False
        elif not self.check:
            if not self.dice_opponent.total >= 18:
                # Same as above but for dice_opponent instead of dice_agent
                self.set_next_state(STATE_THREE)
                self.check = True
        # Checks the agents scores and if both have above 18 and under 21 points state is set to state four.
        if self.dice_agent.total >= 18 and self.dice_opponent.total >= 18:
            if not self.dice_agent.total > 21 or not self.dice_opponent.total > 21:
                time.sleep(0.5)
                self.set_next_state(STATE_FOUR)


# -----------------------------------------------------------------------------------------------------------------------
# STATE_TWO

class StateTwo(State):
    # Overwriting constructor to pass dice_agent into the state
    def __init__(self, dice_agent):
        super().__init__()
        self.dice_agent = dice_agent

    async def run(self):
        # A random number is assigned to the variable random_number
        random_number = random_dice_number()
        # The randomly generated number is appended to dice_agents total
        self.dice_agent.total += random_number
        # Print agents name, random number and total score
        print(f'{email_stripper(self.dice_agent.jid)} rolled ({random_number}) Total: ({self.dice_agent.total})')
        time.sleep(0.5)
        # Go to next state
        self.set_next_state(STATE_ONE)


# -----------------------------------------------------------------------------------------------------------------------
# STATE_THREE

# State two and state three are virtually the same. We tried to implement current_agent which we alternate instead but
# when adding states we had to pass both dice_agent and opponent.
class StateThree(State):
    def __init__(self, dice_opponent):
        super().__init__()
        self.dice_opponent = dice_opponent

    async def run(self):
        random_number = random_dice_number()
        self.dice_opponent.total += random_number
        print(f'{email_stripper(self.dice_opponent.jid)} rolled ({random_number}) Total: ({self.dice_opponent.total})')
        time.sleep(0.5)
        self.set_next_state(STATE_ONE)


# -----------------------------------------------------------------------------------------------------------------------
# STATE_FOUR

class StateFour(State):
    # Overwriting constructor to pass the agents into the state
    def __init__(self, dice_agent, dice_opponent):
        super().__init__()
        self.dice_agent = dice_agent
        self.dice_opponent = dice_opponent

    async def run(self):
        # Prints the finals scores that the agents got
        print(f'Final Scores - {email_stripper(self.dice_agent.jid)}: ({self.dice_agent.total}),'
              f' {email_stripper(self.dice_opponent.jid)}: ({self.dice_opponent.total})')
        # If both agents rolled a total above 21, print "Both lose"
        if self.dice_agent.total > 21 and self.dice_opponent.total > 21:
            print(f'Both lose!')
        # If dice_opponents total is higher than dice_agent and lower or equal to 21 or
        # if dice_agents total is higher than 21 and dice_opponents total is equal to or less than 21 print
        # (dice_opponent won!)
        elif 21 >= self.dice_opponent.total > self.dice_agent.total \
                or self.dice_agent.total > 21 >= self.dice_opponent.total:
            print(f'{email_stripper(self.dice_opponent.jid)} won!')
        # If dice_agents total is higher than dice_opponents and lower or equal to 21 or
        # if dice_opponents total is higher than 21 and dice_agents total is equal to or less than 21 print
        # (dice_agents won!)
        elif 21 >= self.dice_agent.total > self.dice_opponent.total \
                or self.dice_opponent.total > 21 >= self.dice_agent.total:
            print(f'{email_stripper(self.dice_agent.jid)} won!')
        # If none of the other four possibilities are true, the last possible is a tie.
        else:
            print(f'It is a tie!')
        # Go to next state
        self.set_next_state(STATE_STOP)


# -----------------------------------------------------------------------------------------------------------------------
# STATE_STOP

class StateStop(State):
    async def run(self):  # Last state, since it is the last state no final state is set as agent will stop on its own
        print(f'Thanks for playing!')
        time.sleep(1)


# -----------------------------------------------------------------------------------------------------------------------
# Email stripper, removes email part of the agents and proceeds to rename them ( QoL console prints )

def email_stripper(agent_mail):
    x = str(agent_mail).replace('@chatserver.space', "")
    x = 'Hairy Punter' if x == 'diceagent' else 'Hairmoney Stranger'
    return x


# -----------------------------------------------------------------------------------------------------------------------
# Function for generating random number between 1-6
def random_dice_number():
    return random.randint(1, 6)


# -----------------------------------------------------------------------------------------------------------------------
# Program

if __name__ == "__main__":
    FSMAgentOne = FSMAgent("blackdice@chatserver.space", "12345")
    future = FSMAgentOne.start()
    future.result()

    # If the FSM-Agent does not respond within 1 second, stop the state machine.
    while FSMAgentOne.is_alive():
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            FSMAgentOne.stop()
            break
    print("FSM Game Agent Finished")
