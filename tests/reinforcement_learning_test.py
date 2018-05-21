#!/usr/bin/env python3
"""Tests for reinforcement_learning.py."""

import sys
from collections import namedtuple
from os.path import dirname, realpath

DIRECTORY = dirname(realpath(__file__))
sys.path.insert(0, dirname(DIRECTORY))

# pylint: disable=wrong-import-position
from research.reinforcement_learning import State, Action
from research.reinforcement_learning import GridWorld, SimpleTMaze
from research.reinforcement_learning import gating_memory

RLTestStep = namedtuple('RLTestStep', ['observation', 'actions', 'action', 'reward'])


def test_gridworld():
    """Test the GridWorld environment."""
    env = GridWorld(
        width=2,
        height=3,
        start=[0, 0],
        goal=[2, 0],
    )
    env.new_episode()
    expected_steps = [
        RLTestStep(State(row=0, col=0), [Action('down'), Action('right')], Action('right'), -1),
        RLTestStep(State(row=0, col=1), [Action('down'), Action('left')], Action('right'), -1),
        RLTestStep(State(row=0, col=1), [Action('down'), Action('left')], Action('down'), -1),
        RLTestStep(State(row=1, col=1), [Action('up'), Action('down'), Action('left')], Action('down'), -1),
        RLTestStep(State(row=2, col=1), [Action('up'), Action('left')], Action('down'), -1),
        RLTestStep(State(row=2, col=1), [Action('up'), Action('left')], Action('up'), -1),
        RLTestStep(State(row=1, col=1), [Action('up'), Action('down'), Action('left')], Action('left'), -1),
        RLTestStep(State(row=1, col=0), [Action('up'), Action('down'), Action('right')], Action('down'), 1),
        RLTestStep(None, [], None, None),
    ]
    for expected in expected_steps:
        assert env.get_observation() == expected.observation
        assert set(env.get_actions()) == set(expected.actions)
        if expected.action is not None:
            reward = env.react(expected.action)
            assert reward == expected.reward

def test_simpletmaze():
    """Test the SimpleTMaze environment."""
    env = SimpleTMaze(2, 1, -1)
    env.new_episode()
    assert env.get_state() == State(x=0, y=0, symbol=0, goal_x=-1)
    expected_steps = [
        RLTestStep(
            State(x=0, y=0, symbol=0),
            [Action('up')],
            Action('up'),
            -1,
        ),
        RLTestStep(
            State(x=0, y=1, symbol=-1),
            [Action('up')],
            Action('up'),
            -1,
        ),
        RLTestStep(
            State(x=0, y=2, symbol=0),
            [Action('left'), Action('right')],
            Action('left'),
            10,
        ),
        RLTestStep(None, [], None, None),
    ]
    for expected in expected_steps:
        assert env.get_observation() == expected.observation
        assert set(env.get_actions()) == set(expected.actions)
        if expected.action is not None:
            reward = env.react(expected.action)
            assert reward == expected.reward


def test_simpletmaze_gatingmemory():
    """Test the SimpleTMaze environment."""
    env = gating_memory(SimpleTMaze, num_memory_slots=1, reward=-0.05)(2, 1)
    env.new_episode()
    goal = env.get_state().goal_x
    assert env.get_state() == State(x=0, y=0, symbol=0, goal_x=goal, memory_0=None)
    expected_steps = [
        RLTestStep(
            State(x=0, y=0, symbol=0, memory_0=None),
            [
                Action('up'),
                Action('gate', slot=0, attribute='x'),
                Action('gate', slot=0, attribute='y'),
                Action('gate', slot=0, attribute='symbol'),
            ],
            Action('up'),
            -1,
        ),
        RLTestStep(
            State(x=0, y=1, symbol=goal, memory_0=None),
            [
                Action('up'),
                Action('gate', slot=0, attribute='x'),
                Action('gate', slot=0, attribute='y'),
                Action('gate', slot=0, attribute='symbol'),
            ],
            Action('gate', slot=0, attribute='symbol'),
            -0.05,
        ),
        RLTestStep(
            State(x=0, y=1, symbol=goal, memory_0=goal),
            [
                Action('up'),
                Action('gate', slot=0, attribute='x'),
                Action('gate', slot=0, attribute='y'),
                Action('gate', slot=0, attribute='symbol'),
            ],
            Action('up'),
            -1,
        ),
        RLTestStep(
            State(x=0, y=2, symbol=0, memory_0=goal),
            [
                Action('left'),
                Action('right'),
                Action('gate', slot=0, attribute='x'),
                Action('gate', slot=0, attribute='y'),
                Action('gate', slot=0, attribute='symbol'),
            ],
            Action('right' if goal == -1 else 'left'),
            -10,
        ),
        RLTestStep(None, [], None, None),
    ]
    for expected in expected_steps:
        assert env.get_observation() == expected.observation
        assert set(env.get_actions()) == set(expected.actions)
        if expected.action is not None:
            reward = env.react(expected.action)
            assert reward == expected.reward
