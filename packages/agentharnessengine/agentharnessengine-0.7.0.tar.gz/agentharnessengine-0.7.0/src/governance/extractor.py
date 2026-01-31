from abc import ABC, abstractmethod
from typing import Dict, List, Optional
import math
from collections import deque

from governance.signals import Signals
from governance.observation import Observation


class SignalExtractor(ABC):
    """
    Base class for transforming Observations into Signals.
    
    This layer is heuristic. Its job is to interpret the evidence provided
    by the adapter and produce the 4 control signals (Reward, Novelty, 
    Urgency, Difficulty).
    """
    
    @abstractmethod
    def extract(self, observation: Observation) -> Signals:
        """Convert a single observation into control signals."""
        pass
    
    @abstractmethod
    def reset(self) -> None:
        """Reset internal state (history, counters) between episodes."""
        pass


class RuleBasedExtractor(SignalExtractor):
    """
    Default extractor using explicit heuristic rules.
    
    Implements the logic defined in SIGNAL_SPECIFICATION.md:
    - Reward: Directional change based on result + state delta
    - Novelty: Entropy of actions + control loss scaling
    - Urgency: Monotonic budget/time pressure
    - Difficulty: Failure streaks and stagnation detection
    """
    
    # Weights (from Spec)
    W_ENV = 0.7
    W_AGENT = 0.3
    STATE_HASH_WINDOW = 10  # S-1: How many steps back to check for cycling
    
    def __init__(
        self, 
        time_limit: float = 300.0, 
        step_limit: int = 50,
        progress_threshold: float = 0.05,
        stagnation_limit: int = 5
    ):
        self.time_limit = time_limit
        self.step_limit = step_limit
        self.progress_threshold = progress_threshold
        self.stagnation_limit = stagnation_limit
        self.reset()
        
    def reset(self) -> None:
        self.step_count = 0
        self.start_time = 0.0
        
        # State tracking
        self.action_history: deque = deque(maxlen=20)
        self.failure_streak = 0
        self.stagnation_counter = 0
        
        # State Cycling Detection (S-1 Anti-Churn)
        self.state_hash_history: deque = deque(maxlen=self.STATE_HASH_WINDOW)
        
        # Signal persistence (signals change slowly)
        self.current_reward = 0.0
        self.current_novelty = 1.0
        self.current_difficulty = 0.0
        
        # Novelty debt (Anti-gaming)
        self.novelty_debt = 0.0
        
        # Signal Trust (Immunity to fake signals)
        self.signal_trust = 1.0

    def extract(self, observation: Observation) -> Signals:
        self.step_count += 1
        
        # 0. State Cycling Detection (S-1 Invariant)
        # If the environment state hash repeats within N steps, treat env_state_delta as 0
        state_hash = self._compute_state_hash(observation)
        effective_env_delta = observation.env_state_delta
        
        if state_hash in self.state_hash_history:
            effective_env_delta = 0.0  # S-1: Not actually new state, it's cycling
        
        self.state_hash_history.append(state_hash)
        
        # 1. Compute Composite State Delta (using effective env delta)
        state_delta = (
            self.W_ENV * effective_env_delta + 
            self.W_AGENT * observation.agent_state_delta
        )
        
        # 2. Update Trust
        self._update_trust(observation, state_delta)
        
        # 2. Extract Base Signals
        reward = self._compute_reward(observation, state_delta)
        novelty = self._compute_novelty(observation, state_delta)
        urgency = self._compute_urgency(observation)
        difficulty = self._compute_difficulty(observation, state_delta)
        
        # 3. Apply Control Loss Dominance (Novelty Suppression)
        # Novelty scaled by (1 - difficulty^2) as a proxy for control loss
        effective_novelty = novelty * (1.0 - difficulty ** 2)
        
        # 4. Apply Signal Trust
        # Trust gates all signals to prevent fake progress
        final_reward = reward * self.signal_trust
        final_novelty = effective_novelty * self.signal_trust
        final_difficulty = difficulty  # Difficulty is NOT gated by trust (safety brake)
        
        return Signals(
            reward=max(-1.0, min(1.0, final_reward)),
            novelty=max(0.0, min(1.0, final_novelty)),
            urgency=max(0.0, min(1.0, urgency)),
            difficulty=max(0.0, min(1.0, final_difficulty)),
            trust=max(0.0, min(1.0, self.signal_trust))
        )

    def _compute_reward(self, obs: Observation, state_delta: float) -> float:
        # R-1: Reward decays if state delta below threshold
        if state_delta < self.progress_threshold:
            # Decay reward toward 0 (indifference) or -0.1 (slight penalty)
            self.current_reward *= 0.8
            self.current_reward -= 0.05
        else:
            # Reinforce based on result
            if obs.result == 'success':
                self.current_reward += 0.3
            elif obs.result == 'failure':
                self.current_reward -= 0.5
            elif obs.result == 'timeout':
                self.current_reward -= 0.8
                
        # Clamp persistence
        self.current_reward = max(-1.0, min(1.0, self.current_reward))
        return self.current_reward

    def _compute_novelty(self, obs: Observation, state_delta: float) -> float:
        # Novelty based on action uniqueness
        if obs.action in self.action_history:
            self.current_novelty *= 0.7  # Decay on repetition
        else:
            self.current_novelty += 0.4  # Boost on new action
            
        self.action_history.append(obs.action)
        
        # Novelty Debt Logic
        # Accumulate debt if novelty is high but reward is non-positive
        if self.current_novelty > 0.5 and self.current_reward <= 0:
            self.novelty_debt += self.current_novelty
        
        # Novelty Debt Recovery 
        if self.current_reward > 0.5:
            self.novelty_debt *= 0.8
            
        # Suppress if debt too high
        if self.novelty_debt > 5.0:
            return 0.0  # Exploration theater detected
        elif self.novelty_debt > 3.0:
            return self.current_novelty * 0.5
            
        return min(1.0, self.current_novelty)

    def _compute_urgency(self, obs: Observation) -> float:
        # Monotonic increase based on time or steps
        time_pressure = min(1.0, obs.elapsed_time / self.time_limit) if self.time_limit else 0.0
        step_pressure = min(1.0, self.step_count / self.step_limit) if self.step_limit else 0.0
        
        return max(time_pressure, step_pressure)

    def _compute_difficulty(self, obs: Observation, state_delta: float) -> float:
        # 1. Failure streak
        if obs.result != 'success':
            self.failure_streak += 1
        else:
            self.failure_streak = 0
            
        # 2. Stagnation (Near-zero progress)
        if state_delta < self.progress_threshold:
            self.stagnation_counter += 1
        else:
            self.stagnation_counter = 0
            
        # Base difficulty from failure
        difficulty = 0.0
        if self.failure_streak > 0:
            difficulty += 0.2 * self.failure_streak
            
        # Add stagnation penalty (Control loss spike after N steps)
        if self.stagnation_counter >= self.stagnation_limit:
            difficulty += 0.5  # Significant spike
            
        # Add error penalty
        if obs.result == 'error':
            difficulty += 0.3
            
        self.current_difficulty = max(self.current_difficulty * 0.9, difficulty)
        return min(1.0, self.current_difficulty)

    def _update_trust(self, obs: Observation, state_delta: float) -> None:
        # Trust Logic
        
        # Decay if result is success but state didn't change (fake success)
        if obs.result == 'success' and state_delta < self.progress_threshold:
            self.signal_trust *= 0.85
            
        # Decay if result is failure but agent claims high internal change (spinning wheels)
        if obs.result == 'failure' and obs.agent_state_delta > 0.8:
            self.signal_trust *= 0.9
            
        # Recover slowly on consistent behavior (success + state change)
        if obs.result == 'success' and state_delta > self.progress_threshold:
            self.signal_trust = min(1.0, self.signal_trust + 0.05)

    def _compute_state_hash(self, obs: Observation) -> int:
        """
        Generate a hash representing the environment state for cycling detection.
        
        Uses action + result + env_state_delta (quantized) to create a fingerprint.
        This is intentionally coarse to catch oscillating patterns.
        """
        # Quantize env_state_delta to 2 decimal places to avoid float noise
        quantized_delta = round(obs.env_state_delta, 2)
        
        # Combine action, result, and quantized delta into a hashable tuple
        state_tuple = (obs.action, obs.result, quantized_delta)
        return hash(state_tuple)


