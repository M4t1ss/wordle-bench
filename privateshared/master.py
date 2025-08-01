"""
A game to test the scorekeeping abilities of a model.
Implementation of a game master that control the game mechanisms. 
"""
import random
from typing import List, Dict, Tuple

import numpy as np
from sklearn.metrics import accuracy_score as acc_score
from sklearn.metrics import cohen_kappa_score

import clemcore.clemgame.metrics as ms
from clemcore.backends import Model, CustomResponseModel
from clemcore.clemgame import GameSpec, Player, GameBenchmark
from clemcore.clemgame.legacy.master import DialogueGameMaster
from clemcore.clemgame.legacy.scorer import GameScorer
import logging

from constants import (
    PROBES_PATH, RETRIES_PATH, UPDATE, WORDS_PATH, REQUESTS_PATH,
    INVALID_LABEL, INVALID, SUCCESS, NOT_SUCCESS, NOT_PARSED, RESULT)

logger = logging.getLogger(__name__)


class Words:
    def __init__(self, data):
        self._data = {k.lower(): v for k, v in data.items()}

    def __getattr__(self, key):
        if key.lower() in self._data:
            return self._data[key.lower()]
        raise AttributeError(f"'Words' object has no attribute '{key}'")


class Answerer(Player):
    def __init__(self, model: Model, name, game_recorder, words: Words):
        super().__init__(model, name, game_recorder=game_recorder)
        self.words = words

    def _custom_response(self, context: Dict) -> str:
        """Return a mock response with a tag and possibly a yes/no prefix."""
        r = random.random()
        # randomly decide whether to start with yes, no or nothing
        begin = ''
        if r < 0.4:
            begin = f'{self.words.no}, '
        elif r < 0.8:
            begin = f'{self.words.yes}, '
        # randomly select an initial tag
        if context["content"].startswith(self.words.me):
            tag = self.words.aside if random.random() < 0.9 else ""
        else:
            tag = self.words.answer if random.random() < 0.9 else ""
        # randomly add invalid continuation
        if random.random() < 0.9:
            return f'{tag}{begin}placeholder.'
        return f'{tag}{begin}placeholder \n invalid stuff.'


class Questioner(Player):
    """Programmatic realisation of the Questioner player."""

    def __init__(self, name, game_recorder,
                 question_order: List[str], requests: Dict[str, int], request_strings: Dict):
        super().__init__(CustomResponseModel(), name, game_recorder=game_recorder)
        self.question_order = question_order
        self.question_type = None
        self.requests = requests
        self.request_strings = request_strings

    def _custom_response(self, context: Dict) -> str:
        """Return the request utterance for a given turn."""
        assert self.question_type is not None, "Use set_question_type_for() before calling the questioner"
        request_idx = self.requests[self.question_type]
        return self.request_strings[self.question_type][request_idx]

    def set_question_type_for(self, current_round: int):
        self.question_type = self.question_order[current_round - 1]


class PrivateSharedGame:
    """Basic QA mechanism, to be called by the game master."""

    def __init__(self, question_order: List[str], slots: Dict[str, str]):
        self.slots = slots
        self.max_turns: int = len(question_order)
        self.question_order = question_order
        self.messages: List = []
        self.current_round: int = 0


