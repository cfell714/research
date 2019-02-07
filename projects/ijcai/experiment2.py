#!/usr/bin/env python3

import sys
from collections import namedtuple
from datetime import datetime
from math import isnan
from os.path import realpath, dirname

DIRECTORY = dirname(realpath(__file__))
sys.path.insert(0, dirname(DIRECTORY))

# pylint: disable = wrong-import-position
from permspace import PermutationSpace

from research.knowledge_base import SparqlEndpoint
from research.rl_core import train_and_evaluate
from research.rl_agents import epsilon_greedy, LinearQLearner
from research.rl_environments import State, Action, Environment
from research.rl_memory import memory_architecture, SparqlKB
from research.randommixin import RandomMixin

Album = namedtuple('Album', 'title, artist, year, genre')


class RecordStore(Environment, RandomMixin):

    def __init__(self, num_albums=1000, *args, **kwargs):
        # pylint: disable = keyword-arg-before-vararg
        super().__init__(*args, **kwargs)
        # parameters
        self.num_albums = num_albums
        # variables
        self.albums = {}
        self.titles = []
        self.curr_title = None
        self.location = None
        self.reset()

    def get_state(self):
        return self.get_observation()

    def get_observation(self):
        return State.from_dict({
            '<http://www.w3.org/2000/01/rdf-schema#label>': self.curr_title,
        })

    def get_actions(self):
        if self.location == self.albums[self.curr_title]:
            return []
        actions = []
        for year in set(self.albums.values()):
            actions.append(Action(year))
        return actions

    def react(self, action):
        self.location = action.name
        if self.location == self.albums[self.curr_title]:
            return 0
        else:
            return -10

    def reset(self):
        select_statement = f'''
            SELECT DISTINCT ?title, ?release_date WHERE {{
                ?album <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> dbo:Album ;
                       <http://www.w3.org/2000/01/rdf-schema#label> ?title ;
                       <http://dbpedia.org/ontology/releaseDate> ?release_date .
                FILTER ( lang(?title) = "en" )
            }} LIMIT {self.num_albums}
        '''
        endpoint = SparqlEndpoint('https://dbpedia.org/sparql')
        self.albums = {}
        for result in endpoint.query_sparql(select_statement):
            self.albums[result['title'].rdf_format] = result['release_date'].rdf_format
        self.titles = sorted(self.albums.keys())

    def start_new_episode(self):
        self.curr_title = self.rng.choice(self.titles)
        self.location = 'start'

    def visualize(self):
        raise NotImplementedError()


def feature_extractor(state):
    features = set()
    features.add('_bias')
    for attribute in state:
        if attribute.startswith('scratch'):
            features.add((attribute, state[attribute]))
        else:
            features.add(attribute)
    return features


def testing():
    agent = epsilon_greedy(LinearQLearner)(
        # Linear Q Learner
        learning_rate=0.1,
        discount_rate=0.9,
        feature_extractor=feature_extractor,
        # Epsilon Greedy
        exploration_rate=0.05,
        # Random Mixin
        random_seed=8675309,
    )
    env = memory_architecture(RecordStore)(
        # record store
        num_albums=3,
        # memory architecture
        knowledge_store=SparqlKB(SparqlEndpoint('https://dbpedia.org/sparql')),
        # Random Mixin
        random_seed=8675309,
    )
    for trial in range(1000):
        env.start_new_episode()
        step = 0
        total = 0
        while not env.end_of_episode():
            print(step)
            observation = env.get_observation()
            print('   ', observation)
            actions = env.get_actions()
            action = agent.act(observation, actions)
            print('   ', action)
            reward = env.react(action)
            print('   ', reward)
            agent.observe_reward(observation, reward, actions=env.get_actions())
            step += 1
            print()
            total += reward
            if total < -100:
                break
        print(trial, total)
    env.start_new_episode()
    visited = set()
    for step in range(10):
        print(step)
        observation = env.get_observation()
        print(observation)
        if observation in visited:
            print('\n')
            print('Looped; quitting.\n')
            break
        elif env.end_of_episode():
            break
        print(feature_extractor(observation))
        actions = env.get_actions()
        for action in sorted(actions):
            print(action)
            print('    ', agent.get_value(env.get_observation(), action))
        action = agent.get_best_stored_action(env.get_observation(), actions=actions)
        print(action)
        env.react(action)
        print()


if __name__ == '__main__':
    testing()