class LLMAgentExtractor(RuleBasedExtractor):
    """
    Specialized extractor for LLM-based agents.
    
    Adds token budget awareness and stricter trust logic for reasoning 
    heavy steps (high agent_delta) that yield no environment results.
    """
    
    def __init__(
        self, 
        time_limit: float = 300.0, 
        step_limit: int = 50,
        token_limit: int = 100000,
        progress_threshold: float = 0.05,
        stagnation_limit: int = 5
    ):
        super().__init__(time_limit, step_limit, progress_threshold, stagnation_limit)
        self.token_limit = token_limit
        self.tokens_accumulated = 0

    def _compute_urgency(self, obs: Observation) -> float:
        # LLM urgency includes token budget depletion
        self.tokens_accumulated += obs.tokens_used
        
        token_pressure = (self.tokens_accumulated / self.token_limit) if self.token_limit else 0.0
        base_urgency = super()._compute_urgency(obs)
        
        return max(base_urgency, token_pressure)
    
    def _update_trust(self, obs: Observation, state_delta: float) -> None:
        super()._update_trust(obs, state_delta)
        
        # LLM-Specific Trust: "Reasoning Theater" detection
        # If agent_state_delta is very high (lots of reasoning) but env_state_delta is 0
        # for multiple steps, decay trust faster.
        if obs.env_state_delta < 0.01 and obs.agent_state_delta > 0.8:
            self.signal_trust *= 0.9  # Faster decay for yapping


class ToolAgentExtractor(RuleBasedExtractor):
    """
    Specialized extractor for tool-calling agents.
    
    Focuses on tool execution success/failure and explicit 
    environment changes.
    """
    
    def _compute_reward(self, obs: Observation, state_delta: float) -> float:
        # Tool agents get more reward for env changes than internal ones
        # We override the base composite delta slightly in reward logic
        if obs.env_state_delta > 0.2:
            self.current_reward += 0.2  # Bonus for tangible env change
            
        return super()._compute_reward(obs, state_delta)

    def _compute_difficulty(self, obs: Observation, state_delta: float) -> float:
        # Tool agents spike difficulty immediately on execution errors
        difficulty = super()._compute_difficulty(obs, state_delta)
        
        if obs.result == 'error' or (obs.error is not None):
            difficulty = max(difficulty, 0.6)
            
        return difficulty