class PrivateShared(DialogueGameMaster):

    def __init__(self, game_spec: GameSpec, experiment: Dict, player_models: List[Model]):
        super().__init__(game_spec, experiment, player_models)

    def _on_setup(self, **game_instance):
        """
        Sets the game up, given the game instance parameters.

        Args:
            game_instance: A dictionary containing the game instance parameters.
        """
        self.filled_slots: List = []
        self.aborted: bool = False
        self.played_probing_rounds: int = 0

        # set up game instance
        self.game_instance = game_instance
        self.probing_questions = self.load_json(PROBES_PATH.format(self.experiment['name']))
        self.retries = self.load_json(RETRIES_PATH)['suffixes']

        self.questioner_tag = f"{game_instance['tag']}: "
        self.probing = game_instance['probes']
        self.probe_gt = {slot: i for i, slot in enumerate(game_instance['request_order'])}
        self.game = PrivateSharedGame(game_instance['request_order'], game_instance['slots'])
        self.n_probe_turns = self.game.max_turns + 1  # one probing before the game starts and one after each request
        request_strings = self.load_json(REQUESTS_PATH.format(self.experiment['name']))
        self.words = Words(self.load_json(WORDS_PATH.format(game_instance['lang'])))  # load language specific words
        self.initial_prompt = game_instance['initial_prompt']
        self.all_probes: List[List[Dict]] = []
        
        self.answerer: Answerer = Answerer(self.player_models[0], "Player 1",
                                           self.game_recorder, self.words)
        self.questioner: Questioner = Questioner("Player 2", self.game_recorder,
                                                 game_instance['request_order'],
                                                 game_instance['requests'], request_strings)
        
        # initialise turn counters for common metrics
        self.request_counts = [0] * self.n_probe_turns
        self.parsed_request_counts = [0] * self.n_probe_turns
        self.violated_request_counts = [0] * self.n_probe_turns

        self.add_player(self.answerer)
        self.add_player(self.questioner, initial_context=dict(role="user", content=self.words.dummy_prompt))
        self._current_player_idx = 1  # start with the questioner

    def _on_before_game(self):
        self.set_context_for(self.questioner, self.words.dummy_prompt)

        self.answerer._messages.append(dict(role='user', content=self.initial_prompt, label='pseudo'))
        self.answerer._messages.append(dict(role="assistant", content=self.words.ok, label="pseudo"))
        self.log_event(from_="GM", to=self.answerer.name,
                       action=dict(type="send message", content=self.initial_prompt, label="pseudo"))
        self.log_event(from_=self.answerer.name, to="GM",
                       action=dict(type="get message", content=self.words.ok, label="pseudo"))
        
        # Conduct a preliminary probing round before the actual game starts
        turn_probes, probing_successful = self.probe()
        self.all_probes.append(turn_probes)
        if not probing_successful:
            self.log_to_self("invalid format", "Abort: invalid format in probing.")
            self.aborted = True

        self.current_round = 1  # preliminary probing round is round 0

    def _on_before_round(self):
        self.questioner.set_question_type_for(self.current_round)
        self.set_context_for(self.questioner, self.words.dummy_prompt)

    def _start_next_round(self) -> bool:
        """
        If questioner's turn comes next, we start a new round.

        Rreturns:
            True, when to start a new round
        """
        return self._current_player_idx == 1
    
    def _does_game_proceed(self) -> bool:
        """Check if the game can continue, i.e. not all slots are filled and the game wasn't aborted."""
        if self.aborted:
            return False
        return self.current_round <= self.game.max_turns

    def _validate_player_response(self, player, response):
        """
        Decide if a player response matches the valid response patterns.

        Args:
            player: The player that gave the response.
            response: The response of the current player.
        Returns:
            True, if the response is fine. Otherwise, False.
        """
        if player == self.questioner:
            # Questioner responses are always valid, since they are programmatic
            return True
        if (not response.startswith(self.words.answer.strip())
                or self._has_continuation(response)):
            logger.warning(f"Game round {str(self.current_round)}: {NOT_PARSED}")
            self.violated_request_counts[self.current_round] += 1
            return False
        self.parsed_request_counts[self.current_round] += 1
        return True
    
    def _parse_response(self, player, response):
        # No need to parse questioner's response, since it is programmatic
        if player == self.questioner:
            return response
        # Parse valid answerer's response
        clean_response = self._filter_tag(response, self.words.answer.strip())
        return clean_response
    
    def _on_valid_player_response(self, player, parsed_response):
        """
        Handle a valid response from a player and prepare the next turn.

        Args:
            player: The player that gave the response.
            parsed_response: The parsed response of the current player.
        """
        if player == self.questioner:
            self.set_context_for(self.answerer, f"{self.questioner_tag}{parsed_response}")
        else:
            # Check if the answer was correct
            slot_filled = self._is_slot_filled(parsed_response)
            self.filled_slots.append(slot_filled)
            self.log_to_self("metadata", f"Slot filled: {slot_filled}")
            # check if the agent gave away more info than it should
            # update ground truth if necessary
            self._update_anticipated_slots(parsed_response)
            # probing turn
            turn_probes, probing_successful = self.probe()
            self.all_probes.append(turn_probes)
            if not probing_successful:
                self.log_to_self("invalid format", "Abort: invalid format in probing.")
                self.aborted = True
            # increment request counts
            self.request_counts[self.current_round] += 1  # requests to the answerer per round
    
    def _on_after_game(self):
        self.log_key('probes', self.all_probes)
        self.log_key('realised_slots', self.probe_gt)
        self.log_to_self('end', 'Game finished.')
        self._log_eval_assets()

    @staticmethod
    def _has_continuation(response: str) -> bool:
        """Return True if the response continues after what is needed."""
        # if the answer contains a line break with some continuation after it,
        # we consider it to be an invalid response
        # we strip first to account for cases where it ends in one or many \n
        # without producing anything after it, and then check if the remaining
        # text still contains a line break
        if '\n' in response.strip('\n'):
            return True
        return False

    def _is_slot_filled(self, answer: str) -> bool:
        """Check if answer contains the correct value for a slot."""
        slot = self.game.question_order[self.current_round - 1]
        value = self.game.slots[slot]
        if value.lower() in answer.lower():
            return True
        return False

    def _update_anticipated_slots(self, answer: str) -> None:
        """Update ground truth when agent anticipates a slot value."""
        turn = self.current_round - 1
        for slot, value in self.game.slots.items():
            if value.lower() in answer.lower() and turn < self.probe_gt[slot]:
                update = UPDATE.format(slot.upper(), self.probe_gt[slot], turn)
                self.log_to_self("metadata", update)
                self.probe_gt[slot] = turn

    def _log_eval_assets(self) -> None:
        """Log everything needed for the evaluation."""
        self.log_key(ms.METRIC_REQUEST_COUNT,
                     self.request_counts)
        self.log_key(ms.METRIC_REQUEST_COUNT_PARSED,
                     self.parsed_request_counts)
        self.log_key(ms.METRIC_REQUEST_COUNT_VIOLATED,
                     self.violated_request_counts)
        self.log_key('Filled Slots', self.filled_slots)
        self.log_key('Aborted', self.aborted)
        self.log_key('Played Probe Rounds', self.played_probing_rounds)

    def _create_probe_dict(self, question_type: str, idx: int) -> Dict:
        question = self.probing_questions[question_type][idx]
        return {'target': question_type.upper(),
                'question': self.words.probe.format(question),
                'gt': 1 if self.current_round > self.probe_gt[question_type] else 0}

    def _create_turn_probes(self) -> List[Dict]:
        """Return a list of probing dictionaries."""
        return [self._create_probe_dict(question_type, idx)
                for question_type, idx in self.probing[str(self.current_round)].items()]

    def probe(self) -> Tuple[List[Dict], bool]:
        """Perform a round of probing."""
        probes = self._create_turn_probes()
        success_by_round = []
        for probe in probes:
            # perform a probing loop, with retries up to maximum retries
            answer, parsed_response, successful, tries = self._probing_loop(probe)
            # add results to the probe object
            probe['answer'] = answer
            probe['value'] = self._convert_response(parsed_response)
            probe['tries'] = tries
            self._log_probing_outcome(probe, successful, tries)
            success_by_round.append(successful)
            if not successful:  # interrupt immediately
                break
        probing_successful = all(success_by_round)
        if probing_successful:  # actual valid rounds for posterior evaluation
            self.played_probing_rounds += 1
        return probes, probing_successful

    def _probing_loop(self, probe: Dict) -> Tuple[str, str, bool, int]:
        """
        Perform a probing round until valid response or max attempts.
        Questions from the probing are *not* added to the message history ("memorized").
        """
        tries = 1
        successful = False
        while tries <= len(self.retries):
            question = self._get_probe_content(probe['question'], tries)
            context = dict(role="user", content=question)
            answer = self.answerer(context, memorize=False)
            self.request_counts[self.current_round] += 1  # requests to the answerer per round
            parsed_response = self._parse_probing_response(answer)
            self.log_to_self("parse", parsed_response)
            if parsed_response in (self.words.yes, self.words.no):  # check if valid response, otherwise try again
                successful = True
                self.parsed_request_counts[self.current_round] += 1
                break
            self.violated_request_counts[self.current_round] += 1
            tries += 1
        return answer, parsed_response, successful, tries

    def _get_probe_content(self, question: str, tries: int) -> str:
        return question[:].replace(self.words.me, f'{self.words.me}{self.retries[tries - 1]} ')

    def _log_probing_outcome(self, probe: Dict, successful: bool, tries: int):
        if not successful:
            content = NOT_SUCCESS.format(probe['target'])
        else:
            content = SUCCESS.format(probe['target'], tries)
        # answer valid?
        self.log_to_self("metadata", content)
        # answer correct?
        result = '' if probe['value'] == probe['gt'] else 'in'
        self.log_to_self("check", RESULT.format(result))

    @staticmethod
    def _filter_tag(answer: str, tag: str) -> str:
        """Remove a tag from a utterance."""
        filtered = answer.replace(tag, '')
        return filtered.strip()

    def _parse_probing_response(self, response: str) -> str:
        """Extract parsed answer in probing turn."""
        if (not response.startswith(self.words.aside.strip())
                or self._has_continuation(response)):
            return INVALID
        clean_response = self._filter_tag(response, self.words.aside.strip())
        if clean_response.lower().startswith(self.words.yes):
            return self.words.yes
        if clean_response.lower().startswith(self.words.no):
            return self.words.no
        return INVALID

    def _convert_response(self, response: str) -> int:
        """Turn probing response into integer (0: negation, 1: affirmation)."""
        if response == self.words.yes:
            return 1
        if response == self.words.no:
            return 0
        return INVALID_LABEL


class PrivateSharedScorer(GameScorer):

    def __init__(self, game_name: str, experiment: Dict, game_instance: Dict):
        super().__init__(game_name, experiment, game_instance)
        self.slots = game_instance["slots"]

    def compute_scores(self, episode_interactions: Dict) -> None:
        logs = episode_interactions
        gold = []
        pred = []
        aborted = logs['Aborted']
        for turn in range(logs['Played Probe Rounds']):
            turn_gt, turn_pred = self._compute_turn_scores(logs, turn)
            gold += turn_gt
            pred += turn_pred
            # n_probes = n_slots + 1, we take the third round of probing here
            if turn == int((len(self.slots) + 1) / 2) - 1:
                mid_acc = acc_score(turn_gt, turn_pred) if not aborted else np.nan
                self.log_episode_score('Middle-Accuracy', mid_acc)

        self._compute_episode_scores(gold, pred, logs, aborted)

    def _compute_turn_scores(self, logs: Dict, turn: int) -> Tuple[List, List]:
        """Compute and log turn-level scores."""
        # common scores
        reqs = logs[ms.METRIC_REQUEST_COUNT][turn]
        p_reqs = logs[ms.METRIC_REQUEST_COUNT_PARSED][turn]
        v_reqs = logs[ms.METRIC_REQUEST_COUNT_VIOLATED][turn]

        self.log_turn_score(turn, ms.METRIC_REQUEST_COUNT, reqs)
        self.log_turn_score(turn, ms.METRIC_REQUEST_COUNT_PARSED, p_reqs)
        self.log_turn_score(turn, ms.METRIC_REQUEST_COUNT_VIOLATED, v_reqs)

        # specific scores
        turn_gt, turn_pred = self._get_gold_pred(logs['probes'][turn])
        acc = acc_score(turn_gt, turn_pred)
        self.log_turn_score(turn, 'Accuracy', acc)
        if turn != 0:
            # no slot in the first probing round
            # -1 because the probing turn ids are shifted one step
            filled = int(logs['Filled Slots'][turn - 1])
            self.log_turn_score(turn, 'Slot Filled?', filled)

        return turn_gt, turn_pred

    def _compute_episode_scores(self,
                                gold: List,
                                pred: List,
                                logs: Dict,
                                aborted: bool
                                ) -> None:
        """Compute and log episode-level scores."""
        # specific scores
        acc = acc_score(gold, pred) if not aborted else np.nan
        kappa = cohen_kappa_score(gold, pred) if not aborted else np.nan
        # we truncate kappa to be between 0 and 1
        trunc_kappa = max(0, kappa) if not aborted else np.nan
        filled = logs['Filled Slots']
        sf_acc = sum(filled) / len(filled) if not aborted else np.nan
        bench_score = PrivateSharedScorer.compute_bench_score(sf_acc, trunc_kappa)

        self.log_episode_score('Accuracy', acc)
        self.log_episode_score('Kappa', kappa)
        self.log_episode_score('Truncated Kappa', trunc_kappa)
        self.log_episode_score('Slot-Filling-Accuracy', sf_acc)
        self.log_episode_score(ms.BENCH_SCORE, bench_score)

        # common scores
        success_ratio = int(acc == 1. and sf_acc == 1.) if not aborted else 0
        lose_ratio = int(not success_ratio) if not aborted else 0
        reqs = sum(logs[ms.METRIC_REQUEST_COUNT])
        parsed_reqs = sum(logs[ms.METRIC_REQUEST_COUNT_PARSED])
        violated_reqs = sum(logs[ms.METRIC_REQUEST_COUNT_VIOLATED])

        self.log_episode_score(ms.METRIC_ABORTED, int(aborted))
        self.log_episode_score(ms.METRIC_LOSE, lose_ratio)
        self.log_episode_score(ms.METRIC_SUCCESS, success_ratio)
        self.log_episode_score(ms.METRIC_REQUEST_COUNT, reqs)
        self.log_episode_score(ms.METRIC_REQUEST_COUNT_PARSED, parsed_reqs)
        self.log_episode_score(ms.METRIC_REQUEST_COUNT_VIOLATED, violated_reqs)
        self.log_episode_score(ms.METRIC_REQUEST_SUCCESS_RATIO, parsed_reqs / reqs)

    def _get_gold_pred(self, turns: List) -> Tuple[List, List]:
        """Retrieve the gold standard and the predictions for all turns."""
        gold, pred = zip(*[(item['gt'], item['value']) for item in turns])
        return gold, pred

    @staticmethod
    def compute_bench_score(sf_acc: float, kappa: float) -> float:
        """Compute the preferred score in [0, 100] for the benchmark."""
        if np.isnan(sf_acc) or np.isnan(kappa):
            return np.nan
        if sf_acc + kappa == 0:
            return 0
        # harmonic mean between accuracy and truncated kappa
        # normalised to 0-100
        return 100 * (2 * sf_acc * kappa / (sf_acc + kappa))


class PrivateSharedGameBenchmark(GameBenchmark):
    """Integrate the game into the benchmark run."""

    def __init__(self, game_spec: GameSpec):
        super().__init__(game_spec)

    def create_game_master(self, experiment: Dict, player_models: List[Model]) -> DialogueGameMaster:
        return PrivateShared(self.game_spec, experiment, player_models)

    def create_game_scorer(self, experiment: Dict, game_instance: Dict) -> GameScorer:
        return PrivateSharedScorer(self.game_name, experiment, game_instance)


def main():
    """Play the first episode in the instances."""
    from clemcore.utils import file_utils
    instances = file_utils.load_json("in/instances.json", "privateshared")
    experiment = instances["experiments"][0]
    instance = experiment["game_instances"][0]
    master = PrivateShared(experiment, ["dry_run"])
    master.setup(**instance)
    master.play()


if __name__ == '__main__':
    main()
